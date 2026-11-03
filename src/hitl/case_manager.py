"""Case Management System for AML Investigators."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from src.core.models import Case, Alert, DecisionStatus, SuspiciousActivityReport
from src.agents.state import InvestigationDossier


class CaseManager:
    """Manages case states, investigator assignments, and priority queues."""

    def __init__(self):
        self._cases: Dict[str, Case] = {}

    def create_case_from_dossier(self, dossier: InvestigationDossier) -> Case:
        """Instantiate an investigator review case from a completed agent dossier."""
        case_id = f"CASE-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

        case = Case(
            case_id=case_id,
            alert=dossier.alert,
            dossier={
                "dossier_id": dossier.dossier_id,
                "entity_findings": dossier.entity_resolution_findings,
                "forensic_findings": dossier.forensic_findings,
                "osint_findings": dossier.osint_findings,
                "groundedness_score": dossier.groundedness_score,
                "critic_approved": dossier.critic_approved,
                "clearance_rationale": dossier.clearance_rationale,
            },
            draft_sar=dossier.draft_sar,
            status=dossier.triage_determination,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self._cases[case_id] = case
        return case

    def get_case(self, case_id: str) -> Optional[Case]:
        """Retrieve case by ID."""
        return self._cases.get(case_id)

    def list_cases(self, status: Optional[DecisionStatus] = None) -> List[Case]:
        """List cases, optionally filtered by status."""
        cases = list(self._cases.values())
        if status:
            return [c for c in cases if c.status == status]
        return sorted(cases, key=lambda c: c.created_at, reverse=True)


case_manager = CaseManager()
