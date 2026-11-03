"""Targeted tests for all 8 structural money laundering evasion typologies (Section 10)."""

import pytest
from src.core.config import settings
from src.core.models import TypologyType
from src.data_engineering.ingestion import transaction_ingestor
from src.datascience.tier1_rules.engine import tier1_engine
from src.datascience.tier2_ml.model_blender import model_blender
from src.datascience.tier2_ml.triage_gate import triage_gate
from src.agents.swarm_orchestrator import swarm_orchestrator


@pytest.fixture(scope="module")
def seed_transactions():
    return transaction_ingestor.load_seed_transactions(str(settings.SEED_TRANSACTIONS_PATH))


def _find_txn(txns, txn_id):
    return next((t for t in txns if t.transaction_id == txn_id), None)


def test_typology_1_smurfing_structuring(seed_transactions):
    """Typology 1: Sub-threshold structured cash deposits across confederate branches."""
    txn = _find_txn(seed_transactions, "TXN-SMURF-001")
    assert txn is not None
    assert txn.amount == 9500.0  # Sub CTR

    tier1 = tier1_engine.evaluate(txn)
    assert tier1.is_blocked is False  # Bypasses Tier 1 static threshold ($10,000)

    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.SMURFING_STRUCTURING
    assert scoring.s_final >= 0.35  # Caught by Tier 2


def test_typology_2_peeling_chains(seed_transactions):
    """Typology 2: Rapid pass-through peeling chain layering sequence."""
    txn = _find_txn(seed_transactions, "TXN-PEEL-001")
    assert txn is not None
    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.RAPID_VELOCITY_PEELING_CHAIN
    assert scoring.s_final >= 0.70  # High score


def test_typology_3_sleeper_mule_activation(seed_transactions):
    """Typology 3: Seasoned dormant account burst."""
    txn = _find_txn(seed_transactions, "TXN-SLEEP-001")
    assert txn is not None
    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.SLEEPER_MULE_ACTIVATION
    # Caught by Unsupervised Autoencoder anomaly loss
    assert scoring.s_unsupervised >= 0.70


def test_typology_4_synthetic_identity_rings(seed_transactions):
    """Typology 4: Synthetic identities sharing device hardware fingerprints."""
    txn = _find_txn(seed_transactions, "TXN-SYNTH-001")
    assert txn is not None
    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.SYNTHETIC_IDENTITY_RING
    assert scoring.s_graph >= 0.70  # Caught by Multigraph GNN


def test_typology_5_fractional_ubo_concealment(seed_transactions):
    """Typology 5: Concealed beneficial owner partitioned under 25% shell holdings."""
    txn = _find_txn(seed_transactions, "TXN-UBO-001")
    assert txn is not None
    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.FRACTIONAL_UBO_CONCEALMENT

    # Agent unrolls recursive UBO tree to find Dmitry Sokolov
    alert = triage_gate.evaluate_gate(txn, tier1_engine.evaluate(txn), scoring)
    dossier = swarm_orchestrator.investigate_alert(alert)
    true_controllers = dossier.entity_resolution_findings.get("true_controllers", [])
    assert any("SOKOLOV" in c for c in true_controllers)


def test_typology_6_crypto_mixer_bridges(seed_transactions):
    """Typology 6: Crypto-to-fiat privacy mixer bridge."""
    txn = _find_txn(seed_transactions, "TXN-CRYPTO-001")
    assert txn is not None
    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.CRYPTO_TO_FIAT_MIXER_BRIDGE


def test_typology_7_trade_based_money_laundering(seed_transactions):
    """Typology 7: Commercial wire with over-invoiced commodity prices."""
    txn = _find_txn(seed_transactions, "TXN-TBML-001")
    assert txn is not None
    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.TRADE_BASED_MONEY_LAUNDERING

    alert = triage_gate.evaluate_gate(txn, tier1_engine.evaluate(txn), scoring)
    dossier = swarm_orchestrator.investigate_alert(alert)
    tbml = dossier.osint_findings.get("tbml_analysis", {})
    assert tbml.get("is_tbml_flagged") is True
    assert tbml.get("anomaly_direction") == "OVER_INVOICED"


def test_typology_8_adversarial_ml_perturbations(seed_transactions):
    """Typology 8: Model gaming probe transactions mimicking payroll."""
    txn = _find_txn(seed_transactions, "TXN-ADVML-001")
    assert txn is not None
    scoring = model_blender.score_transaction(txn)
    assert scoring.inferred_typology == TypologyType.ADVERSARIAL_ML_PERTURBATION
    # Supervised score is intentionally undercut, but Autoencoder flags systemic anomaly
    assert scoring.s_unsupervised > scoring.s_supervised
    assert scoring.s_final >= settings.TIER2_LOW_THRESHOLD  # Still flagged by ensemble!
