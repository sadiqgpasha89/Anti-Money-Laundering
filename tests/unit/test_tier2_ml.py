"""Unit tests for Tier 2 Machine Learning, Autoencoders, and Graph Analytics."""

import pytest
from src.core.models import DecisionStatus, RiskTier
from src.datascience.tier2_ml.supervised import supervised_scorer
from src.datascience.tier2_ml.autoencoder import anomaly_autoencoder
from src.datascience.tier2_ml.graph_neural_net import graph_scorer
from src.datascience.tier2_ml.model_blender import model_blender
from src.datascience.tier2_ml.explainability import explainability_engine
from src.datascience.tier2_ml.triage_gate import triage_gate
from src.datascience.tier1_rules.engine import tier1_engine


def test_supervised_scorer(sample_transaction):
    """Test supervised scoring output range and feature importances."""
    score = supervised_scorer.predict_score(sample_transaction)
    assert 0.0 <= score <= 1.0

    importances = supervised_scorer.get_feature_importances()
    assert "amount" in importances
    assert "v1h_v30d_ratio" in importances
    assert sum(importances.values()) > 0.0


def test_autoencoder_reconstruction(sample_transaction):
    """Test autoencoder reconstruction anomaly scoring."""
    from src.core.models import Transaction, PartyProfile, PaymentChannel
    clean_txn = Transaction(
        transaction_id="TXN-AE-CLEAN-001",
        amount=150.0,
        currency="USD",
        channel=PaymentChannel.DOMESTIC_ACH,
        sender=PartyProfile(
            customer_id="CUST-CLEAN-01",
            account_id="ACCT-CLEAN-01A",
            name="NORMAL ALICE",
            country="US",
            risk_rating=RiskTier.LOW,
            account_tenure_months=24,
            historical_monthly_avg_vol=1500.0,
        ),
        receiver=PartyProfile(
            customer_id="CUST-CLEAN-02",
            account_id="ACCT-CLEAN-02B",
            name="NORMAL BOB",
            country="US",
            risk_rating=RiskTier.LOW,
        ),
    )
    score = anomaly_autoencoder.predict_score(clean_txn)
    assert 0.0 <= score <= 1.0
    # Normal sample should have relatively low anomaly score
    assert score < 0.60


def test_graph_topological_scorer(sample_transaction):
    """Test multigraph topological scoring."""
    score = graph_scorer.predict_score(sample_transaction)
    assert 0.0 <= score <= 1.0


def test_model_blender_and_explainability(sample_transaction):
    """Test ensemble blending S_final = w1*S_sup + w2*S_unsup + w3*S_graph and SHAP."""
    res = model_blender.score_transaction(sample_transaction)
    assert 0.0 <= res.s_final <= 1.0
    assert res.s_final == pytest.approx(
        0.40 * res.s_supervised + 0.30 * res.s_unsupervised + 0.30 * res.s_graph,
        abs=0.01,
    )
    assert res.latency_ms < 100.0  # SLA < 100ms
    assert len(res.shap_contributions) > 0
    assert res.counterfactual_explanation is not None


def test_triage_gate_routing(sample_transaction):
    """Test triage gate thresholds (Pass vs Agentic Triage vs Escalation)."""
    tier1_res = tier1_engine.evaluate(sample_transaction)
    scoring = model_blender.score_transaction(sample_transaction)

    # Benign low score should produce None (auto-approved)
    scoring.s_final = 0.20
    alert_pass = triage_gate.evaluate_gate(sample_transaction, tier1_res, scoring)
    assert alert_pass is None

    # Intermediate score should route to TRIAGING (Tier 3 Agents)
    scoring.s_final = 0.55
    alert_triage = triage_gate.evaluate_gate(sample_transaction, tier1_res, scoring)
    assert alert_triage is not None
    assert alert_triage.status == DecisionStatus.TRIAGING

    # High score should route to ESCALATED_HUMAN
    scoring.s_final = 0.85
    alert_escalate = triage_gate.evaluate_gate(sample_transaction, tier1_res, scoring)
    assert alert_escalate is not None
    assert alert_escalate.status == DecisionStatus.ESCALATED_HUMAN
