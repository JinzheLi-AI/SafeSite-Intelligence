"""Presentation-only translations; machine fields and original source text are never rewritten."""
import json
import re
from functools import lru_cache
from pathlib import Path

@lru_cache
def dictionary(language):
    path=Path(__file__).resolve().parents[3]/'shared'/'locales'/(language+'.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def tr(text,language='en',**values):
    data=dictionary(language)
    translated=data.get(text,text)
    if translated==text and language!='en':
        for template,target in sorted(data.items(), key=lambda item: -len(item[0])):
            names=re.findall(r'\{(\w+)\}',template)
            if not names: continue
            pattern=re.escape(template)
            for name in names: pattern=pattern.replace(re.escape('{'+name+'}'),'(.+?)',1)
            match=re.fullmatch(pattern,text)
            if match:
                arguments={name:data.get(value,value) for name,value in zip(names,match.groups())}
                translated=target.format(**arguments)
                break
    return translated.format(**values) if values else translated

def localize_inspection(result,language):
    if language=='en': return result
    result.reasoning_notes=[tr(x,language) for x in result.reasoning_notes]
    for hazard in result.hazards:
        hazard.title=tr(hazard.title,language)
        hazard.description=tr(hazard.description,language)
        hazard.visual_evidence=[tr(x,language) for x in hazard.visual_evidence]
        hazard.recommended_actions=[tr(x,language) for x in hazard.recommended_actions]
    return result
