"""FastAPI Application Main Entrypoint for AML Hybrid Architecture Platform."""

import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from src.core.config import settings
from src.data_engineering.ingestion import transaction_ingestor
from src.api.routes.transactions import ingest_transaction
from fastapi import BackgroundTasks

from src.api.routes import (
    transactions_router,
    pipeline_router,
    models_router,
    agents_router,
    cases_router,
    metrics_router,
    mlops_router,
    typologies_router,
    audit_router,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    # Pre-populate seed stream for immediate exploration
    try:
        txns = transaction_ingestor.load_seed_transactions(str(settings.SEED_TRANSACTIONS_PATH))
        for txn in txns:
            ingest_transaction(txn.model_dump(), BackgroundTasks())
    except Exception as e:
        print(f"Seed population notice: {e}")
    yield


app = FastAPI(
    title="Hybrid Anti-Money Laundering (AML) Platform",
    description="Deterministic Rules, Machine Learning & Graph Neural Nets, and Cognitive Multi-Agent Swarm (OpenStack + GCP)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Mount Static & Templates
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serve AML Investigator Cockpit and Operations Center."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.APP_NAME},
    )


@app.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "HEALTHY",
        "app_env": settings.APP_ENV,
        "openstack_region": settings.OPENSTACK_REGION,
        "gcp_project_id": settings.GCP_PROJECT_ID,
        "safe_degradation_mode": settings.SAFE_DEGRADATION_MODE,
        "crypto_audit_chain_length": len(list(settings.DATA_DIR.glob("*"))),
    }


# Include Routers
app.include_router(transactions_router)
app.include_router(pipeline_router)
app.include_router(models_router)
app.include_router(agents_router)
app.include_router(cases_router)
app.include_router(metrics_router)
app.include_router(mlops_router)
app.include_router(typologies_router)
app.include_router(audit_router)
