"""Entity Resolution and KYC Micro-Agent."""

from typing import Dict, Any
from src.core.models import Transaction, Alert
from src.agents.tools.entity_tools import entity_tools
from src.agents.tools.graph_tools import graph_tools


class EntityResolutionAgent:
    """Investigates synthetic identity rings, shared device infrastructure, and UBO structures."""

    def __init__(self):
        self.name = "EntityResolutionAgent"

    def investigate(self, alert: Alert) -> Dict[str, Any]:
        """Execute deep identity resolution and corporate registry traversal."""
        txn = alert.transaction
        sender_cust = txn.sender.customer_id
        sender_name = txn.sender.name

        # 1. Check shared digital footprints (IMEI, MAC, phone)
        shared_device_data = entity_tools.check_shared_device_cluster(sender_cust)

        # 2. Check Corporate UBO trees (if legal entity or offshore sender)
        ubo_data = entity_tools.unroll_ubo_tree(sender_name)

        # 3. Subgraph topology
        subgraph = graph_tools.get_account_subgraph(txn.sender.account_id)

        # Formulate findings
        is_synthetic = shared_device_data.get("is_synthetic_ring", False)
        is_fractional_ubo = any(
            c.get("is_fractional_concealment", False) for c in ubo_data.get("effective_controllers", [])
        )
        true_controllers = [
            c["individual_name"] for c in ubo_data.get("effective_controllers", [])
            if c.get("is_ubo_statutory") or c.get("is_fractional_concealment")
        ]

        summary = (
            f"Entity Resolution Analysis for {sender_name}: "
            f"Synthetic Ring Detected: {is_synthetic} ({shared_device_data.get('shared_identities_count', 0)} linked identities). "
            f"UBO Unrolled: {ubo_data.get('ubo_resolved', False)}. "
            f"Identified Controlling Parties: {', '.join(true_controllers) if true_controllers else 'None'}."
        )

        return {
            "agent": self.name,
            "sender_name": sender_name,
            "sender_id": sender_cust,
            "is_synthetic_ring": is_synthetic,
            "shared_device_details": shared_device_data,
            "is_fractional_ubo": is_fractional_ubo,
            "ubo_details": ubo_data,
            "true_controllers": true_controllers,
            "subgraph_metrics": subgraph.get("metrics", {}),
            "summary": summary,
        }


entity_resolution_agent = EntityResolutionAgent()
