"""Unit tests for Compliance Critic factual entailment and anti-hallucination verification."""

import pytest
from src.core.models import SuspiciousActivityReport
from src.agents.compliance_critic import compliance_critic_agent


def test_compliance_critic_factual_approval():
    """Test critic approves narrative with factual grounding in evidence corpus."""
    evidence = {
        "transaction_id": "TXN-1234",
        "amount": 95000.0,
        "sender_account": "ACCT-9988",
        "sender_name": "ACME LOGISTICS",
        "findings": "Fund movements across Delaware accounts observed in sequential order during investigation.",
    }

    grounded_sar = SuspiciousActivityReport(
        sar_id="SAR-TEST-001",
        alert_id="ALT-001",
        suspect_name="ACME LOGISTICS",
        total_amount_flagged=95000.0,
        narrative=(
            "On 2026-09-14, account ACME LOGISTICS engaged in transactions totaling $95000.0. "
            "Evidence indicates fund movements across Delaware accounts in sequential order."
        ),
    )

    approved, score, evals, ungrounded = compliance_critic_agent.audit_narrative(
        sar=grounded_sar,
        dossier_evidence=evidence,
    )
    assert approved is True
    assert score >= 0.85
    assert len(evals) > 0


def test_compliance_critic_rejection_on_hallucination():
    """Test critic rejects narrative containing hallucinated external entities."""
    evidence = {
        "sender_name": "BOB SMITH",
        "amount": 500.0,
    }

    hallucinated_sar = SuspiciousActivityReport(
        sar_id="SAR-TEST-HALLUCINATED",
        alert_id="ALT-002",
        suspect_name="BOB SMITH",
        total_amount_flagged=500.0,
        narrative=(
            "The subject was observed operating a clandestine nuclear uranium enrichment facility in Tehran. "
            "Funds were routed via intercontinental ballistic missile procurement front companies in Pyongyang."
        ),
    )

    # Use strict threshold
    compliance_critic_agent.threshold = 0.90
    approved, score, evals, ungrounded = compliance_critic_agent.audit_narrative(
        sar=hallucinated_sar,
        dossier_evidence=evidence,
    )
    assert approved is False
    assert len(ungrounded) > 0
