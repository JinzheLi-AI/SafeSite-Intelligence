"""Versioned, offline-only three-state vision scoring. No provider imports."""
import argparse
import hashlib
import json
from pathlib import Path
from .schema import HAZARDS
from .metrics import ratio, mean, rates

VERSION = 'vision-three-state-v1'
MANIFEST_SCHEMA = 'vision-v2-split-manifest-v1'

def validate_manifest(doc):
    if not isinstance(doc, dict) or doc.get('schema_version') != MANIFEST_SCHEMA:
        raise ValueError('Explicit V2 split manifest required')
    rows = doc['cases']
    if len({r['case_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate case IDs')
    for r in rows:
        decisions = r.get('class_decisions', {})
        if set(decisions) != set(HAZARDS) or any(v not in ('positive','negative','indeterminate') for v in decisions.values()):
            raise ValueError('Six explicit class decisions required')
        if set(r['ground_truth_hazards']) != {h for h,v in decisions.items() if v == 'positive'}:
            raise ValueError('Positive labels disagree with class decisions')
        if type(r.get('expected_uncertainty_review')) is not bool:
            raise ValueError('Explicit expected_uncertainty_review required')
    return rows

def eligibility(doc):
    rows = validate_manifest(doc)
    return dict(scoring_schema_version=VERSION, cases=len(rows),
        per_class={h:dict(evaluable_count=sum(r['class_decisions'][h]!='indeterminate' for r in rows),
                         indeterminate_count=sum(r['class_decisions'][h]=='indeterminate' for r in rows),
                         positive_support=sum(r['class_decisions'][h]=='positive' for r in rows)) for h in HAZARDS},
        confirmed_safe_case_ids=[r['case_id'] for r in rows if all(v=='negative' for v in r['class_decisions'].values())],
        unknown_status_case_ids=[r['case_id'] for r in rows if 'indeterminate' in r['class_decisions'].values()],
        full_exact_match_case_ids=[r['case_id'] for r in rows if 'indeterminate' not in r['class_decisions'].values()])

def score(doc, predictions):
    rows=validate_manifest(doc); plan=eligibility(doc)
    by_id={p['case_id']:p for p in predictions}
    if len(by_id)!=len(predictions) or set(by_id)!={r['case_id'] for r in rows}:
        raise ValueError('One cached prediction or explicit failure per case required')
    for p in predictions:
        if type(p.get('provider_success')) is not bool:raise ValueError('Explicit provider_success required')
        if p['provider_success'] and (not isinstance(p.get('predicted_hazards'),list) or any(h not in HAZARDS for h in p['predicted_hazards'])):
            raise ValueError('Supported predicted_hazards required')
        if p.get('model_uncertainty_review') is not None and type(p['model_uncertainty_review']) is not bool:
            raise ValueError('Uncertainty review must be boolean or unavailable')
    good=[r for r in rows if by_id[r['case_id']]['provider_success']]
    counts={h:[0,0,0,0] for h in HAZARDS}; errors=[]
    exact=[];known=[];safe=[];reviews=[]
    for r in good:
        p=by_id[r['case_id']];actual=set(p['predicted_hazards']);d=r['class_decisions']
        eligible={h for h in HAZARDS if d[h]!='indeterminate'}
        expected={h for h in eligible if d[h]=='positive'}
        fp=sorted((actual & eligible)-expected);fn=sorted(expected-actual)
        errors.append(dict(case_id=r['case_id'],false_positive_classes=fp,false_negative_classes=fn,
                           excluded_indeterminate_classes=sorted(set(HAZARDS)-eligible)))
        for h in eligible:
            counts[h][0 if h in expected and h in actual else 1 if h in actual else 2 if h in expected else 3]+=1
        if len(eligible)==6:exact.append(not fp and not fn)
        elif eligible:known.append(not fp and not fn)
        if all(v=='negative' for v in d.values()):safe.append(not actual)
        flag=p.get('model_uncertainty_review')
        if flag is not None:reviews.append((r['expected_uncertainty_review'],flag))
    per={}
    for h,c in counts.items():
        per[h]=dict(**rates(*c),positive_support=c[0]+c[2],evaluable_sample_count=sum(c),
                    indeterminate_count=sum(r['class_decisions'][h]=='indeterminate' for r in good),
                    dataset_evaluable_count=plan['per_class'][h]['evaluable_count'],
                    dataset_indeterminate_count=plan['per_class'][h]['indeterminate_count'])
    expected=sum(e for e,f in reviews);unneeded=sum(not e for e,f in reviews)
    return dict(scoring_schema_version=VERSION,dataset_cases=len(rows),successful_cases=len(good),
        failed_cases=len(rows)-len(good),coverage=ratio(len(good),len(rows)),eligibility=plan,
        micro=rates(*(sum(c[i] for c in counts.values()) for i in range(4))),per_class=per,
        macro={k:mean([v[k] for v in per.values()]) for k in ['precision','recall','f1']},
        macro_defined_class_counts={k:sum(v[k] is not None for v in per.values()) for k in ['precision','recall','f1']},
        macro_policy='Unweighted mean of defined class values separately per metric; null denominators excluded. Zero-support F1 is 0 if FP>0, otherwise null; zero-support recall null. Not evidence of positive recognition.',
        full_exact_match=dict(evaluable_count=len(exact),correct_count=sum(exact),accuracy=ratio(sum(exact),len(exact))),
        partial_known_label_agreement=dict(evaluable_case_count=len(known),correct_count=sum(known),rate=ratio(sum(known),len(known))),
        safe_scene=dict(confirmed_count=len(safe),correctly_predicted_count=sum(safe),false_positive_count=len(safe)-sum(safe),false_positive_rate=ratio(len(safe)-sum(safe),len(safe)),unknown_status_scene_count=sum('indeterminate' in r['class_decisions'].values() for r in good)),
        uncertainty_review=dict(status='available' if len(reviews)==len(good) and good else 'partial' if reviews else 'unavailable',
            expected_dataset_count=sum(r['expected_uncertainty_review'] for r in rows),evaluable_count=len(reviews),unavailable_successful_count=len(good)-len(reviews),
            expected_evaluable_count=expected,correct_flags=sum(e and f for e,f in reviews),missed_flags=sum(e and not f for e,f in reviews),
            recall=ratio(sum(e and f for e,f in reviews),expected),unnecessary_count=sum(not e and f for e,f in reviews),
            unnecessary_denominator=unneeded,unnecessary_rate=ratio(sum(not e and f for e,f in reviews),unneeded)),
        case_errors=errors)

def main():
    parser=argparse.ArgumentParser(description='Offline V2 eligibility or cached prediction scoring; never inference')
    parser.add_argument('manifest',type=Path);parser.add_argument('--cache',type=Path)
    args=parser.parse_args();raw=args.manifest.read_bytes();doc=json.loads(raw)
    if args.cache:
        cache=json.loads(args.cache.read_text(encoding='utf-8'))
        if cache.get('scoring_schema_version')!=VERSION or cache.get('manifest_sha256')!=hashlib.sha256(raw).hexdigest():
            raise ValueError('Cache schema/manifest fingerprint mismatch')
        if cache.get('manifest_snapshot')!=doc:raise ValueError('Cache must preserve complete three-state manifest')
        result=score(doc,cache['predictions'])
    else:result=eligibility(doc)
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
