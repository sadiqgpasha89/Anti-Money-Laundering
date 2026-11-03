"""Machine Learning scoring and explainability routes."""

from typing import Dict, Any
from fastapi import APIRouter
from src.core.models import Transaction
from src.data_engineering.ingestion import transaction_ingestor
from src.datascience.tier2_ml.supervised import supervised_scorer
from src.datascience.tier2_ml.model_blender import model_blender
from src.datascience.tier2_ml.explainability import explainability_engine

router = APIRouter(prefix="/api/models", tags=["Machine Learning"])


@router.get("/feature-importance")
def get_feature_importances() -> Dict[str, Any]:
    """Retrieve supervised model global feature importances."""
    return {"feature_importances": supervised_scorer.get_feature_importances()}


@router.post("/score")
def score_sample_transaction(raw_txn: Dict[str, Any]) -> Dict[str, Any]:
    """Score a transaction against Tier 2 ML & GNN ensemble."""
    txn = transaction_ingestor.parse_raw_event(raw_txn)
    result = model_blender.score_transaction(txn)
    return result.model_dump()


@router.post("/counterfactual")
def get_counterfactual(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate regulatory counterfactual for arbitrary transaction parameters."""
    raw_txn = payload.get("transaction", {})
    txn = transaction_ingestor.parse_raw_event(raw_txn)
    score = float(payload.get("score", 0.75))
    counterfactual = explainability_engine.generate_counterfactual(txn, score)
    return {"counterfactual_explanation": counterfactual, "input_score": score}
