"""Multi-channel streaming ingestion fabric (ISO 20022, ACH, Card, Cash)."""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from src.core.models import Transaction, PartyProfile, TelemetryData, PaymentChannel, RiskTier


class TransactionIngestor:
    """Ingests, parses, and standardizes multi-channel financial event streams."""

    def __init__(self):
        self._ingested_count = 0

    def parse_raw_event(self, raw_data: Dict[str, Any]) -> Transaction:
        """Normalize raw incoming payload into canonical ISO 20022 Transaction model."""
        self._ingested_count += 1

        sender_data = raw_data.get("sender", {})
        receiver_data = raw_data.get("receiver", {})
        telemetry_data = raw_data.get("telemetry", {})

        # Parse timestamp
        raw_ts = raw_data.get("timestamp")
        if isinstance(raw_ts, str):
            ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        elif isinstance(raw_ts, datetime):
            ts = raw_ts
        else:
            ts = datetime.now(timezone.utc)

        raw_risk = str(sender_data.get("risk_rating", "LOW")).upper()
        try:
            risk_tier = RiskTier(raw_risk)
        except ValueError:
            risk_tier = RiskTier.LOW

        sender = PartyProfile(
            customer_id=sender_data.get("customer_id", "UNKNOWN_CUST"),
            account_id=sender_data.get("account_id", "UNKNOWN_ACCT"),
            name=sender_data.get("name", "ANONYMOUS"),
            ssn=sender_data.get("ssn"),
            country=sender_data.get("country", "US"),
            city=sender_data.get("city"),
            account_tenure_months=sender_data.get("account_tenure_months", 12),
            historical_monthly_avg_vol=sender_data.get("historical_monthly_avg_vol", 1000.0),
            risk_rating=risk_tier,
            is_pep=sender_data.get("is_pep", False),
            is_sanctioned=sender_data.get("is_sanctioned", False),
        )

        receiver = PartyProfile(
            customer_id=receiver_data.get("customer_id", "UNKNOWN_CUST"),
            account_id=receiver_data.get("account_id", "UNKNOWN_ACCT"),
            name=receiver_data.get("name", "ANONYMOUS"),
            country=receiver_data.get("country", "US"),
            city=receiver_data.get("city"),
        )

        telemetry = TelemetryData(
            device_id=telemetry_data.get("device_id"),
            mac_address=telemetry_data.get("mac_address"),
            ip_address=telemetry_data.get("ip_address"),
            geo_hash=telemetry_data.get("geo_hash"),
            phone_hash=telemetry_data.get("phone_hash"),
            failed_auth_count=telemetry_data.get("failed_auth_count", 0),
        )

        channel_str = raw_data.get("channel", "DOMESTIC_ACH")
        try:
            channel = PaymentChannel(channel_str)
        except ValueError:
            channel = PaymentChannel.DOMESTIC_ACH

        return Transaction(
            transaction_id=raw_data.get("transaction_id", f"TXN-{self._ingested_count}"),
            timestamp=ts,
            amount=float(raw_data.get("amount", 0.0)),
            currency=raw_data.get("currency", "USD"),
            channel=channel,
            payment_rail=raw_data.get("payment_rail", "ISO20022_PACS008"),
            sender=sender,
            receiver=receiver,
            telemetry=telemetry,
            metadata=raw_data.get("metadata", {}),
        )

    def load_seed_transactions(self, file_path: str) -> List[Transaction]:
        """Load and parse transactions from seed file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [self.parse_raw_event(item) for item in data]


transaction_ingestor = TransactionIngestor()
