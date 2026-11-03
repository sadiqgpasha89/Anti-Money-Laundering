"""Configuration module for Hybrid AML Architecture (OpenStack + GCP)."""

import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Hybrid Cloud and AML Platform Configuration."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "AML Hybrid Architecture Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    SECRET_KEY: str = "aml-super-secret-hmac-tokenization-key-2026"

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    SANCTIONS_PATH: Path = DATA_DIR / "sanctions_list.json"
    CORPORATE_REGISTRY_PATH: Path = DATA_DIR / "corporate_registry.json"
    ADVERSE_MEDIA_PATH: Path = DATA_DIR / "adverse_media.json"
    COMMODITY_BENCHMARKS_PATH: Path = DATA_DIR / "commodity_benchmarks.json"
    SEED_TRANSACTIONS_PATH: Path = DATA_DIR / "seed_transactions.json"

    # OpenStack / On-Premise Enclave Configuration
    OPENSTACK_REGION: str = "dc-west-1"
    OPENSTACK_NOVA_CELL: str = "cell-edge-compute-01"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-cluster.openstack.internal:9092"
    KAFKA_TRANSACTION_TOPIC: str = "aml.financial.transactions.v1"
    KAFKA_ALERT_TOPIC: str = "aml.triage.alerts.v1"
    REDIS_FEATURE_CACHE_URL: str = "redis://redis-cluster.openstack.internal:6379/0"
    SAFE_DEGRADATION_MODE: bool = False  # If True, OpenStack operates without GCP

    # Google Cloud Platform (GCP) Enclave Configuration
    GCP_PROJECT_ID: str = "aml-sentinel-prod"
    GCP_REGION: str = "us-central1"
    GKE_CLUSTER_NAME: str = "aml-agent-cluster-autopilot"
    VERTEX_AI_ENDPOINT: str = "projects/aml-sentinel-prod/locations/us-central1/endpoints/llm-zero-retention"
    BIGQUERY_DATASET: str = "aml_analytical_lakehouse"
    CLOUD_INTERCONNECT_SATURATION_MAX: float = 0.85

    # Tier 1 Deterministic Rules Configuration
    TIER1_CTR_THRESHOLD: float = 10000.0
    TIER1_MAX_LATENCY_MS: float = 20.0
    SANCTIONS_JARO_THRESHOLD: float = 0.88
    SANCTIONS_LEVENSHTEIN_DISTANCE: int = 2
    HIGH_RISK_COUNTRIES: List[str] = Field(
        default=["KP", "IR", "RU", "MM", "SY"]
    )
    MAX_VELOCITY_FAILURES: int = 5

    # Tier 2 Machine Learning & Graph Analytics Configuration
    TIER2_LOW_THRESHOLD: float = 0.35
    TIER2_HIGH_THRESHOLD: float = 0.70
    TIER2_MAX_LATENCY_MS: float = 100.0
    WEIGHT_SUPERVISED: float = 0.40
    WEIGHT_UNSUPERVISED: float = 0.30
    WEIGHT_GRAPH: float = 0.30
    AUTOENCODER_RECONSTRUCTION_THRESHOLD: float = 0.65

    # Tier 3 Multi-Agent Workspace Configuration
    TIER3_GROUNDEDNESS_THRESHOLD: float = 0.90
    AGENT_MAX_RECURSION_STEPS: int = 10
    AGENT_TIMEOUT_SECONDS: float = 60.0

    # Business & System Targets
    TARGET_THROUGHPUT_TPS: int = 10000
    BURST_THROUGHPUT_TPS: int = 50000
    TARGET_MTTI_MINUTES: float = 20.0
    BASELINE_MTTI_HOURS: float = 4.0


settings = Settings()
