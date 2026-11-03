"""System Infrastructure and Latency Metrics."""

from typing import Dict, Any, List
import numpy as np


class SystemMetricsCalculator:
    """Calculates latency percentiles (p50, p95, p99), throughput TPS, and error rates."""

    @staticmethod
    def calculate_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
        """Compute p50, p95, p99, max and mean latency."""
        if not latencies_ms:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "max": 0.0}

        arr = np.array(latencies_ms, dtype=float)
        return {
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p95": round(float(np.percentile(arr, 95)), 2),
            "p99": round(float(np.percentile(arr, 99)), 2),
            "mean": round(float(np.mean(arr)), 2),
            "max": round(float(np.max(arr)), 2),
        }

    @classmethod
    def compute_all(
        cls,
        tier1_latencies: List[float],
        tier2_latencies: List[float],
        tier3_latencies_sec: List[float],
        current_tps: float = 12500.0,
        cloud_interconnect_saturation: float = 0.42,
    ) -> Dict[str, Any]:
        """Consolidate system engineering metrics."""
        t1_stats = cls.calculate_latency_percentiles(tier1_latencies)
        t2_stats = cls.calculate_latency_percentiles(tier2_latencies)
        t3_stats = cls.calculate_latency_percentiles([s * 1000.0 for s in tier3_latencies_sec])

        return {
            "tier1_latency_ms": t1_stats,
            "tier1_sla_met": t1_stats["p99"] < 20.0,
            "tier2_latency_ms": t2_stats,
            "tier2_sla_met": t2_stats["p99"] < 100.0,
            "tier3_latency_ms": t3_stats,
            "throughput_tps": round(current_tps, 1),
            "throughput_target_met": current_tps >= 10000.0,
            "cloud_interconnect_saturation_pct": round(cloud_interconnect_saturation * 100.0, 1),
            "safe_degradation_active": False,
        }
