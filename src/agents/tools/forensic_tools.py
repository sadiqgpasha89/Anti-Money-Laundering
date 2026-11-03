"""Transaction Forensics and Fund-Flow Velocity Tools."""

from typing import Dict, Any, List
from src.core.models import Transaction
from src.data_engineering.feature_store import feature_store
from src.data_engineering.graph_builder import aml_graph


class ForensicTools:
    """Agent toolset for analyzing fund-flow sequencing and peeling mechanics."""

    @staticmethod
    def analyze_pass_through_velocity(txn: Transaction) -> Dict[str, Any]:
        """
        Evaluate immediate pass-through behavior:
        Checks if funds dwell less than 120-180 seconds and balance throughput ratio is ~1.0.
        """
        feats = feature_store.get_online_features(txn)
        metadata = txn.metadata or {}

        dwell_time = float(metadata.get("dwell_time_seconds", 300.0))
        throughput_ratio = float(metadata.get("throughput_ratio", 0.5))

        is_rapid_dwell = dwell_time < 120.0
        is_pass_through = throughput_ratio > 0.90

        # Circular flow check
        cycles = aml_graph.detect_circular_flows(txn.sender.account_id, max_depth=4)

        return {
            "transaction_id": txn.transaction_id,
            "amount": txn.amount,
            "dwell_time_seconds": dwell_time,
            "balance_throughput_ratio": throughput_ratio,
            "is_rapid_dwell": is_rapid_dwell,
            "is_pass_through": is_pass_through,
            "circular_cycles_count": len(cycles),
            "cycles": cycles,
            "velocity_ratio_1h": feats.get("v1h_v30d_ratio", 0.0),
            "amount_zscore": feats.get("amount_zscore", 0.0),
            "is_layering_peeling_chain": is_rapid_dwell and is_pass_through,
        }

    @staticmethod
    def analyze_smurfing_structuring(txn: Transaction) -> Dict[str, Any]:
        """
        Check for sub-threshold structured deposits (e.g. $9,000 - $9,999)
        and cross-branch multi-deposit coordination.
        """
        is_sub_ctr = 9000.0 <= txn.amount < 10000.0
        related_txns = txn.metadata.get("related_txns", [])

        return {
            "transaction_id": txn.transaction_id,
            "amount": txn.amount,
            "is_sub_threshold_ctr": is_sub_ctr,
            "deposit_channel": txn.channel.value,
            "coordinated_related_txns": related_txns,
            "smurfing_confidence": 0.92 if (is_sub_ctr or len(related_txns) > 0) else 0.10,
        }


forensic_tools = ForensicTools()
