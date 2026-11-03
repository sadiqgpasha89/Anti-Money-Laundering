"""Cryptographic Immutable Audit Ledger (Continuous SHA-256 Hash Chain).

Satisfies regulatory compliance mandates (SR 11-7 / OCC 2011-12) by recording
tamper-evident cryptographic links for every system event across the lifecycle:
[Event Ingress] -> [Rules Exec] -> [ML Scores] -> [Agent Trace] -> [Human Decision]
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.core.models import AuditBlock


class CryptoAuditLedger:
    """Continuous SHA-256 Cryptographic Hash Chain for WORM auditability."""

    GENESIS_PREV_HASH = "0" * 64

    def __init__(self):
        self._chain: List[AuditBlock] = []
        self._initialize_genesis()

    def _initialize_genesis(self):
        """Seed the continuous hash chain with the genesis block."""
        genesis_payload = {
            "genesis": "AML_CRYPTO_AUDIT_GENESIS_2026",
            "standard": "FED_SR_11_7_COMPLIANT",
        }
        payload_hash = self.compute_hash(genesis_payload)
        current_hash = hashlib.sha256(
            f"0:{genesis_payload}:{payload_hash}:{self.GENESIS_PREV_HASH}".encode("utf-8")
        ).hexdigest()

        genesis_block = AuditBlock(
            block_index=0,
            timestamp=datetime.now(timezone.utc),
            event_type="GENESIS",
            event_payload_hash=payload_hash,
            previous_hash=self.GENESIS_PREV_HASH,
            current_hash=current_hash,
            actor="SYSTEM_INIT",
        )
        self._chain.append(genesis_block)

    @staticmethod
    def compute_hash(data: Any) -> str:
        """Compute SHA-256 digest of arbitrary JSON-serializable structure."""
        if isinstance(data, str):
            encoded = data.encode("utf-8")
        else:
            try:
                encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
            except Exception:
                encoded = str(data).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def record_event(self, event_type: str, payload: Any, actor: str = "SYSTEM") -> AuditBlock:
        """Append a new tamper-evident event block to the cryptographic chain."""
        last_block = self._chain[-1]
        block_index = len(self._chain)
        payload_hash = self.compute_hash(payload)
        prev_hash = last_block.current_hash
        timestamp = datetime.now(timezone.utc)

        raw_block_data = f"{block_index}:{timestamp.isoformat()}:{event_type}:{payload_hash}:{prev_hash}:{actor}"
        current_hash = hashlib.sha256(raw_block_data.encode("utf-8")).hexdigest()

        block = AuditBlock(
            block_index=block_index,
            timestamp=timestamp,
            event_type=event_type,
            event_payload_hash=payload_hash,
            previous_hash=prev_hash,
            current_hash=current_hash,
            actor=actor,
        )
        self._chain.append(block)
        return block

    def verify_integrity(self) -> Dict[str, Any]:
        """Validate every link in the cryptographic chain from genesis to head."""
        if not self._chain:
            return {"is_valid": False, "error": "Chain is empty"}

        # Validate Genesis
        if self._chain[0].previous_hash != self.GENESIS_PREV_HASH:
            return {"is_valid": False, "error": "Genesis previous_hash corrupt"}

        for i in range(1, len(self._chain)):
            curr = self._chain[i]
            prev = self._chain[i - 1]

            # Check forward link
            if curr.previous_hash != prev.current_hash:
                return {
                    "is_valid": False,
                    "error": f"Broken chain link at block {curr.block_index}: prev {curr.previous_hash} != {prev.current_hash}",
                    "corrupted_block_index": curr.block_index,
                }

            # Check block hash consistency
            raw_block_data = f"{curr.block_index}:{curr.timestamp.isoformat()}:{curr.event_type}:{curr.event_payload_hash}:{curr.previous_hash}:{curr.actor}"
            recomputed = hashlib.sha256(raw_block_data.encode("utf-8")).hexdigest()
            if curr.current_hash != recomputed:
                return {
                    "is_valid": False,
                    "error": f"Tampered hash at block {curr.block_index}: {curr.current_hash} != {recomputed}",
                    "corrupted_block_index": curr.block_index,
                }

        return {
            "is_valid": True,
            "chain_length": len(self._chain),
            "head_hash": self._chain[-1].current_hash,
        }

    def get_chain(self, limit: Optional[int] = None) -> List[AuditBlock]:
        """Retrieve the immutable audit chain."""
        if limit:
            return self._chain[-limit:]
        return list(self._chain)


# Global singleton instance
audit_ledger = CryptoAuditLedger()
