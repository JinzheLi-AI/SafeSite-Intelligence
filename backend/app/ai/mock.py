from app.schemas.contracts import HazardAnalysis, InspectionAnalysis, ReinspectionAnalysis, ReinspectionContext
from app.services.risk import RiskEngine
from app.core.localization import tr, localize_inspection


class MockSafetyAIProvider:
    model_provider = 'mock'
    model_name = 'safesite-scenario-v1'
    prompt_version = 'inspection-prompt-1.0'

    def analyze_inspection(self, *, location: str, description: str | None, image_path: str | None) -> InspectionAnalysis:
        scenarios = [
            ('working_at_height', 'Working at Height',
             'Worker operating close to exposed edge without visible fall-arrest protection.',
             ['Worker positioned near exposed edge', 'No visible fall-arrest attachment', 'Elevated work area'],
             0.94, 5, 4, 4,
             ['Suspend exposed-edge work and isolate the area.', 'Arrange competent-person verification of fall protection before work resumes.']),
            ('unprotected_edge', 'Unprotected Edge',
             'Temporary edge protection appears incomplete.',
             ['Gap in temporary perimeter barrier', 'Accessible route adjacent to open edge'],
             0.91, 5, 3, 4,
             ['Restrict access to the affected edge.', 'Restore edge protection and record a competent-person inspection.']),
        ]
        hazards = []
        for kind, title, detail, evidence, confidence, severity, exposure, probability, actions in scenarios:
            risk = RiskEngine.assess(kind, severity, exposure, probability, confidence)
            hazards.append(HazardAnalysis(hazard_type=kind, title=title, description=detail,
                visual_evidence=evidence, confidence=confidence, severity=severity, exposure=exposure,
                probability=probability, risk_score=risk.final_score, risk_level=risk.risk_level,
                recommended_actions=actions, regulation_queries=[f'{kind} fall prevention guidance']))
        language = getattr(self, 'output_language', 'en')
        result = InspectionAnalysis(summary=tr('Two demonstration hazards identified at {location}.',language,location=location),
            hazards=hazards, overall_confidence=0.92, requires_human_review=True,
            reasoning_notes=['MOCK: fixed scenario; no image understanding has been performed.',
                             'Recommendations require review by a qualified human. They are not legally binding decisions.'])

        return localize_inspection(result, language)

    def analyze_reinspection(self, *, incident_id: int, previous_risk: int, evidence_path: str | None, notes: str, original_hazard: ReinspectionContext | None = None) -> ReinspectionAnalysis:
        result = ReinspectionAnalysis(original_incident_id=incident_id, hazard_still_present=False,
            mitigation_confidence=0.93, evidence=['MOCK: simulated restored edge protection.', 'MOCK: simulated fall-protection verification.'],
            previous_risk_score=previous_risk, current_risk_score=15, recommendation='ELIGIBLE_FOR_CLOSURE')

        result.evidence = [tr(x, getattr(self, 'output_language', 'en')) for x in result.evidence]
        return result
