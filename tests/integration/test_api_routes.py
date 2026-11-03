"""Integration tests for FastAPI endpoints."""

import pytest


def test_health_endpoint(client):
    """Test health check."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "HEALTHY"


def test_transaction_ingest_and_stream(client, sample_transaction):
    """Test transaction ingestion and stream retrieval."""
    resp = client.post("/api/transactions/ingest", json=sample_transaction.model_dump(mode="json"))
    assert resp.status_code == 200
    data = resp.json()
    assert "event" in data
    assert "tier1_result" in data

    stream_resp = client.get("/api/transactions/stream?limit=5")
    assert stream_resp.status_code == 200
    assert len(stream_resp.json()) > 0


def test_pipeline_routes(client):
    """Test pipeline graph stats and tokenization endpoint."""
    stats = client.get("/api/pipeline/graph/stats").json()
    assert "total_nodes" in stats
    assert "total_edges" in stats

    tok = client.post("/api/pipeline/tokenize", json={"name": "SERGEY VOLKOV"}).json()
    assert tok["tokenized"]["name"].startswith("TOK_NAME_")


def test_metrics_routes(client):
    """Test all metrics endpoints."""
    all_metrics = client.get("/api/metrics/all").json()
    assert "business_metrics" in all_metrics
    assert "system_metrics" in all_metrics
    assert "rag_metrics" in all_metrics
    assert "agentic_metrics" in all_metrics
    assert "ml_metrics" in all_metrics


def test_typologies_and_simulation(client):
    """Test typology catalog and 1-click simulation."""
    catalog = client.get("/api/typologies/catalog").json()
    assert len(catalog) == 8

    # Simulate typology #1 (Smurfing)
    sim = client.post("/api/typologies/simulate/1").json()
    assert "simulation_result" in sim
    assert sim["typology"]["id"] == 1


def test_crypto_audit_routes(client):
    """Test cryptographic audit chain and integrity verification."""
    chain = client.get("/api/audit/chain?limit=10").json()
    assert len(chain) > 0

    verify = client.get("/api/audit/verify").json()
    assert verify["is_valid"] is True
