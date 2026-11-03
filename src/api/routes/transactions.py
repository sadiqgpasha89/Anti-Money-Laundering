"""Transaction ingress, streaming, and Tier 1 screening routes."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.core.config import settings
from src.core.models import Transaction, DecisionStatus
from src.data_engineering.ingestion import transaction_ingestor
from src.data_engineering.pipeline import data_pipeline
from src.datascience.tier1_rules.engine import tier1_engine
from src.datascience.tier2_ml.model_blender import model_blender
from src.datascience.tier2_ml.triage_gate import triage_gate
from src.agents.swarm_orchestrator import swarm_orchestrator
from src.hitl.case_manager import case_manager
from src.metrics.engine import metrics_engine

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

# In-memory recents cache for UI stream
recent_stream_events: List[Dict[str, Any]] = []


@router.post("/ingest")
def ingest_transaction(raw_payload: Dict[str, Any], background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Ingest single transaction and execute pipeline through Tiers 1, 2, and 3."""
    txn = transaction_ingestor.parse_raw_event(raw_payload)

    # 1. Data Engineering Pipeline (OpenStack -> GCP)
    raw_txn, tokenized_txn, online_features = data_pipeline.process_incoming_transaction(txn)

    # 2. Tier 1 Deterministic Rules Engine
    tier1_res = tier1_engine.evaluate(raw_txn)
    metrics_engine.record_tier1_latency(tier1_res.latency_ms)

    # 3. Tier 2 ML & Graph Inference
    ml_scoring = model_blender.score_transaction(tokenized_txn)
    metrics_engine.record_tier2_latency(ml_scoring.latency_ms)

    # 4. Triage Gate Evaluation
    alert = triage_gate.evaluate_gate(tokenized_txn, tier1_res, ml_scoring)

    dossier = None
    case_id = None

    if alert:
        metrics_engine.record_alert()
        if alert.status == DecisionStatus.HOLD:
            # Immediate freeze on sanctions match
            metrics_engine.record_alert(is_sar=True)
        else:
            # Multi-Agent Swarm (Tier 3)
            dossier = swarm_orchestrator.investigate_alert(alert)
            case = case_manager.create_case_from_dossier(dossier)
            case_id = case.case_id

            if dossier.triage_determination == DecisionStatus.AUTO_CLEARED:
                metrics_engine.record_alert(auto_cleared=True)
            elif dossier.triage_determination in [DecisionStatus.ESCALATED_HUMAN, DecisionStatus.SAR_APPROVED]:
                metrics_engine.record_alert(is_sar=True)

    event_summary = {
        "transaction_id": raw_txn.transaction_id,
        "timestamp": raw_txn.timestamp.isoformat(),
        "amount": raw_txn.amount,
        "currency": raw_txn.currency,
        "sender": raw_txn.sender.name,
        "receiver": raw_txn.receiver.name,
        "tier1_status": tier1_res.status.value,
        "tier1_latency_ms": tier1_res.latency_ms,
        "tier2_score": ml_scoring.s_final,
        "inferred_typology": ml_scoring.inferred_typology.value,
        "alert_triggered": alert is not None,
        "alert_id": alert.alert_id if alert else None,
        "case_id": case_id,
        "status": dossier.triage_determination.value if dossier else (
            DecisionStatus.HOLD.value if tier1_res.is_blocked else DecisionStatus.PASSED.value
        ),
    }

    recent_stream_events.insert(0, event_summary)
    if len(recent_stream_events) > 100:
        recent_stream_events.pop()

    return {
        "event": event_summary,
        "tier1_result": tier1_res.model_dump(),
        "tier2_scoring": ml_scoring.model_dump(),
        "dossier": dossier.model_dump() if dossier else None,
    }


@router.get("/stream")
def get_recent_stream(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent transaction stream events for live monitoring UI."""
    return recent_stream_events[:limit]


@router.get("/seed-populate")
def populate_seed_stream() -> Dict[str, Any]:
    """Pre-populate the system with transactions from data/seed_transactions.json."""
    txns = transaction_ingestor.load_seed_transactions(str(settings.SEED_TRANSACTIONS_PATH))
    processed = []

    for txn in txns:
        res = ingest_transaction(txn.model_dump(), BackgroundTasks())
        processed.append(res["event"])

    return {
        "message": f"Successfully ingested {len(processed)} seed transactions.",
        "processed_count": len(processed),
        "events": processed,
    }
