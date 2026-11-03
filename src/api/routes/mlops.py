"""MLOps model governance, drift radar, and champion-challenger routes."""

from typing import Dict, Any, List
from fastapi import APIRouter
from src.mlops.registry import model_registry
from src.mlops.drift_detector import drift_detector
from src.mlops.shadow_validator import shadow_validator

router = APIRouter(prefix="/api/mlops", tags=["MLOps"])


@router.get("/models")
def list_models() -> List[Dict[str, Any]]:
    """List all registered models under Model Risk Management governance."""
    return [m.model_dump() for m in model_registry.list_models()]


@router.get("/drift")
def get_drift_radar() -> Dict[str, Any]:
    """Execute continuous drift evaluation across feature distributions and concept stability."""
    # Synthetic baseline vs current operational distribution
    baseline = {
        "amount": [120, 150, 210, 95, 300, 180, 240, 110, 420, 160],
        "v1h_v30d_ratio": [0.05, 0.08, 0.04, 0.12, 0.09, 0.06, 0.07, 0.04, 0.15, 0.08],
        "geo_entropy": [0.10, 0.15, 0.08, 0.22, 0.14, 0.11, 0.09, 0.05, 0.18, 0.12],
    }
    current = {
        "amount": [140, 175, 230, 105, 320, 195, 260, 125, 450, 180],
        "v1h_v30d_ratio": [0.06, 0.09, 0.05, 0.13, 0.10, 0.07, 0.08, 0.05, 0.16, 0.09],
        "geo_entropy": [0.12, 0.16, 0.09, 0.24, 0.15, 0.12, 0.10, 0.06, 0.19, 0.14],
    }
    error_series = [0.02, 0.03, 0.02, 0.04, 0.03, 0.02, 0.03, 0.05, 0.04, 0.03]

    report = drift_detector.evaluate_drift_report(baseline, current, error_series)
    return report


@router.get("/shadow")
def get_shadow_performance() -> Dict[str, Any]:
    """Retrieve Champion vs Challenger model divergence metrics."""
    return {
        "divergence_rate": shadow_validator.get_divergence_rate(),
        "tolerance": shadow_validator.tolerance,
        "recent_divergences": shadow_validator.get_recent_divergences(limit=10),
    }
