"""Human Investigator Adjudication and Sign-Off Service."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.core.models import Case, DecisionStatus
from src.core.crypto_audit import audit_ledger
from src.hitl.case_manager import case_manager


class AdjudicationService:
    """Handles investigator sign-off, narrative modification, and model overrides."""

    def approve_sar(
        self,
        case_id: str,
        analyst_id: str,
        investigator_notes: Optional[str] = None,
        edited_narrative: Optional[str] = None,
    ) -> Case:
        """Sign off on draft SAR for regulatory submission."""
        case = case_manager.get_case(case_id)
        if not case:
            raise ValueError(f"Case '{case_id}' not found.")

        case.status = DecisionStatus.SAR_APPROVED
        case.assigned_analyst = analyst_id
        case.adjudication_timestamp = datetime.now(timezone.utc)
        case.updated_at = datetime.now(timezone.utc)

        if case.draft_sar:
            case.draft_sar.human_approved = True
            case.draft_sar.human_notes = investigator_notes
            if edited_narrative:
                case.draft_sar.narrative = edited_narrative

        # Cryptographic Audit Record: Human Decision
        audit_ledger.record_event(
            event_type="HUMAN_DECISION_APPROVE",
            payload={
                "case_id": case_id,
                "analyst_id": analyst_id,
                "status": DecisionStatus.SAR_APPROVED.value,
                "notes": investigator_notes,
                "sar_id": case.draft_sar.sar_id if case.draft_sar else None,
            },
            actor=analyst_id,
        )

        return case

    def override_decision(
        self,
        case_id: str,
        analyst_id: str,
        override_reason_code: str,
        justification_notes: str,
    ) -> Case:
        """
        Override automated agent/model recommendation with mandatory audit rationale:
        E.g. FALSE_POSITIVE_KNOWN_LEGITIMATE_BUSINESS, AGGRESSIVE_ALERT_CLEARANCE, INSUFFICIENT_EVIDENCE
        """
        case = case_manager.get_case(case_id)
        if not case:
            raise ValueError(f"Case '{case_id}' not found.")

        case.status = DecisionStatus.SAR_OVERRIDDEN
        case.assigned_analyst = analyst_id
        case.override_reason_code = override_reason_code
        case.adjudication_timestamp = datetime.now(timezone.utc)
        case.updated_at = datetime.now(timezone.utc)

        # Cryptographic Audit Record: Model Override
        audit_ledger.record_event(
            event_type="HUMAN_DECISION_OVERRIDE",
            payload={
                "case_id": case_id,
                "analyst_id": analyst_id,
                "override_code": override_reason_code,
                "justification": justification_notes,
                "status": DecisionStatus.SAR_OVERRIDDEN.value,
            },
            actor=analyst_id,
        )

        return case


adjudication_service = AdjudicationService()
