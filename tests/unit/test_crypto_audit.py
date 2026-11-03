"""Unit tests for Continuous SHA-256 Cryptographic Audit Ledger."""

import pytest
from src.core.crypto_audit import CryptoAuditLedger


def test_crypto_audit_chain_initialization_and_verification():
    """Verify genesis block and forward link integrity."""
    ledger = CryptoAuditLedger()
    res = ledger.verify_integrity()
    assert res["is_valid"] is True
    assert res["chain_length"] == 1


def test_crypto_audit_event_recording():
    """Test recording events and checking sequential hash chain."""
    ledger = CryptoAuditLedger()

    b1 = ledger.record_event("EVENT_INGRESS", {"txn_id": "TXN-01", "amt": 1000}, actor="INGESTION")
    assert b1.block_index == 1
    assert b1.previous_hash == ledger._chain[0].current_hash

    b2 = ledger.record_event("RULES_EXEC", {"txn_id": "TXN-01", "status": "PASSED"}, actor="TIER1")
    assert b2.block_index == 2
    assert b2.previous_hash == b1.current_hash

    res = ledger.verify_integrity()
    assert res["is_valid"] is True
    assert res["chain_length"] == 3


def test_crypto_audit_tamper_detection():
    """Test that modifying any block content or hash is immediately detected."""
    ledger = CryptoAuditLedger()
    ledger.record_event("EVENT_1", {"data": "authentic"}, actor="ACTOR_1")
    ledger.record_event("EVENT_2", {"data": "authentic"}, actor="ACTOR_2")

    assert ledger.verify_integrity()["is_valid"] is True

    # Intentionally tamper with block 1 payload hash
    ledger._chain[1].event_payload_hash = "corrupted_tampered_hash_0000000000000000"

    tamper_check = ledger.verify_integrity()
    assert tamper_check["is_valid"] is False
    assert "Tampered hash" in tamper_check["error"]
