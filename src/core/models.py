"""Domain models for Hybrid Anti-Money Laundering (AML) architecture."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PaymentChannel(str, Enum):
    SWIFT_WIRE = "SWIFT_WIRE"
    DOMESTIC_ACH = "DOMESTIC_ACH"
    INSTANT_ACH = "INSTANT_ACH"
    CARD_CNP = "CARD_CNP"
    CARD_CP = "CARD_CP"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    P2P_TRANSFER = "P2P_TRANSFER"
    CROSS_BORDER_WIRE = "CROSS_BORDER_WIRE"
    CRYPTO_FIAT_ONRAMP = "CRYPTO_FIAT_ONRAMP"
    COMMERCIAL_LC = "COMMERCIAL_LC"
    CORPORATE_PAYROLL = "CORPORATE_PAYROLL"


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    INTERMEDIATE = "INTERMEDIATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionStatus(str, Enum):
    PASSED = "PASSED"
    HOLD = "HOLD"
    TRIAGING = "TRIAGING"
    AUTO_CLEARED = "AUTO_CLEARED"
    ESCALATED_HUMAN = "ESCALATED_HUMAN"
    SAR_APPROVED = "SAR_APPROVED"
    SAR_OVERRIDDEN = "SAR_OVERRIDDEN"
    REJECTED = "REJECTED"


class TypologyType(str, Enum):
    SMURFING_STRUCTURING = "SMURFING_STRUCTURING"
    RAPID_VELOCITY_PEELING_CHAIN = "RAPID_VELOCITY_PEELING_CHAIN"
    SLEEPER_MULE_ACTIVATION = "SLEEPER_MULE_ACTIVATION"
    SYNTHETIC_IDENTITY_RING = "SYNTHETIC_IDENTITY_RING"
    FRACTIONAL_UBO_CONCEALMENT = "FRACTIONAL_UBO_CONCEALMENT"
    CRYPTO_TO_FIAT_MIXER_BRIDGE = "CRYPTO_TO_FIAT_MIXER_BRIDGE"
    TRADE_BASED_MONEY_LAUNDERING = "TRADE_BASED_MONEY_LAUNDERING"
    ADVERSARIAL_ML_PERTURBATION = "ADVERSARIAL_ML_PERTURBATION"
    SANCTIONS_HARD_STOP = "SANCTIONS_HARD_STOP"
    BENIGN_NORMAL = "BENIGN_NORMAL"


class TelemetryData(BaseModel):
    """Digital footprint and session telemetry."""
    device_id: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    geo_hash: Optional[str] = None
    phone_hash: Optional[str] = None
    browser_fingerprint: Optional[str] = None
    failed_auth_count: int = 0
    session_duration_sec: float = 0.0


class PartyProfile(BaseModel):
    """Customer or legal entity profile."""
    customer_id: str
    account_id: str
    name: str
    ssn: Optional[str] = None  # PII scrubbed in transit
    country: str = "US"
    city: Optional[str] = None
    account_tenure_months: int = 12
    historical_monthly_avg_vol: float = 1000.0
    risk_rating: RiskTier = RiskTier.LOW
    is_pep: bool = False
    is_sanctioned: bool = False


class Transaction(BaseModel):
    """Canonical financial transaction conforming to ISO 20022 AML schema."""
    transaction_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    amount: float
    currency: str = "USD"
    channel: PaymentChannel
    payment_rail: str = "ISO20022_PACS008"
    sender: PartyProfile
    receiver: PartyProfile
    telemetry: TelemetryData = Field(default_factory=TelemetryData)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_tokenized: bool = False


class RuleHit(BaseModel):
    """Deterministic rule match detail."""
    rule_id: str
    rule_name: str
    is_hard_stop: bool
    confidence: float
    description: str
    trigger_value: Any = None


class Tier1Result(BaseModel):
    """Outcome of Tier 1 Deterministic Rules Engine."""
    transaction_id: str
    is_blocked: bool
    status: DecisionStatus
    latency_ms: float
    rule_hits: List[RuleHit] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RiskScoreResult(BaseModel):
    """Outcome of Tier 2 Machine Learning & Graph Inference Engine."""
    transaction_id: str
    s_supervised: float = Field(..., ge=0.0, le=1.0)
    s_unsupervised: float = Field(..., ge=0.0, le=1.0)
    s_graph: float = Field(..., ge=0.0, le=1.0)
    s_final: float = Field(..., ge=0.0, le=1.0)
    risk_tier: RiskTier
    recommended_action: DecisionStatus
    inferred_typology: TypologyType
    shap_contributions: Dict[str, float] = Field(default_factory=dict)
    counterfactual_explanation: Optional[str] = None
    latency_ms: float = 0.0


class Alert(BaseModel):
    """Triage alert dispatched from Tier 2 to Tier 3 or human investigator."""
    alert_id: str
    transaction: Transaction
    tier1_result: Tier1Result
    ml_scoring: RiskScoreResult
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: DecisionStatus = DecisionStatus.TRIAGING


class ClaimEvidencePair(BaseModel):
    """Claim-to-evidence pairing for Compliance Critic grounding check."""
    claim: str
    evidence_source: str
    evidence_text: str
    entailment_score: float = Field(..., ge=0.0, le=1.0)
    is_grounded: bool


class SuspiciousActivityReport(BaseModel):
    """Regulatory Suspicious Activity Report (FinCEN/FIU compliant)."""
    sar_id: str
    alert_id: str
    filing_institution: str = "SENTINEL HYBRID FINANCIAL CORP"
    suspect_name: str
    suspect_tax_id: Optional[str] = None
    suspect_address: Optional[str] = None
    suspicious_activity_codes: List[str] = Field(default_factory=list)
    total_amount_flagged: float
    narrative: str
    timeline_events: List[Dict[str, Any]] = Field(default_factory=list)
    involved_accounts: List[str] = Field(default_factory=list)
    counterparties: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    critic_groundedness_score: float = 1.0
    critic_feedback: Optional[str] = None
    human_approved: bool = False
    human_notes: Optional[str] = None


class Case(BaseModel):
    """Human-in-the-Loop Case Management container."""
    case_id: str
    alert: Alert
    dossier: Dict[str, Any] = Field(default_factory=dict)
    draft_sar: Optional[SuspiciousActivityReport] = None
    status: DecisionStatus = DecisionStatus.TRIAGING
    assigned_analyst: Optional[str] = None
    adjudication_timestamp: Optional[datetime] = None
    override_reason_code: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditBlock(BaseModel):
    """Cryptographic WORM Audit Block in continuous SHA-256 chain."""
    block_index: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    event_payload_hash: str
    previous_hash: str
    current_hash: str
    actor: str = "SYSTEM"
