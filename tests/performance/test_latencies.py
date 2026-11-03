"""Performance and Latency SLA Benchmark tests."""

import time
import pytest
import numpy as np
from src.datascience.tier1_rules.engine import tier1_engine
from src.datascience.tier2_ml.model_blender import model_blender


def test_tier1_latency_sla(sample_transaction):
    """Benchmark Tier 1 Deterministic Rules: p50 < 5ms, p99 < 20ms."""
    latencies = []
    # 50 iterations
    for _ in range(50):
        t0 = time.perf_counter()
        res = tier1_engine.evaluate(sample_transaction)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    arr = np.array(latencies)
    p50 = float(np.percentile(arr, 50))
    p99 = float(np.percentile(arr, 99))

    print(f"\n[Tier 1 Benchmark] p50: {p50:.2f}ms, p99: {p99:.2f}ms")
    assert p50 < 10.0
    assert p99 < 20.0, f"Tier 1 p99 exceeded 20ms SLA: {p99:.2f}ms"


def test_tier2_latency_sla(sample_transaction):
    """Benchmark Tier 2 Ensemble ML: p50 < 40ms, p99 < 100ms."""
    latencies = []
    # 25 iterations
    for _ in range(25):
        t0 = time.perf_counter()
        res = model_blender.score_transaction(sample_transaction)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    arr = np.array(latencies)
    p50 = float(np.percentile(arr, 50))
    p99 = float(np.percentile(arr, 99))

    print(f"\n[Tier 2 Benchmark] p50: {p50:.2f}ms, p99: {p99:.2f}ms")
    assert p50 < 60.0
    assert p99 < 100.0, f"Tier 2 p99 exceeded 100ms SLA: {p99:.2f}ms"
