"""Unit tests for Dual Online/Offline Feature Store."""

import pytest
from src.data_engineering.feature_store import FeatureStore


def test_feature_store_hydration_and_ratios(sample_transaction):
    """Test feature store rolling aggregates and velocity ratios."""
    fs = FeatureStore()
    fs.record_transaction(sample_transaction)

    feats = fs.get_online_features(sample_transaction)
    assert feats["amount"] == 150.0
    assert feats["vol_1h"] >= 150.0
    assert feats["count_1h"] >= 1
    assert "v1h_v30d_ratio" in feats
    assert "geo_entropy" in feats
    assert "amount_zscore" in feats

    vec = fs.get_feature_vector(sample_transaction)
    assert len(vec) == 7


def test_current_transaction_is_not_counted_twice(sample_transaction):
    """The pipeline records a transaction before Tier 2 scores it; the features must still count it once."""
    fs = FeatureStore()
    before = fs.get_online_features(sample_transaction)
    fs.record_transaction(sample_transaction)
    after = fs.get_online_features(sample_transaction)

    assert after["count_1h"] == before["count_1h"] == 1
    assert after["vol_24h"] == before["vol_24h"] == sample_transaction.amount
    assert after["v24h_daily_ratio"] == before["v24h_daily_ratio"]
