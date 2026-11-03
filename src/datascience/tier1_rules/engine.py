"""Tier 1 Deterministic Rules Engine.

Executes low-latency heuristic boundary checks and statutory sanctions screens within memory.
SLA: p50 < 5ms, p99 < 20ms.
"""

import time
from typing import List
from src.core.config import settings
from src.core.models import Transaction, Tier1Result, DecisionStatus, RuleHit
from src.core.crypto_audit import audit_ledger
from src.datascience.tier1_rules.sanctions import sanctions_matcher
from src.datascience.tier1_rules.thresholds import StatutoryThresholdRules
from src.datascience.tier1_rules.velocity_rules import VelocityBoundaryRules


class Tier1RulesEngine:
    """RETE-style high-throughput deterministic rules executor."""

    def __init__(self):
        self._processed_txns = 0

    def evaluate(self, txn: Transaction) -> Tier1Result:
        """
        Evaluate transaction against deterministic rules matrix.
        Returns Tier1Result in <20ms.
        """
        t0 = time.perf_counter()
        self._processed_txns += 1
        rule_hits: List[RuleHit] = []

        # 1. Sanctions Screening (Sender & Receiver)
        sender_hit = sanctions_matcher.check_hard_stop(txn.sender.name, txn.sender.country)
        if sender_hit:
            rule_hits.append(sender_hit)

        receiver_hit = sanctions_matcher.check_hard_stop(txn.receiver.name, txn.receiver.country)
        if receiver_hit:
            rule_hits.append(receiver_hit)

        # 2. Statutory Thresholds (CTR & Large Wire)
        ctr_hit = StatutoryThresholdRules.check_ctr_threshold(txn)
        if ctr_hit:
            rule_hits.append(ctr_hit)

        wire_hit = StatutoryThresholdRules.check_large_wire_threshold(txn)
        if wire_hit:
            rule_hits.append(wire_hit)

        # 3. Velocity & FATF Jurisdiction Gatekeepers
        vel_hit = VelocityBoundaryRules.check_failed_authorizations(txn)
        if vel_hit:
            rule_hits.append(vel_hit)

        fatf_hit = VelocityBoundaryRules.check_fatf_call_for_action(txn)
        if fatf_hit:
            rule_hits.append(fatf_hit)

        # Determine overall status
        is_hard_stop = any(hit.is_hard_stop for hit in rule_hits)
        status = DecisionStatus.HOLD if is_hard_stop else DecisionStatus.PASSED

        latency_ms = (time.perf_counter() - t0) * 1000.0

        result = Tier1Result(
            transaction_id=txn.transaction_id,
            is_blocked=is_hard_stop,
            status=status,
            latency_ms=round(latency_ms, 3),
            rule_hits=rule_hits,
        )

        # Cryptographic Audit Record: Rules Execution
        audit_ledger.record_event(
            event_type="RULES_EXEC",
            payload={
                "transaction_id": txn.transaction_id,
                "is_blocked": is_hard_stop,
                "status": status.value,
                "rule_hits_count": len(rule_hits),
                "latency_ms": result.latency_ms,
            },
            actor="TIER1_RULES_ENGINE",
        )

        return result


tier1_engine = Tier1RulesEngine()
