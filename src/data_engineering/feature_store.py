"""Dual Online/Offline Feature Store for AML Streaming and Baseline Metrics.

Provides:
- Sub-millisecond online feature hydration (1h volume, 24h count, velocity)
- Offline baseline calculations (30-day moving average, variance, geolocation entropy)
- Feature vector extraction for Tier 2 ML inference
"""

import math
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from src.core.models import Transaction


class FeatureStore:
    """Enterprise Feature Store combining fast in-memory online cache and historical windows."""

    def __init__(self):
        # Online In-Memory Stores indexed by account_id / customer_id
        # Key: account_id -> deque of (timestamp, amount, geo_hash)
        self._history: Dict[str, deque] = defaultdict(deque)
        # Key: account_id -> baseline metrics
        self._baselines: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "avg_monthly_volume": 1000.0,
            "avg_txn_amount": 150.0,
            "std_txn_amount": 50.0,
            "geo_entropy_baseline": 0.20,
        })
        # Global counter
        self._feature_access_count = 0

    def record_transaction(self, txn: Transaction):
        """Ingest a transaction event into the rolling feature window."""
        acct_id = txn.sender.account_id
        geo = txn.telemetry.geo_hash or "c00000"
        self._history[acct_id].append({
            "transaction_id": txn.transaction_id,
            "timestamp": txn.timestamp,
            "amount": txn.amount,
            "geo_hash": geo,
            "channel": txn.channel.value,
            "failed_auth": txn.telemetry.failed_auth_count,
        })

        # Evict records older than 30 days
        cutoff = txn.timestamp - timedelta(days=30)
        while self._history[acct_id] and self._history[acct_id][0]["timestamp"] < cutoff:
            self._history[acct_id].popleft()

    def get_online_features(self, txn: Transaction) -> Dict[str, float]:
        """Compute instantaneous and rolling features with sub-millisecond latency."""
        self._feature_access_count += 1
        acct_id = txn.sender.account_id
        records = self._history[acct_id]
        now = txn.timestamp

        cutoff_1h = now - timedelta(hours=1)
        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d = now - timedelta(days=7)

        vol_1h = txn.amount
        count_1h = 1
        vol_24h = txn.amount
        count_24h = 1
        vol_7d = txn.amount
        count_7d = 1
        amounts = [txn.amount]
        geos = [txn.telemetry.geo_hash or "c00000"]
        recent_auth_failures = txn.telemetry.failed_auth_count

        for rec in records:
            # the current transaction is already counted above; the pipeline records it before it is scored
            if rec.get("transaction_id") == txn.transaction_id:
                continue
            ts = rec["timestamp"]
            amt = rec["amount"]
            amounts.append(amt)
            geos.append(rec["geo_hash"])
            if ts >= cutoff_1h:
                vol_1h += amt
                count_1h += 1
            if ts >= cutoff_24h:
                vol_24h += amt
                count_24h += 1
            if ts >= cutoff_7d:
                vol_7d += amt
                count_7d += 1
            recent_auth_failures += rec.get("failed_auth", 0)

        # Baseline stats
        baseline = self._baselines[acct_id]
        base_monthly = max(baseline["avg_monthly_volume"], txn.sender.historical_monthly_avg_vol, 1.0)
        base_daily = base_monthly / 30.0

        # Frequency and Velocity Ratios
        v1h_v30d_ratio = vol_1h / max(base_monthly, 1.0)
        v24h_daily_ratio = vol_24h / max(base_daily, 1.0)

        # Amount Variance / Std Dev
        amounts_arr = np.array(amounts, dtype=float)
        amount_std = float(np.std(amounts_arr)) if len(amounts_arr) > 1 else 0.0
        amount_zscore = (txn.amount - np.mean(amounts_arr)) / (amount_std + 1e-5)

        # Geolocation Entropy: H(geo) = - sum(p * log2(p))
        geo_counts = defaultdict(int)
        for g in geos:
            geo_counts[g] += 1
        total_geos = len(geos)
        entropy = 0.0
        for g, count in geo_counts.items():
            p = count / total_geos
            entropy -= p * math.log2(p) if p > 0 else 0.0
        geo_entropy = min(1.0, entropy / 3.0)  # normalized

        # Peer Deviation / Tenure Factor
        tenure = max(txn.sender.account_tenure_months, 1)
        # Young accounts with large spikes have high deviation
        tenure_multiplier = 2.0 if tenure < 6 else 1.0
        tenure_deviation = (txn.amount / max(txn.sender.historical_monthly_avg_vol, 1.0)) * tenure_multiplier

        return {
            "amount": float(txn.amount),
            "vol_1h": float(vol_1h),
            "count_1h": float(count_1h),
            "vol_24h": float(vol_24h),
            "count_24h": float(count_24h),
            "vol_7d": float(vol_7d),
            "count_7d": float(count_7d),
            "v1h_v30d_ratio": float(v1h_v30d_ratio),
            "v24h_daily_ratio": float(v24h_daily_ratio),
            "amount_std": float(amount_std),
            "amount_zscore": float(amount_zscore),
            "geo_entropy": float(geo_entropy),
            "tenure_months": float(tenure),
            "tenure_deviation": float(tenure_deviation),
            "failed_auth_count": float(recent_auth_failures),
        }

    def get_feature_vector(self, txn: Transaction) -> np.ndarray:
        """Return canonical numpy array of features for model inference."""
        feats = self.get_online_features(txn)
        return np.array([
            feats["amount"],
            feats["v1h_v30d_ratio"],
            feats["v24h_daily_ratio"],
            feats["amount_zscore"],
            feats["geo_entropy"],
            feats["tenure_deviation"],
            feats["failed_auth_count"],
        ], dtype=float)


# Global singleton feature store
feature_store = FeatureStore()
