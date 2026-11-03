"""Telemetry models and helpers for digital device footprints."""

import hashlib
from typing import Dict, Any


def hash_device_identifier(imei_or_mac: str, salt: str = "AML_DEVICE_SALT") -> str:
    """Deterministic hash for device IDs to preserve privacy while maintaining graph linkability."""
    return hashlib.sha256(f"{salt}:{imei_or_mac.strip().upper()}".encode("utf-8")).hexdigest()[:16]


def parse_geo_distance(geohash1: str, geohash2: str) -> float:
    """Approximate distance metric based on geohash prefix matching (0.0 to 1.0 divergence)."""
    if not geohash1 or not geohash2:
        return 0.5
    prefix_len = 0
    min_len = min(len(geohash1), len(geohash2))
    for i in range(min_len):
        if geohash1[i] == geohash2[i]:
            prefix_len += 1
        else:
            break
    # 0 match = 1.0 (extreme jump), 6 match = 0.0 (exact same neighborhood)
    return max(0.0, 1.0 - (prefix_len / 6.0))
