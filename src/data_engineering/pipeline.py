"""End-to-end orchestrated data engineering pipeline."""

import time
from typing import Dict, Any, Tuple
from src.core.models import Transaction
from src.core.crypto_audit import audit_ledger
from src.data_engineering.tokenizer import pii_tokenizer
from src.data_engineering.feature_store import feature_store
from src.data_engineering.graph_builder import aml_graph
from src.data_engineering.lakehouse_sink import lakehouse_sink


class DataPipeline:
    """Coordinates multi-stage data engineering flow across OpenStack and GCP boundaries."""

    def __init__(self):
        self._processed_count = 0

    def process_incoming_transaction(self, raw_txn: Transaction) -> Tuple[Transaction, Transaction, Dict[str, float]]:
        """
        Execute full data engineering pipeline:
        1. Ingest raw transaction (On-Prem OpenStack)
        2. Hydrate Feature Store (Online & Offline windows)
        3. Update Knowledge Graph topology
        4. Tokenize PII for cross-cloud GCP transit
        5. Record Cryptographic Audit Block
        6. Sink to Lakehouse

        Returns: (raw_txn, tokenized_txn, online_features)
        """
        t0 = time.perf_counter()
        self._processed_count += 1

        # 1. Update Knowledge Graph with on-prem cleartext relationships
        aml_graph.add_transaction(raw_txn)

        # 2. Hydrate rolling Feature Store
        feature_store.record_transaction(raw_txn)
        online_features = feature_store.get_online_features(raw_txn)

        # 3. Cryptographic Audit Record: Event Ingress
        audit_ledger.record_event(
            event_type="EVENT_INGRESS",
            payload={
                "transaction_id": raw_txn.transaction_id,
                "timestamp": raw_txn.timestamp.isoformat(),
                "amount": raw_txn.amount,
                "currency": raw_txn.currency,
                "sender_account": raw_txn.sender.account_id,
                "receiver_account": raw_txn.receiver.account_id,
            },
            actor="INGESTION_FABRIC",
        )

        # 4. Tokenize & Scrub PII for Cloud Interconnect Transit
        tokenized_txn = pii_tokenizer.tokenize_transaction(raw_txn)

        # 5. Sink to Lakehouse
        lakehouse_sink.sink_transaction(tokenized_txn)

        duration_ms = (time.perf_counter() - t0) * 1000.0
        online_features["de_pipeline_latency_ms"] = duration_ms

        return raw_txn, tokenized_txn, online_features


data_pipeline = DataPipeline()
