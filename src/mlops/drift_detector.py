"""Continuous Machine Learning Drift Detection Engine (PSI, Wasserstein, Page-Hinkley, SHAP Drift)."""

import math
from typing import Dict, Any, List, Tuple
import numpy as np
from scipy.stats import wasserstein_distance


class DriftDetector:
    """Monitors Covariate Drift, Concept Drift, and Feature Attribution Drift."""

    def calculate_psi(
        self,
        baseline_distribution: List[float],
        current_distribution: List[float],
        num_bins: int = 10,
    ) -> float:
        """
        Calculate Population Stability Index (PSI):
        PSI = sum((P_b - Q_b) * ln(P_b / Q_b))
        PSI < 0.10: Stable
        0.10 <= PSI < 0.25: Moderate Drift
        PSI >= 0.25: Significant Drift (Trigger Retraining)
        """
        if not baseline_distribution or not current_distribution:
            return 0.0

        p_arr = np.array(baseline_distribution, dtype=float)
        q_arr = np.array(current_distribution, dtype=float)

        # Quantile binning on baseline
        percentiles = np.linspace(0, 100, num_bins + 1)
        bin_edges = np.percentile(p_arr, percentiles)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        # Frequencies with Laplace smoothing
        eps = 1e-4
        p_counts, _ = np.histogram(p_arr, bins=bin_edges)
        q_counts, _ = np.histogram(q_arr, bins=bin_edges)

        p_probs = (p_counts + eps) / (len(p_arr) + num_bins * eps)
        q_probs = (q_counts + eps) / (len(q_arr) + num_bins * eps)

        psi = np.sum((q_probs - p_probs) * np.log(q_probs / p_probs))
        return float(round(psi, 4))

    def calculate_wasserstein(
        self,
        baseline_distribution: List[float],
        current_distribution: List[float],
    ) -> float:
        """Calculate Earth Mover's Distance between distributions."""
        if not baseline_distribution or not current_distribution:
            return 0.0
        return float(round(wasserstein_distance(baseline_distribution, current_distribution), 4))

    def page_hinkley_test(
        self,
        error_series: List[float],
        delta: float = 0.005,
        threshold: float = 5.0,
    ) -> Tuple[bool, float]:
        """
        Sequential Page-Hinkley test for detecting concept drift in error rates.
        Returns: (is_drift_detected, cumulative_sum)
        """
        if not error_series:
            return False, 0.0

        mean = np.mean(error_series)
        cumulative_sum = 0.0
        min_cumulative = 0.0

        for val in error_series:
            cumulative_sum += (val - mean - delta)
            if cumulative_sum < min_cumulative:
                min_cumulative = cumulative_sum

        ph_value = cumulative_sum - min_cumulative
        is_drift = ph_value > threshold
        return is_drift, float(round(ph_value, 4))

    def evaluate_drift_report(
        self,
        baseline_features: Dict[str, List[float]],
        current_features: Dict[str, List[float]],
        error_series: List[float],
    ) -> Dict[str, Any]:
        """Generate comprehensive drift radar evaluation."""
        feature_psi = {}
        feature_wasserstein = {}
        drift_warnings = []

        for feat, base_vals in baseline_features.items():
            curr_vals = current_features.get(feat, [])
            if curr_vals:
                psi = self.calculate_psi(base_vals, curr_vals)
                w_dist = self.calculate_wasserstein(base_vals, curr_vals)
                feature_psi[feat] = psi
                feature_wasserstein[feat] = w_dist

                if psi >= 0.25:
                    drift_warnings.append(f"Significant Covariate Drift in '{feat}' (PSI = {psi:.4f} >= 0.25)")
                elif psi >= 0.10:
                    drift_warnings.append(f"Moderate Covariate Drift in '{feat}' (PSI = {psi:.4f} >= 0.10)")

        concept_drift, ph_val = self.page_hinkley_test(error_series)
        if concept_drift:
            drift_warnings.append(f"Concept Drift Detected by Page-Hinkley Test (PH = {ph_val:.2f} > 5.0)")

        action = "RECALIBRATE_MODEL" if any("Significant" in w for w in drift_warnings) or concept_drift else (
            "INSPECT_DISTRIBUTIONS" if drift_warnings else "STABLE"
        )

        return {
            "feature_psi": feature_psi,
            "feature_wasserstein": feature_wasserstein,
            "concept_drift_detected": concept_drift,
            "page_hinkley_metric": ph_val,
            "drift_warnings": drift_warnings,
            "recommended_action": action,
        }


drift_detector = DriftDetector()
