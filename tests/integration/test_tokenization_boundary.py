"""The graph, the feature store and the agents must all work in the same (tokenized) identity space."""

from src.core.models import Alert, PartyProfile, PaymentChannel, TelemetryData, Transaction
from src.data_engineering.feature_store import feature_store
from src.data_engineering.graph_builder import aml_graph
from src.data_engineering.pipeline import data_pipeline
from src.datascience.tier1_rules.engine import tier1_engine
from src.datascience.tier2_ml.graph_neural_net import graph_scorer
from src.datascience.tier2_ml.model_blender import model_blender
from src.agents.entity_resolution import entity_resolution_agent
from src.agents.osint import osint_agent


def _txn(txn_id, cust, acct, name, device=None, receiver_name="TOKEN BOUNDARY RECEIVER"):
    return Transaction(
        transaction_id=txn_id,
        amount=1200.0,
        channel=PaymentChannel.DOMESTIC_ACH,
        sender=PartyProfile(customer_id=cust, account_id=acct, name=name),
        receiver=PartyProfile(customer_id=f"{cust}-R", account_id=f"{acct}-R", name=receiver_name),
        telemetry=TelemetryData(device_id=device, geo_hash="dr5reg"),
    )


def _alert(raw, tokenized):
    return Alert(
        alert_id=f"ALT-{raw.transaction_id}",
        transaction=tokenized,
        tier1_result=tier1_engine.evaluate(raw),
        ml_scoring=model_blender.score_transaction(tokenized),
    )


def test_graph_and_feature_store_are_keyed_by_token():
    raw = _txn("TXN-TB-KEY-1", "CUST-TB-KEY", "ACCT-TB-KEY", "TOKEN KEY PERSON")
    _, tokenized, _ = data_pipeline.process_incoming_transaction(raw)

    assert tokenized.sender.account_id.startswith("TOK_ACCT_")
    assert tokenized.sender.account_id in aml_graph.graph
    assert "ACCT-TB-KEY" not in aml_graph.graph  # no cleartext identifier in the cloud-side graph
    assert len(feature_store._history[tokenized.sender.account_id]) == 1
    assert "ACCT-TB-KEY" not in feature_store._history


def test_shared_device_ring_survives_tokenization():
    """Two unrelated customers on one device is the synthetic-identity signal; Tier 2 sees it only if the graph uses tokens."""
    first = _txn("TXN-TB-RING-1", "CUST-TB-RING-A", "ACCT-TB-RING-A", "RING MEMBER ONE", device="DEV-TB-RING")
    second = _txn("TXN-TB-RING-2", "CUST-TB-RING-B", "ACCT-TB-RING-B", "RING MEMBER TWO", device="DEV-TB-RING")
    data_pipeline.process_incoming_transaction(first)
    _, tokenized, _ = data_pipeline.process_incoming_transaction(second)

    assert graph_scorer.predict_score(tokenized) >= 0.5  # 0.05 baseline + 0.45 shared-device weight
    assert entity_resolution_agent.investigate(_alert(second, tokenized))["is_synthetic_ring"] is True


def test_entity_agent_unrolls_ubo_for_a_tokenized_company():
    raw = _txn("TXN-TB-UBO-1", "CUST-TB-UBO", "ACCT-TB-UBO", "BLUE HORIZON HOLDINGS LTD")
    _, tokenized, _ = data_pipeline.process_incoming_transaction(raw)
    assert tokenized.sender.name.startswith("TOK_NAME_")

    findings = entity_resolution_agent.investigate(_alert(raw, tokenized))

    assert findings["ubo_details"]["ubo_resolved"] is True
    assert "DMITRY V. SOKOLOV" in findings["true_controllers"]


def test_osint_agent_finds_adverse_media_for_a_tokenized_name():
    raw = _txn("TXN-TB-MEDIA-1", "CUST-TB-MEDIA", "ACCT-TB-MEDIA", "BLUE HORIZON HOLDINGS LTD")
    _, tokenized, _ = data_pipeline.process_incoming_transaction(raw)

    findings = osint_agent.investigate(_alert(raw, tokenized))

    assert findings["has_adverse_media"] is True
