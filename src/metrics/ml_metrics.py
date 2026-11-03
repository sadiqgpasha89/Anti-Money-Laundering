"""Machine Learning Statistical and Evaluation Metrics."""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import precision_recall_curve, auc, brier_score_loss


class MLMetricsCalculator:
    """Calculates PR-AUC, Precision@Top-K, Expected Calibration Error (ECE), and Brier Score."""

    @staticmethod
    def calculate_pr_auc(y_true: List[int], y_scores: List[float]) -> float:
        """Calculate Area Under the Precision-Recall Curve (PR-AUC)."""
        if len(set(y_true)) < 2:
            return 1.0 if y_true and y_true[0] == 1 else 0.0
        precision, recall, _ = precision_recall_curve(y_true, y_scores)
        return float(round(auc(recall, precision), 4))

    @staticmethod
    def calculate_precision_at_k(y_true: List[int], y_scores: List[float], k: int = 10) -> float:
        """
        Precision@Top-K:
        Precision@K = 1/K * sum(I(y_i = 1)) for top K scored samples.
        """
        if not y_true or k <= 0:
            return 0.0
        paired = sorted(zip(y_scores, y_true), key=lambda x: x[0], reverse=True)
        top_k = paired[:k]
        hits = sum(y for _, y in top_k)
        return float(round(hits / len(top_k), 4))

    @staticmethod
    def calculate_ece(
        y_true: List[int],
        y_probs: List[float],
        num_bins: int = 10,
    ) -> float:
        """
        Expected Calibration Error (ECE):
        ECE = sum(|B_m|/N * |acc(B_m) - conf(B_m)|)
        """
        if not y_true:
            return 0.0

        probs = np.array(y_probs)
        labels = np.array(y_true)
        bin_edges = np.linspace(0, 1, num_bins + 1)
        ece = 0.0
        n = len(labels)

        for i in range(num_bins):
            mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
            if np.any(mask):
                bin_acc = np.mean(labels[mask])
                bin_conf = np.mean(probs[mask])
                bin_size = np.sum(mask)
                ece += (bin_size / n) * abs(bin_acc - bin_conf)

        return float(round(ece, 4))

    @staticmethod
    def calculate_brier_score(y_true: List[int], y_probs: List[float]) -> float:
        """Calculate Mean Squared Error of probability assessments (Brier score)."""
        if not y_true:
            return 0.0
        return float(round(brier_score_loss(y_true, y_probs), 4))

    @classmethod
    def compute_all(
        cls,
        y_true: List[int],
        y_probs: List[float],
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """Consolidate ML statistical metrics."""
        pr_auc = cls.calculate_pr_auc(y_true, y_probs)
        prec_k = cls.calculate_precision_at_k(y_true, y_probs, k=top_k)
        ece = cls.calculate_ece(y_true, y_probs)
        brier = cls.calculate_brier_score(y_true, y_probs)

        return {
            "pr_auc": pr_auc,
            "precision_at_k": prec_k,
            "expected_calibration_error": ece,
            "brier_score": brier,
            "evaluated_samples": len(y_true),
        }
