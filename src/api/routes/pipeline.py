"""Data engineering and feature store inspection routes."""

from typing import Dict, Any
from fastapi import APIRouter
from src.data_engineering.tokenizer import pii_tokenizer
from src.data_engineering.graph_builder import aml_graph
from src.data_engineering.lakehouse_sink import lakehouse_sink

router = APIRouter(prefix="/api/pipeline", tags=["Data Engineering Pipeline"])


@router.get("/graph/stats")
def get_graph_stats() -> Dict[str, Any]:
    """Retrieve Knowledge Graph topology statistics."""
    g = aml_graph.graph
    node_types = {}
    for _, data in g.nodes(data=True):
        ntype = data.get("node_type", "Unknown")
        node_types[ntype] = node_types.get(ntype, 0) + 1

    return {
        "total_nodes": g.number_of_nodes(),
        "total_edges": g.number_of_edges(),
        "node_type_breakdown": node_types,
        "is_directed": g.is_directed(),
        "is_multigraph": g.is_multigraph(),
    }


@router.post("/tokenize")
def test_tokenization(payload: Dict[str, str]) -> Dict[str, Any]:
    """Test OpenStack PII Tokenization Gateway."""
    raw_name = payload.get("name", "JOHN DOE")
    raw_ssn = payload.get("ssn", "999-00-1111")
    raw_acct = payload.get("account_id", "ACCT-12345")

    tok_name = pii_tokenizer._generate_token("NAME", raw_name)
    tok_ssn = pii_tokenizer._generate_token("SSN", raw_ssn)
    tok_acct = pii_tokenizer._generate_token("ACCT", raw_acct)

    return {
        "original": {"name": raw_name, "ssn": raw_ssn, "account_id": raw_acct},
        "tokenized": {"name": tok_name, "ssn": tok_ssn, "account_id": tok_acct},
        "detokenized_name": pii_tokenizer.detokenize(tok_name),
    }


@router.get("/lakehouse/recent")
def get_lakehouse_recent(limit: int = 15) -> Dict[str, Any]:
    """Retrieve recent records persisted in analytical lakehouse."""
    records = lakehouse_sink.get_historical_records(limit=limit)
    return {"total_lakehouse_records": len(lakehouse_sink._raw_events), "recent_records": records}
