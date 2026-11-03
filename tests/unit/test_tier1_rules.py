"""Unit tests for Tier 1 Deterministic Rules Engine."""

import pytest
from src.core.models import DecisionStatus, PaymentChannel
from src.datascience.tier1_rules.sanctions import (
    jaro_winkler_similarity,
    soundex,
    sanctions_matcher,
)
from src.datascience.tier1_rules.thresholds import StatutoryThresholdRules
from src.datascience.tier1_rules.velocity_rules import VelocityBoundaryRules
from src.datascience.tier1_rules.engine import tier1_engine


def test_jaro_winkler_and_soundex():
    """Verify string similarity and phonetic encoding."""
    # Identical strings
    assert jaro_winkler_similarity("VLADIMIR KOROLYOV", "VLADIMIR KOROLYOV") == 1.0
    # Close variation
    sim = jaro_winkler_similarity("VLAD KOROL", "VLADIMIR KOROLYOV")
    assert sim > 0.70
    # Soundex
    assert soundex("KOROLYOV") == soundex("KOROLIOV")
    assert soundex("SMITH") == soundex("SMYTH")


def test_sanctions_matcher_exact_and_alias():
    """Test sanctions matching against OFAC seed list."""
    # Exact name
    hit = sanctions_matcher.check_hard_stop("VLADIMIR KOROLYOV", "RU")
    assert hit is not None
    assert hit.is_hard_stop is True
    assert "OFAC_SDN" in hit.description

    # Alias match
    hit_alias = sanctions_matcher.check_hard_stop("VLAD KOROL", "RU")
    assert hit_alias is not None
    assert hit_alias.is_hard_stop is True

    # Benign customer
    hit_benign = sanctions_matcher.check_hard_stop("ALICE FREEMAN", "US")
    assert hit_benign is None


def test_sanctions_embargoed_jurisdiction():
    """Test FATF embargoed jurisdictions."""
    hit_kp = sanctions_matcher.check_hard_stop("NORMAL TRADING CORP", "KP")
    assert hit_kp is not None
    assert hit_kp.is_hard_stop is True
    assert "KP" in hit_kp.description


def test_ctr_statutory_threshold(sample_transaction):
    """Test statutory CTR rule for >= $10k cash deposits."""
    # Under CTR threshold
    sample_transaction.channel = PaymentChannel.CASH_DEPOSIT
    sample_transaction.amount = 9500.0
    assert StatutoryThresholdRules.check_ctr_threshold(sample_transaction) is None

    # Meets CTR threshold
    sample_transaction.amount = 10000.0
    hit = StatutoryThresholdRules.check_ctr_threshold(sample_transaction)
    assert hit is not None
    assert hit.rule_id == "RULE_CTR_001"
    assert hit.is_hard_stop is False  # Mandatory reporting, not freeze


def test_velocity_boundary_rules(sample_transaction):
    """Test failed authorization gatekeeper."""
    sample_transaction.telemetry.failed_auth_count = 2
    assert VelocityBoundaryRules.check_failed_authorizations(sample_transaction) is None

    sample_transaction.telemetry.failed_auth_count = 6
    hit = VelocityBoundaryRules.check_failed_authorizations(sample_transaction)
    assert hit is not None
    assert hit.is_hard_stop is True
    assert hit.rule_id == "RULE_VEL_001"


def test_tier1_engine_full_execution(sample_transaction, sanctions_transaction):
    """Test end-to-end Tier 1 execution and latency SLA."""
    # Normal transaction passes
    res_normal = tier1_engine.evaluate(sample_transaction)
    assert res_normal.is_blocked is False
    assert res_normal.status == DecisionStatus.PASSED
    assert res_normal.latency_ms < 20.0  # SLA < 20ms

    # Sanctioned transaction blocked
    res_sanc = tier1_engine.evaluate(sanctions_transaction)
    assert res_sanc.is_blocked is True
    assert res_sanc.status == DecisionStatus.HOLD
    assert len(res_sanc.rule_hits) >= 1
