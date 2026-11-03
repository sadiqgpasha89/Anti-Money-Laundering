"""Transaction Forensics Micro-Agent."""

from typing import Dict, Any
from src.core.models import Alert
from src.agents.tools.forensic_tools import forensic_tools


class TransactionForensicsAgent:
    """Investigates fund-flow velocities, peeling chains, dwell times, and smurfing structures."""

    def __init__(self):
        self.name = "TransactionForensicsAgent"

    def investigate(self, alert: Alert) -> Dict[str, Any]:
        """Analyze temporal velocity, pass-through ratio, and smurfing patterns."""
        txn = alert.transaction

        pass_through_data = forensic_tools.analyze_pass_through_velocity(txn)
        smurfing_data = forensic_tools.analyze_smurfing_structuring(txn)

        is_peeling = pass_through_data.get("is_layering_peeling_chain", False)
        is_smurfing = smurfing_data.get("is_sub_threshold_ctr", False)
        has_cycles = pass_through_data.get("circular_cycles_count", 0) > 0

        summary = (
            f"Forensics Analysis for TXN {txn.transaction_id} (${txn.amount:,.2f}): "
            f"Peeling Chain / Pass-Through Flag: {is_peeling} (Dwell: {pass_through_data['dwell_time_seconds']}s, "
            f"Throughput Ratio: {pass_through_data['balance_throughput_ratio']}). "
            f"Structuring/Smurfing Sub-CTR: {is_smurfing}. "
            f"Circular Loops: {has_cycles} ({pass_through_data.get('circular_cycles_count', 0)} cycles detected)."
        )

        return {
            "agent": self.name,
            "transaction_id": txn.transaction_id,
            "pass_through_analysis": pass_through_data,
            "smurfing_analysis": smurfing_data,
            "is_peeling_chain": is_peeling,
            "is_smurfing_structure": is_smurfing,
            "has_circular_loops": has_cycles,
            "summary": summary,
        }


transaction_forensics_agent = TransactionForensicsAgent()
