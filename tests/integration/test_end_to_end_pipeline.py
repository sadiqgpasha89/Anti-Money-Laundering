"""Integration tests for end-to-end AML lifecycle."""

import pytest
from src.core.models import DecisionStatus, PaymentChannel
from src.data_engineering.ingestion import transaction_ingestor
from src.data_engineering.pipeline import data_pipeline
from src.datascience.tier1_rules.engine import tier1_engine
from src.datascience.tier2_ml.model_blender import model_blender
from src.datascience.tier2_ml.triage_gate import triage_gate
from src.agents.swarm_orchestrator import swarm_orchestrator
from src.hitl.case_manager import case_manager
from src.hitl.adjudication import adjudication_service
from src.hitl.sar_gateway import sar_gateway
from src.core.crypto_audit import audit_ledger


def test_full_aml_lifecycle(sample_transaction):
    """
    Test complete lifecycle from Ingestion -> Data Engineering -> Tier 1 -> Tier 2
    -> Tier 3 Swarm -> HITL Adjudication -> FinCEN Submission -> Cryptographic Audit.
    """
    # 1. Modify transaction to trigger high suspicion
    sample_transaction.amount = 185000.0
    sample_transaction.channel = PaymentChannel.INSTANT_ACH
    sample_transaction.metadata = {
        "scenario": "TYPOLOGY_2_PEELING_CHAIN",
        "dwell_time_seconds": 45,
        "throughput_ratio": 0.98,
    }

    # 2. Data Engineering Pipeline
    raw_txn, tokenized_txn, online_feats = data_pipeline.process_incoming_transaction(sample_transaction)
    assert tokenized_txn.is_tokenized is True

    # 3. Tier 1 Deterministic Rules
    tier1_res = tier1_engine.evaluate(raw_txn)
    assert tier1_res.is_blocked is False

    # 4. Tier 2 ML & Topological Scoring
    scoring = model_blender.score_transaction(tokenized_txn)
    assert scoring.s_final >= 0.35

    # 5. Triage Gate
    alert = triage_gate.evaluate_gate(tokenized_txn, tier1_res, scoring)
    assert alert is not None

    # 6. Multi-Agent Swarm (Tier 3)
    dossier = swarm_orchestrator.investigate_alert(alert)
    assert dossier.execution_dag.is_completed is True
    assert dossier.draft_sar is not None
    assert dossier.groundedness_score >= 0.80

    # 7. HITL Case Creation
    case = case_manager.create_case_from_dossier(dossier)
    assert case.case_id in case_manager._cases

    # 8. Human Investigator Adjudication
    approved_case = adjudication_service.approve_sar(
        case_id=case.case_id,
        analyst_id="ANALYST_CARTER",
        investigator_notes="Confirmed rapid pass-through peeling chain.",
    )
    assert approved_case.status == DecisionStatus.SAR_APPROVED

    # 9. Regulatory Submission Gateway
    submission = sar_gateway.submit_sar(approved_case)
    assert submission["receipt"]["status"] == "ACCEPTED_BY_REGULATOR"
    assert submission["receipt"]["sha256_digest"] is not None

    # 10. Audit Chain Verification
    audit_check = audit_ledger.verify_integrity()
    assert audit_check["is_valid"] is True
