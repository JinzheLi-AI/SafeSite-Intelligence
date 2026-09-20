"""Pure metrics. Undefined denominators return null, never perfect scores."""
from .schema import HAZARDS

def ratio(n, d):
    return n / d if d else None

def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None

def rates(tp, fp, fn, tn):
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=ratio(tp, tp+fp), recall=ratio(tp, tp+fn),
                f1=ratio(2*tp, 2*tp+fp+fn), false_positive_rate=ratio(fp, fp+tn), false_negative_rate=ratio(fn, fn+tp))

def hazards(cases, predictions):
    if any(hasattr(c, "class_decisions") or isinstance(c, dict) and "class_decisions" in c for c in cases):
        raise ValueError("Use vision-three-state-v1 scorer for three-state ground truth")
    truth = {c.case_id:c for c in cases}
    predicted = {p.case_id:p for p in predictions}
    if len(predicted) != len(predictions) or set(predicted) != set(truth):
        raise ValueError('Predictions must cover each case exactly once; no dropped failures or extra cases.')
    if any(c.ground_truth_hazards is None for c in cases):
        raise ValueError('Unlabeled placeholders are not ground truth')
    counts = {h:[0,0,0,0] for h in HAZARDS}
    exact = review = errors = 0
    ambiguous_review=[]; obvious_uncertainty=[]; ambiguous_uncertainty=[]
    for c in cases:
        p=predicted[c.case_id]; failed=bool(p.error); errors+=failed
        expected=set(c.ground_truth_hazards); actual=set(p.hazards) if not failed else set()
        exact += not failed and expected==actual
        review += not failed and p.requires_human_review==c.expected_human_review
        for h in HAZARDS:
            counts[h][0 if h in expected and h in actual else 1 if h in actual else 2 if h in expected else 3]+=1
        if c.ambiguous: ambiguous_review.append(int(not failed and p.requires_human_review))
        if p.uncertain is not None and not failed:
            (ambiguous_uncertainty if c.ambiguous else obvious_uncertainty).append(int(p.uncertain))
    per_class={h:rates(*v) for h,v in counts.items()}
    micro=rates(*(sum(v[i] for v in counts.values()) for i in range(4)))
    return dict(cases=len(cases), errors=errors, completion_rate=ratio(len(cases)-errors,len(cases)),
        precision=micro['precision'], recall=micro['recall'], f1=micro['f1'], micro_f1=micro['f1'],
        false_positive_rate=micro['false_positive_rate'], false_negative_rate=micro['false_negative_rate'],
        macro_f1=mean([v['f1'] for v in per_class.values()]), per_class=per_class, micro=micro,
        exact_match_rate=ratio(exact,len(cases)), review_agreement=ratio(review,len(cases)),
        ambiguous_review_rate=mean(ambiguous_review), ambiguous_uncertainty_rate=mean(ambiguous_uncertainty),
        obvious_uncertainty_rate=mean(obvious_uncertainty), uncertainty_scored_cases=len(obvious_uncertainty)+len(ambiguous_uncertainty))

def retrieval(cases, results):
    if len(results)!=len(cases) or {r['query_id'] for r in results}!={c.query_id for c in cases}:
        raise ValueError('Every query must have exactly one result')
    by_id={r['query_id']:r for r in results}
    recalls={1:[],3:[]}; hits={1:[],3:[]}; precision=[]; rr=[]; negatives=[]; citations=[]; errors=0
    for c in cases:
        r=by_id[c.query_id]; items=r['citations']; citations.extend(items)
        failed=bool(r.get('error')); errors+=failed
        def relevant(x):
            return (x.get('document_key') in c.expected_document_ids or x.get('family') in c.expected_source_families) and (
                not c.expected_section_keywords or any(k.casefold() in (x.get('section','')+' '+x.get('excerpt','')).casefold() for k in c.expected_section_keywords))
        if c.should_return_evidence:
            # Relevance units are explicitly judged documents/families, not duplicate chunks.
            target_count=len(set(c.expected_document_ids))+len(set(c.expected_source_families))
            for k in [1,3]:
                found=set()
                for x in items[:k] if not failed else []:
                    if relevant(x):
                        if x.get('document_key') in c.expected_document_ids: found.add(('document',x['document_key']))
                        if x.get('family') in c.expected_source_families: found.add(('family',x['family']))
                recalls[k].append(len(found)/target_count); hits[k].append(int(bool(found)))
            precision.append(sum(relevant(x) for x in items[:3])/3 if not failed else 0)
            rr.append(next((1/i for i,x in enumerate(items,1) if relevant(x)),0) if not failed else 0)
        else: negatives.append(int(not failed and not items))
    return dict(queries=len(cases), answerable_queries=len(rr), no_answer_queries=len(negatives), errors=errors,
        recall_at_1=mean(recalls[1]), recall_at_3=mean(recalls[3]), hit_at_1=mean(hits[1]), hit_at_3=mean(hits[3]),
        precision_at_3=mean(precision), mrr=mean(rr), no_answer_accuracy=mean(negatives), citations=len(citations),
        unsupported_citation_rate=ratio(sum(not x['stored_source_valid'] for x in citations),len(citations)),
        verified_source_rate=ratio(sum(x['verified'] for x in citations),len(citations)))

def workflow(rows):
    axes=['safety_guardrail','human_control','audit_completeness','state_transition']
    output={'scenarios':len(rows),'workflow_success_rate':mean([int(r['passed']) for r in rows])}
    for axis in axes:
        selected=[r for r in rows if axis in r['criteria']]
        output[axis]={'passed':sum(r['passed'] for r in selected),'total':len(selected),
                      'success_rate':mean([int(r['passed']) for r in selected])}
    return output
