"""Shared pytest fixtures and test setup."""

import pytest
from fastapi.testclient import TestClient
from src.core.models import (
    Transaction,
    PartyProfile,
    TelemetryData,
    PaymentChannel,
    RiskTier,
)
from src.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_transaction():
    """A standard legitimate retail transaction."""
    return Transaction(
        transaction_id="TXN-FIXTURE-001",
        amount=150.00,
        currency="USD",
        channel=PaymentChannel.CARD_CNP,
        payment_rail="VISA",
        sender=PartyProfile(
            customer_id="CUST-TEST-01",
            account_id="ACCT-TEST-01A",
            name="JANE DOE",
            ssn="999-11-2222",
            country="US",
            city="NEW YORK",
            account_tenure_months=24,
            historical_monthly_avg_vol=1200.0,
            risk_rating=RiskTier.LOW,
        ),
        receiver=PartyProfile(
            customer_id="CUST-TEST-02",
            account_id="ACCT-TEST-02B",
            name="METRO DELI & GROCERY",
            country="US",
            city="NEW YORK",
        ),
        telemetry=TelemetryData(
            device_id="DEV-PHONE-001",
            ip_address="192.0.2.1",
            geo_hash="dr5reg",
            failed_auth_count=0,
        ),
        metadata={"scenario": "NORMAL_TEST"},
    )


@pytest.fixture
def sanctions_transaction():
    """A transaction triggering a hard sanctions match."""
    return Transaction(
        transaction_id="TXN-FIXTURE-SANC",
        amount=50000.00,
        currency="USD",
        channel=PaymentChannel.SWIFT_WIRE,
        payment_rail="ISO20022_PACS008",
        sender=PartyProfile(
            customer_id="CUST-SANC-01",
            account_id="ACCT-SANC-01A",
            name="VLADIMIR KOROLYOV",
            country="RU",
            city="MOSCOW",
        ),
        receiver=PartyProfile(
            customer_id="CUST-RECV-01",
            account_id="ACCT-RECV-01",
            name="FOREIGN TRADE LTD",
            country="CY",
        ),
        telemetry=TelemetryData(
            device_id="DEV-SANC-01",
            ip_address="85.115.248.10",
            geo_hash="ucft0w",
        ),
        metadata={"scenario": "TIER1_HARD_SANCTIONS_MATCH"},
    )
