"""Tier 1 Deterministic Rules Engine (RETE algorithm, Sub-20ms latency)."""

from src.datascience.tier1_rules.engine import Tier1RulesEngine, tier1_engine
from src.datascience.tier1_rules.sanctions import SanctionsMatcher, sanctions_matcher
from src.datascience.tier1_rules.thresholds import StatutoryThresholdRules
from src.datascience.tier1_rules.velocity_rules import VelocityBoundaryRules

__all__ = [
    "Tier1RulesEngine",
    "tier1_engine",
    "SanctionsMatcher",
    "sanctions_matcher",
    "StatutoryThresholdRules",
    "VelocityBoundaryRules",
]
