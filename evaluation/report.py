import json
from pathlib import Path
from evaluation.schema import PENDING

def ablations(summary):
    # Component results, never invented joint end-to-end results for unimplemented systems.
    configs=[
        {'system':'A - Generic vision','components':['generic_direct'],'vision':summary['hazard'].get('baselines',{}).get('generic_direct'),
         'joint_status':PENDING,'joint_score':None},
        {'system':'B - Vision + basic RAG','components':['generic_direct','semantic_only'],
         'rag':summary['retrieval'].get('baselines',{}).get('semantic_only',{}).get('metrics'),'joint_status':PENDING,'joint_score':None},
        {'system':'C - Vision + verified RAG + RiskEngine','components':['safesite_vision','semantic_metadata','RiskEngine'],
         'rag':summary['retrieval'].get('baselines',{}).get('semantic_metadata',{}).get('metrics'),'risk':summary['risk']['metrics'],
         'joint_status':PENDING,'joint_score':None},
        {'system':'D - Full SafeSite','components':['safesite_vision','safesite_retrieval','RiskEngine','human_review','workflow_controls'],
         'rag':summary['retrieval'].get('baselines',{}).get('safesite',{}).get('metrics'),'risk':summary['risk']['metrics'],
         'workflow':summary['workflow']['metrics'],'joint_status':PENDING,'joint_score':None}]

    for row in configs:
        row['component_statuses']={'vision':summary['hazard']['status']}
        if 'rag' in row:row['component_statuses']['rag']=summary['retrieval']['status']
        if 'risk' in row:row['component_statuses']['risk']=summary['risk']['status']
        if 'workflow' in row:row['component_statuses']['workflow']=summary['workflow']['status']
    return configs

def number(value): return 'N/A (undefined)' if value is None else f'{value:.4f}'

def markdown(summary):
    lines=['# SafeSite Evaluation','', 'No live vision accuracy or integrated ablation superiority is claimed. Ratios are 0-1.', '',
           '## Hazard Recognition','',summary['hazard']['status'],'',
           '| Baseline | Precision | Recall | Micro F1 | Macro F1 |','| --- | ---: | ---: | ---: | ---: |']
    for name,r in summary['hazard'].get('baselines',{}).items():
        m=r['metrics'];lines.append('| '+name+' | '+' | '.join(number(m[k]) for k in ['precision','recall','micro_f1','macro_f1'])+' |')
    if not summary['hazard'].get('baselines'):lines.append('| Generic direct / SafeSite | Pending live evaluation | Pending | Pending | Pending |')
    lines+=['','## Regulation Retrieval','',summary['retrieval']['status'], '',
            'Draft source-family relevance judgments on the existing pilot corpus; not a held-out expert benchmark.','',
            '| Baseline | Recall@1 | Recall@3 | Precision@3 | MRR | No-answer accuracy | Unsupported citations | Verified sources |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name,r in summary['retrieval'].get('baselines',{}).items():
        m=r['metrics'];lines.append('| '+name+' | '+' | '.join(number(m[k]) for k in ['recall_at_1','recall_at_3','precision_at_3','mrr','no_answer_accuracy','unsupported_citation_rate','verified_source_rate'])+' |')
    lines+=['','## Risk Evaluation','',summary['risk']['status']+' - deterministic specification conformance.', '', '| Metric | Value |','| --- | ---: |']
    lines+=['| '+k+' | '+number(v)+' |' for k,v in summary['risk']['metrics'].items()]
    lines+=['','## Workflow Evaluation','',summary['workflow']['status']+' - isolated database, injected AI.', '', '| Metric | Value | Eligible scenarios |','| --- | ---: | ---: |']
    for k,v in summary['workflow']['metrics'].items():
        if k=='scenarios':continue
        lines.append('| '+k+' | '+number(v['success_rate'] if isinstance(v,dict) else v)+' | '+str(v['total'] if isinstance(v,dict) else summary['workflow']['metrics']['scenarios'])+' |')
    lines+=['','## Ablations','', 'Component comparisons are measured separately. All A-D integrated scores remain pending; no workflow-control result is attributed to a generic LLM.', '',
            'See summary.json and individual result files for case-level outcomes, errors, hashes and denominators.']
    return '\n'.join(lines)+'\n'

def write(summary,output):
    output=Path(output);output.mkdir(exist_ok=True,parents=True)
    summary['ablations']=ablations(summary)
    (output/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (output/'summary.md').write_text(markdown(summary),encoding='utf-8')
    for part in ['hazard','retrieval','risk','workflow','ablations']:
        (output/(part+'.json')).write_text(json.dumps(summary[part],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
