"""Statutory Currency Transaction Reporting (CTR) and Threshold Rules."""

from typing import Optional
from src.core.config import settings
from src.core.models import Transaction, RuleHit, PaymentChannel


class StatutoryThresholdRules:
    """Evaluates non-negotiable statutory transaction threshold triggers."""

    @staticmethod
    def check_ctr_threshold(txn: Transaction) -> Optional[RuleHit]:
        """
        Statutory CTR rule: Raw cash or equivalent deposits >= $10,000 USD
        trigger mandatory Currency Transaction Reporting.
        """
        if txn.channel == PaymentChannel.CASH_DEPOSIT and txn.amount >= settings.TIER1_CTR_THRESHOLD:
            return RuleHit(
                rule_id="RULE_CTR_001",
                rule_name="STATUTORY_CTR_THRESHOLD_TRIGGER",
                is_hard_stop=False,  # Not a hard freeze, but statutory reporting mandate
                confidence=1.0,
                description=f"Raw cash deposit of ${txn.amount:,.2f} meets or exceeds statutory CTR threshold of ${settings.TIER1_CTR_THRESHOLD:,.2f}",
                trigger_value={"amount": txn.amount, "threshold": settings.TIER1_CTR_THRESHOLD},
            )
        return None

    @staticmethod
    def check_large_wire_threshold(txn: Transaction) -> Optional[RuleHit]:
        """Flag extraordinarily large wires (> $500,000) for instant priority review."""
        if txn.amount >= 500000.0 and txn.channel in [PaymentChannel.SWIFT_WIRE, PaymentChannel.CROSS_BORDER_WIRE]:
            return RuleHit(
                rule_id="RULE_WIRE_LARGE_001",
                rule_name="HIGH_VALUE_CROSS_BORDER_WIRE",
                is_hard_stop=False,
                confidence=0.95,
                description=f"High-value cross-border wire exceeding $500,000 (${txn.amount:,.2f})",
                trigger_value={"amount": txn.amount},
            )
        return None
