"""Synthetic response fixtures test contracts/selection, not real visual accuracy."""
import json
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from PIL import Image
from app.ai.real import RealMultimodalSafetyAIProvider
from app.ai.provider import get_provider
from app.ai.prompts import VISION_SYSTEM_PROMPT, REINSPECTION_SYSTEM_PROMPT
from app.ai.vision_v2 import VISION_V2_SYSTEM_PROMPT
from app.core.config import Settings, settings
from app.schemas.contracts import InspectionAnalysis
from app.main import app


def finding(label, evidence, **changes):
    return dict(hazard_type=label,title='Synthetic test observation',description=evidence,
        visual_evidence=[evidence],confidence=.95,severity=2,exposure=2,probability=1,
        recommended_actions=['Arrange appropriate site assessment.'],regulation_queries=[]) | changes


def make_provider(hazards,uncertain=False,version='vision-v2',notes=None,confidence=.95):
    sdk=Mock()
    observation=dict(summary='Synthetic fixture, not a real image prediction.',hazards=hazards,
        overall_confidence=confidence,requires_human_review=uncertain,
        ambiguity_detected=uncertain,reasoning_notes=notes or [])
    def parse(**kwargs):
        parsed=kwargs['text_format'].model_validate(observation)
        return SimpleNamespace(status='completed',output=[],output_parsed=parsed,usage=None)
    sdk.responses.parse.side_effect=parse
    config=Settings(_env_file=None,vision_model='gpt-5.6-sol',vision_prompt_version=version)
    return RealMultimodalSafetyAIProvider(config,sdk)


@pytest.fixture
def image(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'upload_dir',tmp_path)
    Image.new('RGB',(20,20)).save(tmp_path/'fixture.jpg')
    return '/uploads/fixture.jpg'


@pytest.mark.parametrize('scenario,hazards,uncertain,expected',[
 ('ppe_hidden',[],True,[]),
 ('ppe_visibly_absent_and_required',[finding('missing_ppe','Visible bare head beneath an observable overhead impact exposure.')],False,['missing_ppe']),
 ('ppe_requirement_unknown',[],True,[]),
 ('safe_scene',[],False,[]),
 ('guarded_elevated_activity',[finding('working_at_height','Worker on elevated platform with continuous guardrails; no uncontrolled fall condition established.')],False,['working_at_height']),
 ('scaffold_no_visible_defect',[],False,[]),
 ('electrical_equipment_no_visible_danger',[],False,[]),
 ('clear_housekeeping',[finding('housekeeping','Loose cable crosses the visible walking route.')],False,['housekeeping']),
 ('ambiguous_image',[],True,[]),
])
def test_synthetic_scenarios_keep_uncertainty_separate(image,scenario,hazards,uncertain,expected):
    p=make_provider(hazards,uncertain)
    result=p.analyze_inspection(location='',description=None,image_path=image)
    assert [h.hazard_type for h in result.hazards]==expected
    assert result.model_uncertainty_review==uncertain
    assert result.operational_human_confirmation==bool(hazards)
    assert result.requires_human_review==(uncertain or bool(hazards))
    assert p._injected_client.responses.parse.call_args.kwargs['input'][0]['content'].startswith(VISION_V2_SYSTEM_PROMPT)
    assert p.call_records[0]['prompt_version']=='vision-v2'
    assert InspectionAnalysis.model_validate(result.model_dump())==result


def test_v1_default_and_keyword_behavior_preserved(image):
    assert Settings(_env_file=None).vision_prompt_version=='vision-v1'
    notes=['No unclear condition is identified.']
    v1=make_provider([],version='vision-v1',notes=notes)
    a=v1.analyze_inspection(location='',description=None,image_path=image)
    b=make_provider([],notes=notes).analyze_inspection(location='',description=None,image_path=image)
    assert a.requires_human_review and a.model_uncertainty_review is None
    assert not b.requires_human_review
    assert v1._injected_client.responses.parse.call_args.kwargs['input'][0]['content'].startswith(VISION_SYSTEM_PROMPT)
    assert v1.reinspection_prompt_version=='reinspection-vision-v1'


@pytest.mark.parametrize('hazards,confidence',[([],.84),([finding('housekeeping','Cable crosses route.',confidence=.84)],.95),([finding('housekeeping','Cable crosses route.',visual_evidence=[])],.95)])
def test_numeric_and_empty_evidence_guards_remain(image,hazards,confidence):
    result=make_provider(hazards,confidence=confidence).analyze_inspection(location='',description=None,image_path=image)
    assert result.model_uncertainty_review and result.requires_human_review


def test_contract_cannot_bypass_operational_confirmation(image):
    result=make_provider([finding('housekeeping','Obstruction across route.')]).analyze_inspection(location='',description=None,image_path=image)
    data=result.model_dump();data.update(operational_human_confirmation=False,requires_human_review=False)
    restored=InspectionAnalysis.model_validate(data)
    assert restored.operational_human_confirmation and restored.requires_human_review
    assert not restored.model_uncertainty_review
    data['model_uncertainty_review']=None
    with pytest.raises(ValidationError):InspectionAnalysis.model_validate(data)


def test_v2_workflow_still_requires_explicit_human_confirmation(client,image):
    p=make_provider([finding('housekeeping','Clear obstruction across the walking route.')])
    app.dependency_overrides[get_provider]=lambda:p
    created=client.post('/api/v1/inspections',json=dict(project_id=1,site_id=1,location_text='Synthetic site',source_type='IMAGE',image_path=image))
    assert created.status_code==201
    path='/api/v1/inspections/'+str(created.json()['id'])
    response=client.post(path+'/analyze');assert response.status_code==200,response.text
    value=response.json()
    assert value['incident_ids']==[]
    assert value['analysis_json']['operational_human_confirmation']
    assert not value['analysis_json']['model_uncertainty_review']
    assert value['analysis_json']['requires_human_review']
    assert value['analysis_source']['prompt_version']=='vision-v2'
    confirmed=client.post(path+'/confirm',json={})
    assert confirmed.status_code==201 and len(confirmed.json())==1
