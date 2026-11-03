"""API routes package."""

from src.api.routes.transactions import router as transactions_router
from src.api.routes.pipeline import router as pipeline_router
from src.api.routes.models import router as models_router
from src.api.routes.agents import router as agents_router
from src.api.routes.cases import router as cases_router
from src.api.routes.metrics import router as metrics_router
from src.api.routes.mlops import router as mlops_router
from src.api.routes.typologies import router as typologies_router
from src.api.routes.audit import router as audit_router

__all__ = [
    "transactions_router",
    "pipeline_router",
    "models_router",
    "agents_router",
    "cases_router",
    "metrics_router",
    "mlops_router",
    "typologies_router",
    "audit_router",
]
