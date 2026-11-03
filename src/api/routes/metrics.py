"""Multi-Dimensional Metrics API routes."""

from typing import Dict, Any
from fastapi import APIRouter
from src.metrics.engine import metrics_engine

router = APIRouter(prefix="/api/metrics", tags=["Metrics & Observatory"])


@router.get("/all")
def get_all_metrics() -> Dict[str, Any]:
    """Retrieve full 5-tier performance matrix."""
    return metrics_engine.get_consolidated_scorecard()


@router.get("/business")
def get_business_metrics() -> Dict[str, Any]:
    """Retrieve Business & Compliance operational metrics."""
    return metrics_engine.get_consolidated_scorecard()["business_metrics"]


@router.get("/system")
def get_system_metrics() -> Dict[str, Any]:
    """Retrieve System latency and throughput metrics."""
    return metrics_engine.get_consolidated_scorecard()["system_metrics"]


@router.get("/rag")
def get_rag_metrics() -> Dict[str, Any]:
    """Retrieve RAG Triad and generative grounding metrics."""
    return metrics_engine.get_consolidated_scorecard()["rag_metrics"]


@router.get("/agentic")
def get_agentic_metrics() -> Dict[str, Any]:
    """Retrieve Agentic reasoning and execution efficiency metrics."""
    return metrics_engine.get_consolidated_scorecard()["agentic_metrics"]


@router.get("/ml")
def get_ml_metrics() -> Dict[str, Any]:
    """Retrieve ML statistical and calibration metrics."""
    return metrics_engine.get_consolidated_scorecard()["ml_metrics"]
