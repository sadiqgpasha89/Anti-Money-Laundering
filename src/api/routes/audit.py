"""Regulatory Audit and Cryptographic Hash Chain routes (Section 11)."""

from typing import Dict, Any, List
from fastapi import APIRouter
from src.core.crypto_audit import audit_ledger

router = APIRouter(prefix="/api/audit", tags=["Cryptographic Audit"])


@router.get("/chain")
def get_audit_chain(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve immutable continuous SHA-256 cryptographic audit ledger."""
    chain = audit_ledger.get_chain(limit=limit)
    return [b.model_dump() for b in chain]


@router.get("/verify")
def verify_audit_integrity() -> Dict[str, Any]:
    """Cryptographically verify all block links and hashes in the audit chain."""
    return audit_ledger.verify_integrity()
