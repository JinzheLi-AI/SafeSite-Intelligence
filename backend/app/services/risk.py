from app.schemas.contracts import HazardType, RiskBreakdown, RiskLevel


class RiskEngine:
    POLICY_VERSION = 'safety-policy-1.0'
    THRESHOLDS = ((80, RiskLevel.CRITICAL), (50, RiskLevel.HIGH), (25, RiskLevel.MEDIUM), (0, RiskLevel.LOW))

    @classmethod
    def level(cls, score: int) -> RiskLevel:
        if not 0 <= score <= 100:
            raise ValueError('Risk score must be 0–100')
        return next(level for threshold, level in cls.THRESHOLDS if score >= threshold)

    @classmethod
    def assess(cls, hazard_type: str, severity: int, exposure: int, probability: int, confidence: float) -> RiskBreakdown:
        HazardType(hazard_type)
        if not (1 <= severity <= 5 and 1 <= exposure <= 5 and 1 <= probability <= 4 and 0 <= confidence <= 1):
            raise ValueError('Invalid risk inputs')
        raw = severity * exposure * probability
        score = raw
        overrides = []
        if hazard_type == 'working_at_height' and severity >= 5 and exposure >= 4:
            score = max(score, 85)
            overrides.append('WAH-001: severity ≥ 5 and exposure ≥ 4 require CRITICAL (minimum score 85).')
        return RiskBreakdown(severity=severity, exposure=exposure, probability=probability,
            raw_score=raw, final_score=score, risk_level=cls.level(score), confidence=confidence,
            requires_human_review=confidence < 0.8, policy_version=cls.POLICY_VERSION,
            overrides=overrides, formula='Severity × Exposure × Probability (maximum 5 × 5 × 4 = 100). Confidence never discounts risk.')
