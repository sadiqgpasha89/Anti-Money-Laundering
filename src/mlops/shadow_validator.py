"""Champion-Challenger Shadow Validator.

Evaluates differential score divergence:
Delta = |S_champion(x) - S_challenger(x)| > epsilon
Surfaces cases where the challenger catches novel patterns or introduces false positives.
"""

from typing import Dict, Any, List
from src.core.models import Transaction
from src.datascience.tier2_ml.supervised import supervised_scorer


class ShadowValidator:
    """Champion-Challenger differential evaluator."""

    def __init__(self, divergence_tolerance: float = 0.15):
        self.tolerance = divergence_tolerance
        self._evaluations: List[Dict[str, Any]] = []

    def evaluate_shadow(
        self,
        txn: Transaction,
        champion_score: float,
        challenger_score: float,
    ) -> Dict[str, Any]:
        """Compare predictions of Champion vs Challenger models on live transaction."""
        delta = abs(champion_score - challenger_score)
        is_divergent = delta > self.tolerance

        result = {
            "transaction_id": txn.transaction_id,
            "champion_score": round(champion_score, 4),
            "challenger_score": round(challenger_score, 4),
            "delta": round(delta, 4),
            "is_divergent": is_divergent,
            "challenger_more_suspicious": challenger_score > champion_score,
            "interpretation": (
                "Challenger surfaces novel illicit pattern" if challenger_score > champion_score + self.tolerance
                else ("Challenger suppresses potential false positive" if champion_score > challenger_score + self.tolerance else "Consistent")
            ),
        }
        self._evaluations.append(result)
        return result

    def get_divergence_rate(self) -> float:
        """Percentage of transactions with divergent champion-challenger scores."""
        if not self._evaluations:
            return 0.0
        div_count = sum(1 for e in self._evaluations if e["is_divergent"])
        return round(div_count / len(self._evaluations), 4)

    def get_recent_divergences(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent divergent evaluations for model validation review."""
        return [e for e in self._evaluations if e["is_divergent"]][-limit:]


shadow_validator = ShadowValidator()
