"""Multi-Agent System & Cognitive Efficiency Metrics."""

from typing import Dict, Any, List


class AgenticMetricsCalculator:
    """Calculates agent performance, reasoning efficiency, plan completion, and critic rejection."""

    @staticmethod
    def calculate_plan_completion_rate(completed_dags: int, total_dags: int) -> float:
        """Percentage of task DAGs executed without unhandled errors."""
        if total_dags <= 0:
            return 1.0
        return round(completed_dags / total_dags, 4)

    @staticmethod
    def calculate_critic_rejection_rate(rejected_drafts: int, total_drafts: int) -> float:
        """Critic Rejection Rate = Drafts Rejected by Critic / Total Drafts Generated."""
        if total_drafts <= 0:
            return 0.0
        return round(rejected_drafts / total_drafts, 4)

    @staticmethod
    def calculate_autonomous_clearance_accuracy(
        true_benign_cleared: int,
        total_auto_cleared: int,
    ) -> float:
        """Accuracy of agent autonomous clearance decisions vs human auditor validation."""
        if total_auto_cleared <= 0:
            return 1.0
        return round(true_benign_cleared / total_auto_cleared, 4)

    @classmethod
    def compute_all(
        cls,
        total_dags: int,
        completed_dags: int,
        total_drafts: int,
        rejected_drafts: int,
        total_tokens: int,
        total_tool_calls: int,
        auto_cleared: int,
        valid_cleared: int,
    ) -> Dict[str, Any]:
        """Consolidate agentic scorecard."""
        plan_rate = cls.calculate_plan_completion_rate(completed_dags, total_dags)
        critic_rate = cls.calculate_critic_rejection_rate(rejected_drafts, total_drafts)
        clearance_acc = cls.calculate_autonomous_clearance_accuracy(valid_cleared, auto_cleared)
        tokens_per_call = round(total_tokens / max(total_tool_calls, 1), 2)
        tools_per_investigation = round(total_tool_calls / max(total_dags, 1), 2)

        return {
            "plan_completion_rate": plan_rate,
            "critic_rejection_rate": critic_rate,
            "autonomous_clearance_accuracy": clearance_acc,
            "avg_tools_per_investigation": tools_per_investigation,
            "token_efficiency_ratio": tokens_per_call,
            "total_tokens_consumed": total_tokens,
            "total_tool_calls": total_tool_calls,
        }
