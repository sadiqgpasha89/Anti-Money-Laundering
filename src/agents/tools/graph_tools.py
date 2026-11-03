"""Graph traversal and topological analysis tools for agents."""

from typing import Dict, Any, List
from src.data_engineering.graph_builder import aml_graph


class GraphTools:
    """Agent toolset for navigating the heterogeneous knowledge graph."""

    @staticmethod
    def get_account_subgraph(account_id: str) -> Dict[str, Any]:
        """Extract multi-hop neighborhood around an account."""
        metrics = aml_graph.get_subgraph_metrics(account_id)
        cycles = aml_graph.detect_circular_flows(account_id, max_depth=4)
        peeling = aml_graph.trace_peeling_chain(account_id, max_hops=4)

        return {
            "account_id": account_id,
            "metrics": metrics,
            "has_cycles": len(cycles) > 0,
            "cycles_detected": cycles,
            "peeling_chain_hops": len(peeling),
            "peeling_chain_path": peeling,
        }


graph_tools = GraphTools()
