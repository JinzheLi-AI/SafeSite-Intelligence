import copy
import importlib.util
import sys
from pathlib import Path
import pytest
from evaluation.schema import RagCase
from evaluation.runners.retrieval import run,stored_valid

BACKEND=Path(__file__).resolve().parents[2]/'backend'
sys.path.insert(0,str(BACKEND/'tests'))
spec=importlib.util.spec_from_file_location('evaluation_product_fixtures',BACKEND/'tests/conftest.py')
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
db_factory=fixtures.db_factory
forbid_paid_http=fixtures.forbid_paid_http
from test_knowledge import indexed,TEXT

def test_baseline_isolation_and_unsupported_filter(indexed,db_factory):
    cases=[RagCase(query_id='hk',hazard_type='working_at_height',query=TEXT['working_at_height'],should_return_evidence=True,expected_source_families=['height']),
           RagCase(query_id='cn',hazard_type='working_at_height',query=TEXT['working_at_height'],should_return_evidence=False,jurisdiction='CN')]
    with db_factory() as db:
        result=run(cases,db,indexed)
        a=result['baselines']['semantic_only'];b=result['baselines']['semantic_metadata'];full=result['baselines']['safesite']
        assert len(a['rows'][1]['citations'])==3
        assert not b['rows'][1]['citations'] and not full['rows'][1]['citations']
        assert b['rows'][0]['citations']
        assert full['rows'][0]['citations'] and full['metrics']['unsupported_citation_rate']==0
        original=copy.deepcopy(full)
        a['rows'][0]['citations'][0]['excerpt']='mutated baseline'
        assert full==original
        assert not stored_valid(a['rows'][0]['citations'][0],db)

def test_rag_errors_are_not_scored_as_correct_abstention(indexed,db_factory):
    class Broken:
        signature=indexed.signature
        def encode(self,*args,**kwargs):raise RuntimeError('offline failure')
    q=RagCase(query_id='bad',hazard_type='working_at_height',query='nonsense',should_return_evidence=False)
    with db_factory() as db:
        result=run([q],db,Broken())
        assert all(r['metrics']['errors']==1 and r['metrics']['no_answer_accuracy']==0 for r in result['baselines'].values()), result
