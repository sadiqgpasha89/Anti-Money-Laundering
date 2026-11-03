"""Case Management and Human Adjudication Cockpit routes."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.models import DecisionStatus
from src.hitl.case_manager import case_manager
from src.hitl.adjudication import adjudication_service
from src.hitl.sar_gateway import sar_gateway

router = APIRouter(prefix="/api/cases", tags=["Case Management & HITL"])


class ApproveSARRequest(BaseModel):
    analyst_id: str = "ANALYST_SARAH_CONNOR_AML_07"
    notes: Optional[str] = "Approved following verified corporate registry and funds-flow analysis."
    edited_narrative: Optional[str] = None


class OverrideRequest(BaseModel):
    analyst_id: str = "ANALYST_SARAH_CONNOR_AML_07"
    override_reason_code: str
    justification_notes: str


@router.get("")
def list_cases(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all cases with optional status filter."""
    st_enum = DecisionStatus(status) if status else None
    cases = case_manager.list_cases(st_enum)
    return [c.model_dump() for c in cases]


@router.get("/{case_id}")
def get_case(case_id: str) -> Dict[str, Any]:
    """Retrieve detailed case dossier."""
    case = case_manager.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case.model_dump()


@router.post("/{case_id}/approve")
def approve_case_sar(case_id: str, req: ApproveSARRequest) -> Dict[str, Any]:
    """Approve draft SAR for regulatory submission."""
    try:
        case = adjudication_service.approve_sar(
            case_id=case_id,
            analyst_id=req.analyst_id,
            investigator_notes=req.notes,
            edited_narrative=req.edited_narrative,
        )
        return {"status": "SUCCESS", "case": case.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/override")
def override_case_decision(case_id: str, req: OverrideRequest) -> Dict[str, Any]:
    """Override automated recommendation with mandatory audit code."""
    try:
        case = adjudication_service.override_decision(
            case_id=case_id,
            analyst_id=req.analyst_id,
            override_reason_code=req.override_reason_code,
            justification_notes=req.justification_notes,
        )
        return {"status": "SUCCESS", "case": case.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/submit-sar")
def submit_to_fincen(case_id: str) -> Dict[str, Any]:
    """Transmit approved SAR to FinCEN gateway."""
    case = case_manager.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    try:
        res = sar_gateway.submit_sar(case)
        return {"status": "SUBMITTED", "receipt": res["receipt"], "fincen_payload": res["fincen_payload"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
