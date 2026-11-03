"""LLM & Multi-Agent Evaluation Harness (RAG Triad & Agentic Metrics)."""

from typing import Dict, Any, List
from src.core.models import SuspiciousActivityReport, ClaimEvidencePair
from src.agents.state import InvestigationDossier


class LLMEvalHarness:
    """Evaluates Faithfulness, Context Relevance, Tool Precision/Recall, and Token Efficiency."""

    def evaluate_faithfulness(self, evaluations: List[ClaimEvidencePair]) -> float:
        """Calculate groundedness / faithfulness score from ClaimEvidencePairs."""
        if not evaluations:
            return 1.0
        grounded = sum(1 for e in evaluations if e.is_grounded)
        return round(grounded / len(evaluations), 4)

    def evaluate_tool_metrics(
        self,
        actual_tools_called: List[str],
        expected_tools: List[str],
    ) -> Dict[str, float]:
        """Calculate precision and recall for tool selection."""
        actual_set = set(actual_tools_called)
        expected_set = set(expected_tools)

        true_pos = len(actual_set.intersection(expected_set))
        precision = true_pos / max(len(actual_set), 1)
        recall = true_pos / max(len(expected_set), 1)
        f1 = (2 * precision * recall) / max(precision + recall, 1e-5)

        return {
            "tool_precision": round(precision, 4),
            "tool_recall": round(recall, 4),
            "tool_f1": round(f1, 4),
        }

    def evaluate_dossier_performance(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Comprehensive evaluation of a completed investigation dossier."""
        faithfulness = self.evaluate_faithfulness(dossier.grounding_evaluations)
        plan_completed = dossier.execution_dag.is_completed if dossier.execution_dag else True

        # Token efficiency ratio: tokens consumed per tool call
        token_efficiency = (
            dossier.total_tokens_consumed / max(dossier.total_tool_calls, 1)
        )

        return {
            "dossier_id": dossier.dossier_id,
            "faithfulness_score": faithfulness,
            "plan_completed": plan_completed,
            "total_tokens_consumed": dossier.total_tokens_consumed,
            "total_tool_calls": dossier.total_tool_calls,
            "token_efficiency_ratio": round(token_efficiency, 2),
            "critic_approved": dossier.critic_approved,
        }


eval_harness = LLMEvalHarness()
