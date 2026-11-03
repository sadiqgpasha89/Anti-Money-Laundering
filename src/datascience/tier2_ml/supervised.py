"""Supervised Gradient Boosting framework for AML typologies."""

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from src.core.models import Transaction
from src.data_engineering.feature_store import feature_store


class SupervisedScorer:
    """Supervised classifier trained on historically validated AML patterns."""

    def __init__(self):
        self.feature_names = [
            "amount",
            "v1h_v30d_ratio",
            "v24h_daily_ratio",
            "amount_zscore",
            "geo_entropy",
            "tenure_deviation",
            "failed_auth_count",
        ]
        self.model = GradientBoostingClassifier(
            n_estimators=50,
            learning_rate=0.1,
            max_depth=3,
            random_state=42,
        )
        self._is_fitted = False
        self._fit_baseline_synthetic()

    def _fit_baseline_synthetic(self):
        """Fit with synthetic seed distribution representing legitimate and laundering vectors."""
        np.random.seed(42)
        n_samples = 400

        # Normal samples (Class 0: ~95%)
        n_normal = 380
        x_normal = np.column_stack([
            np.random.exponential(scale=250, size=n_normal),       # amount
            np.random.uniform(0.01, 1.0, size=n_normal),            # v1h_v30d_ratio
            np.random.uniform(0.5, 6.0, size=n_normal),             # v24h_daily_ratio
            np.random.normal(0.0, 1.0, size=n_normal),              # amount_zscore
            np.random.uniform(0.0, 0.35, size=n_normal),            # geo_entropy
            np.random.uniform(0.1, 2.0, size=n_normal),             # tenure_deviation
            np.random.choice([0, 1], size=n_normal, p=[0.95, 0.05]),# failed_auth_count
        ])
        y_normal = np.zeros(n_normal)

        # Laundering samples (Class 1: ~5%)
        n_illicit = 20
        x_illicit = np.column_stack([
            np.random.uniform(9000, 250000, size=n_illicit),        # amount
            np.random.uniform(2.5, 30.0, size=n_illicit),           # v1h_v30d_ratio
            np.random.uniform(10.0, 80.0, size=n_illicit),          # v24h_daily_ratio
            np.random.uniform(2.5, 8.0, size=n_illicit),            # amount_zscore
            np.random.uniform(0.5, 1.0, size=n_illicit),            # geo_entropy
            np.random.uniform(5.0, 100.0, size=n_illicit),          # tenure_deviation
            np.random.choice([0, 2, 4, 6], size=n_illicit),         # failed_auth_count
        ])
        y_illicit = np.ones(n_illicit)

        x_train = np.vstack([x_normal, x_illicit])
        y_train = np.concatenate([y_normal, y_illicit])

        self.model.fit(x_train, y_train)
        self._is_fitted = True

    def predict_score(self, txn: Transaction) -> float:
        """Score suspiciousness probability using supervised ensemble."""
        vec = feature_store.get_feature_vector(txn).reshape(1, -1)
        prob = float(self.model.predict_proba(vec)[0][1])
        return min(1.0, max(0.0, prob))

    def get_feature_importances(self) -> dict:
        """Return global feature importances."""
        importances = self.model.feature_importances_
        return {name: round(float(imp), 4) for name, imp in zip(self.feature_names, importances)}


supervised_scorer = SupervisedScorer()
