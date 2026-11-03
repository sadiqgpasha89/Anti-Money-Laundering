"""MLOps Model Governance Registry (Federal Reserve SR 11-7 compliant)."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ModelMetadata(BaseModel):
    """Metadata container for governed models."""
    model_id: str
    name: str
    version: str
    model_type: str  # SUPERVISED_GBM, AUTOENCODER, RGCN_GAT
    status: str      # CHAMPION, CHALLENGER, RETIRED, SHADOW
    training_data_hash: str
    prauc_score: float
    f1_score: float
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ModelRegistry:
    """Manages model versions, champion/challenger designation, and lineage."""

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._seed_registry()

    def _seed_registry(self):
        """Seed registry with certified production models."""
        self.register_model(
            ModelMetadata(
                model_id="MOD-GBM-001",
                name="AML-GradientBoostedClassifier",
                version="v2.4.1",
                model_type="SUPERVISED_GBM",
                status="CHAMPION",
                training_data_hash="a1b2c3d4e5f67890123456789abcdef0",
                prauc_score=0.924,
                f1_score=0.887,
                parameters={"n_estimators": 50, "learning_rate": 0.1, "max_depth": 3},
            )
        )
        self.register_model(
            ModelMetadata(
                model_id="MOD-GBM-002",
                name="AML-GradientBoostedClassifier-Experimental",
                version="v2.5.0-rc1",
                model_type="SUPERVISED_GBM",
                status="CHALLENGER",
                training_data_hash="f0e1d2c3b4a567890123456789abcdef",
                prauc_score=0.938,
                f1_score=0.895,
                parameters={"n_estimators": 75, "learning_rate": 0.08, "max_depth": 4},
            )
        )
        self.register_model(
            ModelMetadata(
                model_id="MOD-AE-001",
                name="AML-ReconstructionAutoencoder",
                version="v1.8.0",
                model_type="AUTOENCODER",
                status="CHAMPION",
                training_data_hash="99887766554433221100aabbccddeeff",
                prauc_score=0.865,
                f1_score=0.812,
                parameters={"hidden_layers": [4, 2, 4], "activation": "relu"},
            )
        )
        self.register_model(
            ModelMetadata(
                model_id="MOD-RGCN-001",
                name="AML-RelationalGraphNeuralNet",
                version="v1.2.0",
                model_type="RGCN_GAT",
                status="CHAMPION",
                training_data_hash="11223344556677889900aabbccddeeff",
                prauc_score=0.910,
                f1_score=0.870,
                parameters={"num_relations": 4, "embedding_dim": 32},
            )
        )

    def register_model(self, model: ModelMetadata):
        """Add model to registry."""
        self._models[model.model_id] = model

    def get_champion(self, model_type: str) -> Optional[ModelMetadata]:
        """Retrieve active champion model for specific model type."""
        for m in self._models.values():
            if m.model_type == model_type and m.status == "CHAMPION":
                return m
        return None

    def list_models(self) -> List[ModelMetadata]:
        """List all models in registry."""
        return list(self._models.values())


model_registry = ModelRegistry()
