"""AST validation plus an independent SQLite read-only/authorizer boundary."""
import json
import math
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
import sqlglot
from sqlglot import exp
from app.analyst.contracts import AnalystError
from app.analyst.schema import VIEWS, COLUMNS, BASE_COLUMNS

MAX_ROWS = 100
MAX_BYTES = 200_000
ALLOWED_NODES = set('Select Alias And Or Avg Case Column Count Date Div EQ From GT GTE Group Having Identifier If In Is LT LTE Limit Literal Mul NEQ Not Null Nullif Order Ordered Paren Star Sub Sum Table Where Add Max Min Round Coalesce Neg Distinct TableAlias'.split())
FUNCTIONS = {'count','sum','avg','min','max','round','coalesce','nullif','date','julianday'}

def validate_sql(sql: str) -> str:
    if not sql.strip() or len(sql)>12000 or any(x in sql for x in ('--','/*','*/','\x00')):
        raise AnalystError('rejected','SQL must be a bounded single SELECT without comments.')
    try:
        statements = sqlglot.parse(sql,read='sqlite')
    except Exception:
        raise AnalystError('rejected','SQL could not be parsed safely.') from None
    if len(statements)!=1 or type(statements[0]) is not exp.Select:
        raise AnalystError('rejected','Only one analytical SELECT statement is allowed.')
    tree = statements[0]
    nodes = list(tree.walk())
    if len(nodes)>300 or any(type(n).__name__ not in ALLOWED_NODES or n.comments for n in nodes):
        raise AnalystError('rejected','SQL contains an unsupported operation, function or query structure.')
    tables=list(tree.find_all(exp.Table))
    if len(tables)!=1 or tables[0].name not in VIEWS or tables[0].db or tables[0].catalog:
        raise AnalystError('rejected','Only a single approved safety analytics view may be queried.')
    table=tables[0]
    if len(tree.expressions)>16:
        raise AnalystError('rejected','Too many result columns.')
    names=[e.alias_or_name for e in tree.expressions]
    if any(not n for n in names) or len(names)!=len(set(names)):
        raise AnalystError('rejected','Result columns require unique explicit names or aliases.')
    for star in tree.find_all(exp.Star):
        if not isinstance(star.parent,exp.Count):
            raise AnalystError('rejected','Unrestricted SELECT * is not allowed.')
    for col in tree.find_all(exp.Column):
        if col.name not in COLUMNS[table.name] | set(names) or col.db or col.catalog or (
                col.table and col.table not in {table.name,table.alias}):
            raise AnalystError('rejected','SQL references an unapproved column.')
        # A bare projection name is not permission to read a hidden column.
        if col.name not in COLUMNS[table.name] and not (any(e.alias==col.name for e in tree.expressions) and col.find_ancestor(exp.Order) is not None):
            raise AnalystError('rejected','SQL references an unapproved column.')
    if any(len(str(l.this))>1000 for l in tree.find_all(exp.Literal)):
        raise AnalystError('rejected','SQL literal exceeds the allowed size.')
    limit=tree.args.get('limit')
    if limit:
        value=limit.expression
        if not isinstance(value,exp.Literal) or not value.is_int or int(value.this)<1:
            raise AnalystError('rejected','LIMIT must be a positive integer.')
        amount=min(MAX_ROWS,int(value.this))
    else:
        amount=MAX_ROWS
    return tree.limit(amount).sql(dialect='sqlite')

def authorize(action, first, second, database, source):
    if action==sqlite3.SQLITE_SELECT: return sqlite3.SQLITE_OK
    if action==sqlite3.SQLITE_FUNCTION:
        return sqlite3.SQLITE_OK if (second or '').lower() in FUNCTIONS else sqlite3.SQLITE_DENY
    if action==sqlite3.SQLITE_READ:
        # SQLite join/count optimization can emit a columnless read without view attribution.
        if first in BASE_COLUMNS and not second and database is None:
            return sqlite3.SQLITE_OK
        if first in COLUMNS and database=='temp' and (second in COLUMNS[first] or not second):
            return sqlite3.SQLITE_OK
        if source in VIEWS and database=='main' and first in BASE_COLUMNS and (
                second in BASE_COLUMNS[first] or not second):
            return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY

@contextmanager
def readonly_database(engine):
    url=engine.url
    if url.get_backend_name()!='sqlite' or not url.database or url.database==':memory:':
        raise AnalystError('unavailable','Analytics requires the configured file-backed SQLite database.')
    connection=None
    try:
        uri=Path(url.database).resolve().as_uri()+'?mode=ro'
        connection=sqlite3.connect(uri,uri=True,timeout=2)
        connection.enable_load_extension(False)
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,MAX_BYTES)
        connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH,20000)
        connection.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH,50)
        for name,definition in VIEWS.items():
            connection.execute('CREATE TEMP VIEW '+name+' AS '+definition)
        connection.execute('PRAGMA query_only=ON')
        # The candidate and reference query use one consistent read snapshot.
        connection.execute('BEGIN')
        connection.set_authorizer(authorize)
        yield connection
    except AnalystError:
        raise
    except sqlite3.Error:
        raise AnalystError('error','The read-only safety query failed or exceeded its resource limits. No operational data was changed.') from None
    finally:
        if connection: connection.close()

def execute(connection, sql: str, *, timeout_seconds=2.0, step_limit=1_000_000):
    safe=validate_sql(sql)  # Never rely on validation by a caller.
    tree=sqlglot.parse_one(safe,read='sqlite')
    requested=int(tree.args['limit'].expression.this)
    # One look-ahead row marks truncated output rather than implying completeness.
    actual=tree.limit(MAX_ROWS+1).sql(dialect='sqlite') if requested==MAX_ROWS else safe
    deadline=time.monotonic()+timeout_seconds
    steps=0
    def progress():
        nonlocal steps
        steps+=100
        return int(time.monotonic()>deadline or steps>step_limit)
    connection.set_progress_handler(progress,100)
    try:
        cursor=connection.execute(actual)
        columns=[d[0] for d in cursor.description]
        if len(columns)>16 or len(set(columns))!=len(columns):
            raise AnalystError('rejected','Invalid query result columns.')
        fetched=cursor.fetchmany(MAX_ROWS+1)
        rows=[dict(zip(columns,row)) for row in fetched[:MAX_ROWS]]
        for row in rows:
            if any(not isinstance(v,(str,int,float,type(None))) or
                   (isinstance(v,float) and not math.isfinite(v)) for v in row.values()):
                raise AnalystError('error','Query returned unsupported values.')
        if len(json.dumps(rows,ensure_ascii=False).encode('utf-8'))>MAX_BYTES:
            raise AnalystError('error','Query result exceeds the 200 KB safety limit. Narrow the question.')
        return rows,len(fetched)>MAX_ROWS
    except sqlite3.Error:
        raise AnalystError('error','The read-only safety query failed or exceeded its resource limits. No operational data was changed.') from None
    finally:
        connection.set_progress_handler(None,0)
