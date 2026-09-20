from app.services.risk import RiskEngine
from evaluation.schema import VERIFIED
from evaluation.metrics import mean

def run(cases):
    rows=[]
    for c in cases:
        if c['kind']=='boundary':
            actual={'level':str(RiskEngine.level(c['score']))}
            checks={'classification':actual['level']==c['expected_level'],'boundary':actual['level']==c['expected_level']}
        else:
            r=RiskEngine.assess(c['hazard_type'],c['severity'],c['exposure'],c['probability'],c['confidence'])
            actual=r.model_dump(mode='json')
            checks={'classification':r.risk_level==c['expected_level'],'score':r.final_score==c['expected_score'],
                    'override':bool(r.overrides)==c['expected_override'],'human_review':r.requires_human_review==c['expected_review']}
        rows.append({'case_id':c['case_id'],'passed':all(checks.values()),'checks':checks,'actual':actual})
    return {'status':VERIFIED,'basis':'Deterministic policy specification conformance; not field safety accuracy.',
            'policy_version':RiskEngine.POLICY_VERSION,'cases':len(rows),'metrics':{
                k+'_accuracy':mean([int(r['checks'][k]) for r in rows if k in r['checks']])
                for k in ['classification','boundary','override','human_review','score']},'rows':rows}
