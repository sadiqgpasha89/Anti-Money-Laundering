"""Token and Cloud Compute Cost Tracker for GCP Vertex AI Burst Workloads."""

from typing import Dict, Any


class CostTracker:
    """Tracks token consumption and financial expenditure for agent invocations."""

    # Simulated Vertex AI pricing: $0.001 per 1k input tokens, $0.002 per 1k output tokens
    INPUT_COST_PER_1K = 0.0010
    OUTPUT_COST_PER_1K = 0.0020

    def __init__(self):
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_investigations = 0

    def record_usage(self, input_tokens: int, output_tokens: int):
        """Accumulate token usage for active investigation."""
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_investigations += 1

    def get_summary(self) -> Dict[str, Any]:
        """Compute accumulated costs."""
        input_cost = (self._total_input_tokens / 1000.0) * self.INPUT_COST_PER_1K
        output_cost = (self._total_output_tokens / 1000.0) * self.OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost

        cost_per_investigation = (
            total_cost / max(self._total_investigations, 1)
        )

        return {
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cost_usd": round(total_cost, 4),
            "cost_per_investigation_usd": round(cost_per_investigation, 4),
            "investigations_count": self._total_investigations,
        }


cost_tracker = CostTracker()
