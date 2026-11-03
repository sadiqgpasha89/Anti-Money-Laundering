"""Multi-Agent Cognitive Swarm routes."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from src.core.models import Alert
from src.data_engineering.ingestion import transaction_ingestor
from src.datascience.tier1_rules.engine import tier1_engine
from src.datascience.tier2_ml.model_blender import model_blender
from src.datascience.tier2_ml.triage_gate import triage_gate
from src.agents.swarm_orchestrator import swarm_orchestrator
from src.llmops.trace_logger import trace_logger

router = APIRouter(prefix="/api/agents", tags=["Multi-Agent Swarm"])


@router.post("/investigate")
def run_agent_investigation(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Manually dispatch multi-agent swarm on a transaction."""
    txn = transaction_ingestor.parse_raw_event(raw_payload)
    tier1 = tier1_engine.evaluate(txn)
    ml_scoring = model_blender.score_transaction(txn)
    alert = triage_gate.evaluate_gate(txn, tier1, ml_scoring)

    if not alert:
        # Create ad-hoc alert for manual test investigation
        alert = Alert(
            alert_id=f"ALT-ADHOC-{txn.transaction_id}",
            transaction=txn,
            tier1_result=tier1,
            ml_scoring=ml_scoring,
        )

    dossier = swarm_orchestrator.investigate_alert(alert)
    return dossier.model_dump()


@router.get("/traces/{alert_id}")
def get_traces(alert_id: str) -> List[Dict[str, Any]]:
    """Retrieve execution trace for specified alert."""
    return trace_logger.get_traces_for_alert(alert_id)
