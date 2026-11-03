"""RAG Triad and Generative Grounding Metrics."""

from typing import Dict, Any, List
from src.core.models import ClaimEvidencePair, SuspiciousActivityReport


class RAGMetricsCalculator:
    """Calculates RAG Triad: Context Relevance, Groundedness (Faithfulness), and Answer Completeness."""

    @staticmethod
    def calculate_faithfulness(evaluations: List[ClaimEvidencePair]) -> float:
        """
        Faithfulness = Statements supported by retrieved context / Total statements
        Target: 100% (1.0)
        """
        if not evaluations:
            return 1.0
        grounded = sum(1 for e in evaluations if e.is_grounded)
        return round(grounded / len(evaluations), 4)

    @staticmethod
    def calculate_context_relevance(retrieved_docs: List[Dict[str, Any]]) -> float:
        """Percentage of retrieved documents with high relevance score to the target entity."""
        if not retrieved_docs:
            return 1.0
        relevant = sum(1 for d in retrieved_docs if d.get("relevance_score", 0.0) >= 0.70)
        return round(relevant / len(retrieved_docs), 4)

    @staticmethod
    def calculate_answer_completeness(sar: SuspiciousActivityReport) -> float:
        """
        Evaluates narrative coverage of mandatory regulatory 5Ws:
        Who (suspect/counterparty), What (amount/instrument), When (timestamp),
        Where (jurisdiction/country), Why (suspicious typology/rationale).
        """
        text = sar.narrative.lower()
        score = 0.0

        if sar.suspect_name:
            score += 0.20  # Who
        if str(sar.total_amount_flagged) in sar.narrative or "$" in sar.narrative:
            score += 0.20  # What
        if "2026" in sar.narrative or "date" in text or "on" in text:
            score += 0.20  # When
        if sar.suspect_address or "account" in text:
            score += 0.20  # Where
        if "typology" in text or "suspicious" in text or "inconsistent" in text:
            score += 0.20  # Why

        return round(score, 2)

    @classmethod
    def compute_all(
        cls,
        evaluations: List[ClaimEvidencePair],
        retrieved_docs: List[Dict[str, Any]],
        sar: SuspiciousActivityReport,
    ) -> Dict[str, Any]:
        """Consolidate RAG Triad scores."""
        faithfulness = cls.calculate_faithfulness(evaluations)
        relevance = cls.calculate_context_relevance(retrieved_docs)
        completeness = cls.calculate_answer_completeness(sar)
        rag_triad_mean = round((faithfulness + relevance + completeness) / 3.0, 4)

        return {
            "faithfulness_score": faithfulness,
            "context_relevance_score": relevance,
            "answer_completeness_score": completeness,
            "rag_triad_index": rag_triad_mean,
            "hallucination_detected": faithfulness < 0.90,
        }
