"""MLOps package for model governance, drift detection, and champion-challenger validation."""

from src.mlops.registry import ModelRegistry, model_registry
from src.mlops.drift_detector import DriftDetector, drift_detector
from src.mlops.shadow_validator import ShadowValidator, shadow_validator

__all__ = [
    "ModelRegistry",
    "model_registry",
    "DriftDetector",
    "drift_detector",
    "ShadowValidator",
    "shadow_validator",
]
