"""Heterogeneous Directed Multigraph Builder for AML Topology and Entity Resolution.

Nodes: Customer, Account, Device, LegalEntity, PhysicalAddress
Edges: Transacted, Owns, SharedDevice, AssociatedAddress
Enables:
- Peeling chain traversal & dwell time analysis
- Circular fund flow detection
- Shared device / synthetic identity ring clustering
- Recursive UBO ownership graph unrolling
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import networkx as nx
from src.core.models import Transaction


class AMLKnowledgeGraph:
    """Enterprise Heterogeneous Directed Multigraph."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_transaction(self, txn: Transaction):
        """Update graph topology upon transaction arrival."""
        sender_cust = txn.sender.customer_id
        sender_acct = txn.sender.account_id
        recv_cust = txn.receiver.customer_id
        recv_acct = txn.receiver.account_id

        # Add Customer and Account Nodes
        self.graph.add_node(sender_cust, node_type="Customer", name=txn.sender.name, country=txn.sender.country)
        self.graph.add_node(sender_acct, node_type="Account", country=txn.sender.country)
        self.graph.add_node(recv_cust, node_type="Customer", name=txn.receiver.name, country=txn.receiver.country)
        self.graph.add_node(recv_acct, node_type="Account", country=txn.receiver.country)

        # Ownership Edges
        self.graph.add_edge(sender_cust, sender_acct, edge_type="Owns", equity=100.0)
        self.graph.add_edge(recv_cust, recv_acct, edge_type="Owns", equity=100.0)

        # Transactional Edge
        self.graph.add_edge(
            sender_acct,
            recv_acct,
            key=txn.transaction_id,
            edge_type="Transacted",
            amount=txn.amount,
            currency=txn.currency,
            channel=txn.channel.value,
            timestamp=txn.timestamp.isoformat(),
            dwell_time_seconds=txn.metadata.get("dwell_time_seconds", 300),
        )

        # Device & Telemetry Nodes & Edges
        if txn.telemetry.device_id:
            dev_node = f"DEV_{txn.telemetry.device_id}"
            self.graph.add_node(dev_node, node_type="Device")
            self.graph.add_edge(sender_cust, dev_node, edge_type="SharedDevice", key=f"{sender_cust}_{dev_node}")

        # Physical Address / Geohash Nodes & Edges
        if txn.telemetry.geo_hash:
            geo_node = f"GEO_{txn.telemetry.geo_hash}"
            self.graph.add_node(geo_node, node_type="PhysicalAddress")
            self.graph.add_edge(sender_cust, geo_node, edge_type="AssociatedAddress", key=f"{sender_cust}_{geo_node}")

    def add_corporate_ownership(self, parent_id: str, subsidiary_id: str, equity_percent: float):
        """Add corporate parent-subsidiary ownership edge."""
        self.graph.add_node(parent_id, node_type="LegalEntity")
        self.graph.add_node(subsidiary_id, node_type="LegalEntity")
        self.graph.add_edge(parent_id, subsidiary_id, edge_type="Owns", equity=equity_percent)

    def find_shared_devices(self, customer_id: str) -> List[Dict[str, Any]]:
        """Identify other entities authenticating from the exact same device ID."""
        if customer_id not in self.graph:
            return []

        shared_entities = []
        # Find device neighbors
        for neighbor in self.graph.neighbors(customer_id):
            if self.graph.nodes[neighbor].get("node_type") == "Device":
                # Find other customers connected to this device
                for other in self.graph.predecessors(neighbor):
                    if other != customer_id and self.graph.nodes[other].get("node_type") == "Customer":
                        shared_entities.append({
                            "device_id": neighbor,
                            "associated_customer": other,
                            "customer_name": self.graph.nodes[other].get("name", "Unknown"),
                        })
        return shared_entities

    def detect_circular_flows(self, start_account: str, max_depth: int = 4) -> List[List[str]]:
        """Detect cyclic fund routing loops returning to origin accounts."""
        if start_account not in self.graph:
            return []

        cycles = []
        try:
            # Look for simple cycles involving start_account
            for cycle in nx.simple_cycles(self.graph):
                if start_account in cycle and len(cycle) <= max_depth + 1:
                    cycles.append(cycle)
        except Exception:
            pass
        return cycles

    def trace_peeling_chain(self, start_account: str, max_hops: int = 5) -> List[Dict[str, Any]]:
        """Trace high-velocity multi-hop sequential fund dispersals."""
        if start_account not in self.graph:
            return []

        path = []
        curr = start_account
        visited = {curr}

        for hop in range(max_hops):
            successors = list(self.graph.successors(curr))
            tx_edges = []
            for s in successors:
                if s in visited:
                    continue
                edges = self.graph.get_edge_data(curr, s)
                if edges:
                    for k, data in edges.items():
                        if data.get("edge_type") == "Transacted":
                            tx_edges.append((s, data))

            if not tx_edges:
                break

            # Pick primary flow (highest amount / lowest dwell time)
            next_node, edge_data = max(tx_edges, key=lambda x: x[1].get("amount", 0))
            path.append({
                "hop": hop + 1,
                "from_account": curr,
                "to_account": next_node,
                "amount": edge_data.get("amount", 0),
                "dwell_time_seconds": edge_data.get("dwell_time_seconds", 300),
            })
            visited.add(next_node)
            curr = next_node

        return path

    def get_subgraph_metrics(self, node_id: str) -> Dict[str, float]:
        """Compute topological metrics for GNN feature conditioning."""
        if node_id not in self.graph:
            return {
                "in_degree": 0.0,
                "out_degree": 0.0,
                "clustering_coefficient": 0.0,
                "pagerank": 0.0,
            }

        # Convert to simple DiGraph for topological metrics
        simple_g = nx.DiGraph(self.graph)
        in_deg = float(self.graph.in_degree(node_id))
        out_deg = float(self.graph.out_degree(node_id))

        try:
            clustering = float(nx.clustering(simple_g.to_undirected(), node_id))
        except Exception:
            clustering = 0.0

        try:
            pr_dict = nx.pagerank(simple_g, alpha=0.85)
            pr = float(pr_dict.get(node_id, 0.0))
        except Exception:
            pr = 0.0

        return {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "clustering_coefficient": clustering,
            "pagerank": pr,
        }


# Global singleton graph
aml_graph = AMLKnowledgeGraph()
