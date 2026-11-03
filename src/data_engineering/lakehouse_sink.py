"""Analytical Lakehouse Sink for BigQuery / Iceberg Archival and Drift Analytics."""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from src.core.models import Transaction, Alert


class LakehouseSink:
    """Simulates GCP BigQuery / Apache Iceberg analytical lakehouse sink."""

    def __init__(self):
        self._raw_events: List[Dict[str, Any]] = []
        self._alerts_archive: List[Dict[str, Any]] = []

    def sink_transaction(self, txn: Transaction):
        """Append pseudonymized transaction event into lakehouse partitions."""
        record = {
            "ingest_timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_id": txn.transaction_id,
            "timestamp": txn.timestamp.isoformat(),
            "amount": txn.amount,
            "currency": txn.currency,
            "channel": txn.channel.value,
            "sender_cust_token": txn.sender.customer_id,
            "sender_country": txn.sender.country,
            "receiver_cust_token": txn.receiver.customer_id,
            "geo_hash": txn.telemetry.geo_hash,
            "is_tokenized": txn.is_tokenized,
        }
        self._raw_events.append(record)

    def sink_alert(self, alert: Alert):
        """Sink flagged alert into regulatory compliance analytics dataset."""
        record = {
            "alert_id": alert.alert_id,
            "created_at": alert.created_at.isoformat(),
            "transaction_id": alert.transaction.transaction_id,
            "risk_tier": alert.ml_scoring.risk_tier.value,
            "s_final": alert.ml_scoring.s_final,
            "inferred_typology": alert.ml_scoring.inferred_typology.value,
            "status": alert.status.value,
        }
        self._alerts_archive.append(record)

    def get_historical_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent analytical records for drift computation."""
        return self._raw_events[-limit:]


lakehouse_sink = LakehouseSink()
