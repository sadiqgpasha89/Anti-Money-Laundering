"""Velocity and high-frequency gatekeeper rules."""

from typing import Optional
from src.core.config import settings
from src.core.models import Transaction, RuleHit


class VelocityBoundaryRules:
    """Evaluates rapid velocity boundaries, failed authorizations, and FATF blacklists."""

    @staticmethod
    def check_failed_authorizations(txn: Transaction) -> Optional[RuleHit]:
        """Flag accounts exceeding threshold of failed authorization attempts."""
        if txn.telemetry.failed_auth_count >= settings.MAX_VELOCITY_FAILURES:
            return RuleHit(
                rule_id="RULE_VEL_001",
                rule_name="RAPID_FAILED_AUTH_BURST",
                is_hard_stop=True,
                confidence=1.0,
                description=f"Account has {txn.telemetry.failed_auth_count} failed auth attempts (limit: {settings.MAX_VELOCITY_FAILURES})",
                trigger_value={"failed_auth_count": txn.telemetry.failed_auth_count},
            )
        return None

    @staticmethod
    def check_fatf_call_for_action(txn: Transaction) -> Optional[RuleHit]:
        """Enforce static blacklist on FATF Call-For-Action jurisdictions."""
        country = txn.sender.country.upper()
        if country in settings.HIGH_RISK_COUNTRIES:
            return RuleHit(
                rule_id="RULE_FATF_001",
                rule_name="FATF_CALL_FOR_ACTION_JURISDICTION",
                is_hard_stop=country in ["KP", "IR"],  # KP and IR are hard stops
                confidence=0.90,
                description=f"Transaction originating from FATF High-Risk Jurisdiction: {country}",
                trigger_value={"country": country},
            )
        return None
