"""Unsupervised Autoencoder / Outlier Detector for Zero-Day Laundering Typologies.

Computes anomaly score via normalized reconstruction error:
L_anomaly = ||x - x_hat||^2
Flags sleeper account activations and out-of-distribution velocity.
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from src.core.models import Transaction
from src.data_engineering.feature_store import feature_store


class AnomalyAutoencoder:
    """Deep autoencoder modeling normal behavioral baseline manifolds."""

    def __init__(self):
        self.scaler = StandardScaler()
        # Symmetric bottleneck architecture: 7 -> 4 -> 2 -> 4 -> 7
        self.model = MLPRegressor(
            hidden_layer_sizes=(4, 2, 4),
            activation="relu",
            max_iter=100,
            random_state=42,
        )
        self._is_fitted = False
        self._fit_baseline_synthetic()

    def _fit_baseline_synthetic(self):
        """Fit autoencoder on normal baseline financial behavior."""
        np.random.seed(42)
        n_normal = 400
        x_normal = np.column_stack([
            np.random.exponential(scale=250, size=n_normal),         # amount
            np.random.uniform(0.01, 1.0, size=n_normal),             # v1h_v30d_ratio
            np.random.uniform(0.5, 6.0, size=n_normal),              # v24h_daily_ratio
            np.random.normal(0.0, 1.0, size=n_normal),               # amount_zscore
            np.random.uniform(0.0, 0.35, size=n_normal),             # geo_entropy
            np.random.uniform(0.1, 2.0, size=n_normal),              # tenure_deviation
            np.random.choice([0, 1], size=n_normal, p=[0.95, 0.05]), # failed_auth_count
        ])

        x_scaled = self.scaler.fit_transform(x_normal)
        self.model.fit(x_scaled, x_scaled)
        self._is_fitted = True

        # Calculate baseline MSE distribution for calibration
        baseline_reconstructed = self.model.predict(x_scaled)
        baseline_mses = np.mean((x_scaled - baseline_reconstructed) ** 2, axis=1)
        self._baseline_mse_mean = float(np.mean(baseline_mses))
        self._baseline_mse_std = float(np.std(baseline_mses)) + 1e-4

    def predict_score(self, txn: Transaction) -> float:
        """Compute anomaly score from reconstruction error in [0.0, 1.0]."""
        raw_vec = feature_store.get_feature_vector(txn).reshape(1, -1)
        scaled_vec = self.scaler.transform(raw_vec)
        reconstructed = self.model.predict(scaled_vec)

        # Mean Squared Error reconstruction loss
        mse = float(np.mean((scaled_vec - reconstructed) ** 2))

        # Normalized z-score over normal baseline MSE
        z = (mse - self._baseline_mse_mean) / self._baseline_mse_std
        # Sigmoid calibration: normal z around 0 gives ~0.15 score, high z > 3 gives > 0.8
        score = 1.0 / (1.0 + np.exp(-0.8 * (z - 2.0)))
        return min(1.0, max(0.0, float(score)))


anomaly_autoencoder = AnomalyAutoencoder()
