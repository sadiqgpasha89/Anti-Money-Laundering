"""Dynamic Triage Gate for Multi-Tier Alert Routing."""

import uuid
from typing import Optional
from src.core.config import settings
from src.core.models import (
    Transaction,
    Tier1Result,
    RiskScoreResult,
    Alert,
    DecisionStatus,
)


class TriageGate:
    """Routes scored transactions to Approved, Agentic Swarm (Tier 3), or Direct Escalation."""

    def evaluate_gate(
        self,
        txn: Transaction,
        tier1: Tier1Result,
        scoring: RiskScoreResult,
    ) -> Optional[Alert]:
        """
        Evaluate gating policy based on combined rules and model scores.
        Returns an Alert if flagged for Tier 3 or human escalation, or None if auto-approved.
        """
        # Hard stop already flagged by Tier 1
        if tier1.is_blocked:
            return Alert(
                alert_id=f"ALT-SANC-{uuid.uuid4().hex[:8].upper()}",
                transaction=txn,
                tier1_result=tier1,
                ml_scoring=scoring,
                status=DecisionStatus.HOLD,
            )

        # Dynamic Triage Logic
        if scoring.s_final < settings.TIER2_LOW_THRESHOLD:
            # Benign - Auto Approved
            return None

        # Route to Tier 3 Agentic Swarm or Human Escalation
        if scoring.s_final < settings.TIER2_HIGH_THRESHOLD:
            status = DecisionStatus.TRIAGING
        else:
            status = DecisionStatus.ESCALATED_HUMAN

        return Alert(
            alert_id=f"ALT-ML-{uuid.uuid4().hex[:8].upper()}",
            transaction=txn,
            tier1_result=tier1,
            ml_scoring=scoring,
            status=status,
        )


triage_gate = TriageGate()
