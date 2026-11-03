"""Unit tests for 5-Tier Metrics Framework."""

import pytest
from src.metrics.business_metrics import BusinessMetricsCalculator
from src.metrics.system_metrics import SystemMetricsCalculator
from src.metrics.rag_metrics import RAGMetricsCalculator
from src.metrics.agentic_metrics import AgenticMetricsCalculator
from src.metrics.ml_metrics import MLMetricsCalculator
from src.metrics.engine import metrics_engine


def test_business_metrics():
    """Test business impact metrics calculations."""
    conv = BusinessMetricsCalculator.calculate_conversion_rate(25, 100)
    assert conv == 0.25

    mtti = BusinessMetricsCalculator.calculate_mtti_reduction(baseline_hours=4.0, current_minutes=18.0)
    assert mtti["current_mtti_minutes"] == 18.0
    assert mtti["efficiency_gain_pct"] > 90.0

    labor = BusinessMetricsCalculator.calculate_labor_savings(resolved_alerts=100)
    assert labor["net_labor_savings_usd"] > 0.0


def test_system_metrics():
    """Test system infrastructure latency calculations."""
    latencies = [2.0, 3.0, 4.0, 5.0, 10.0, 15.0, 18.0, 22.0]
    stats = SystemMetricsCalculator.calculate_latency_percentiles(latencies)
    assert stats["p50"] > 0
    assert stats["p99"] >= stats["p95"] >= stats["p50"]


def test_rag_and_agentic_metrics():
    """Test RAG and Agentic metrics."""
    plan_rate = AgenticMetricsCalculator.calculate_plan_completion_rate(48, 50)
    assert plan_rate == 0.96

    critic_rej = AgenticMetricsCalculator.calculate_critic_rejection_rate(2, 50)
    assert critic_rej == 0.04


def test_ml_statistical_metrics():
    """Test PR-AUC, precision@K, ECE, and Brier score."""
    y_true = [0, 0, 0, 0, 1, 1, 1, 0, 1, 1]
    y_probs = [0.1, 0.2, 0.15, 0.05, 0.85, 0.92, 0.78, 0.35, 0.95, 0.88]

    prauc = MLMetricsCalculator.calculate_pr_auc(y_true, y_probs)
    assert 0.80 <= prauc <= 1.0

    prec_k = MLMetricsCalculator.calculate_precision_at_k(y_true, y_probs, k=5)
    assert prec_k == 1.0

    ece = MLMetricsCalculator.calculate_ece(y_true, y_probs)
    assert 0.0 <= ece <= 0.20

    brier = MLMetricsCalculator.calculate_brier_score(y_true, y_probs)
    assert 0.0 <= brier <= 0.15


def test_metrics_engine_consolidated():
    """Test unified metrics engine scorecard."""
    scorecard = metrics_engine.get_consolidated_scorecard()
    assert "business_metrics" in scorecard
    assert "system_metrics" in scorecard
    assert "rag_metrics" in scorecard
    assert "agentic_metrics" in scorecard
    assert "ml_metrics" in scorecard
