"""Run from any directory with the backend virtualenv. Offline unless --live-vision is passed."""
from contextlib import closing
import argparse
import hashlib
import json
import os
import platform
from importlib.metadata import version
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'backend')]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'evaluation/reports')
    parser.add_argument('--datasets',type=Path,default=ROOT/'evaluation/datasets')
    parser.add_argument('--database',type=Path,default=ROOT/'backend/data/safesite.db')
    parser.add_argument('--image-root',type=Path,default=ROOT/'evaluation/datasets')
    parser.add_argument('--live-vision',action='store_true',help='Send reviewed images to the configured real model; may incur API charges.')
    parser.add_argument('--max-vision-cases',type=int,default=100)
    parser.add_argument('--vision-model-id',help='Explicit openai/model or deepseek/model comparison dimension; no automatic provider routing.')
    parser.add_argument('--vision-validation-attempts',type=int,choices=[1,2],default=2,help='Per-case, per-baseline call bound (SDK retries disabled).')
    args=parser.parse_args()
    if not 1<=args.max_vision_cases<=100:parser.error('--max-vision-cases must be 1-100')
    for name in ['output','datasets','database','image_root']:setattr(args,name,getattr(args,name).resolve())
    os.chdir(ROOT/'backend')
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from evaluation.schema import load,HazardCase,RagCase,PENDING
    from evaluation.runners import risk,retrieval,workflow,vision
    from evaluation.report import write
    if settings.embedding_provider!='fastembed':parser.error('Offline RAG evaluation requires configured local fastembed; no paid embeddings are run implicitly.')
    args.output.mkdir(parents=True,exist_ok=True)
    cases={k:json.loads((args.datasets/(k+'.json')).read_text(encoding='utf-8-sig')) for k in ['risk','workflow']}
    hazard_cases=load(args.datasets/'hazards.json',HazardCase);rag_cases=load(args.datasets/'retrieval.json',RagCase)
    summary={'schema_version':'evaluation-v1','generated_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
             'dependencies':{name:version(name) for name in ['pydantic','sqlalchemy','pytest','openai','fastembed']},
             'dataset_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.datasets.glob('*.json'))},
             'source_registry_sha256':hashlib.sha256((ROOT/'backend/app/knowledge/hk_core.json').read_bytes()).hexdigest(),
             'retrieval_thresholds':{'semantic':settings.retrieval_min_semantic,'score':settings.retrieval_min_score},
             'hazard':vision.run(hazard_cases,args.image_root,args.output,args.live_vision,args.max_vision_cases,args.vision_model_id,args.vision_validation_attempts),
             'risk':risk.run(cases['risk'])}
    if args.database.exists():
        # A stable SQLite backup captures a consistent corpus without writing to the product database.
        with tempfile.TemporaryDirectory(prefix='safesite-corpus-eval-') as temp:
            snapshot=Path(temp)/'corpus.sqlite'
            with closing(sqlite3.connect(args.database.as_uri()+'?mode=ro',uri=True)) as source:
                with closing(sqlite3.connect(snapshot)) as dest:source.backup(dest)
            engine=create_engine('sqlite://',creator=lambda:sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True))
            try:
                with Session(engine) as db:summary['retrieval']=retrieval.run(rag_cases,db)
            finally:engine.dispose()
    else:summary['retrieval']={'status':PENDING,'reason':'Local database missing','baselines':{}}
    summary['workflow']=workflow.run(cases['workflow'],ROOT/'backend',args.output)
    summary['product_code_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'backend/app').rglob('*.py'))}
    summary['evaluation_code_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'evaluation').rglob('*.py'))}
    summary['workflow_test_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'backend/tests').glob('*.py'))}
    write(summary,args.output)
    print('Reports:',args.output)
    print(json.dumps({k:summary[k]['status'] for k in ['hazard','retrieval','risk','workflow']}))
    failed=any(not r['passed'] for r in summary['risk']['rows']+summary['workflow']['rows'])
    failed=failed or any(r['metrics']['errors'] for r in summary['retrieval'].get('baselines',{}).values())
    failed=failed or any(r['metrics']['errors'] for r in summary['hazard'].get('baselines',{}).values())
    return 1 if failed else 0

if __name__=='__main__':raise SystemExit(main())
