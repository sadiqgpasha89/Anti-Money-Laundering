"""Unit tests for Tier 3 Multi-Agent Cognitive Swarm."""

import pytest
from src.core.models import Alert
from src.datascience.tier1_rules.engine import tier1_engine
from src.datascience.tier2_ml.model_blender import model_blender
from src.agents.supervisor import supervisor_agent
from src.agents.entity_resolution import entity_resolution_agent
from src.agents.forensics import transaction_forensics_agent
from src.agents.osint import osint_agent
from src.agents.sar_synthesis import sar_synthesis_agent


@pytest.fixture
def alert_fixture(sample_transaction):
    tier1 = tier1_engine.evaluate(sample_transaction)
    scoring = model_blender.score_transaction(sample_transaction)
    return Alert(
        alert_id="ALT-UNIT-TEST",
        transaction=sample_transaction,
        tier1_result=tier1,
        ml_scoring=scoring,
    )


def test_supervisor_dag_formulation(alert_fixture):
    """Test supervisor DAG task generation."""
    dag = supervisor_agent.formulate_execution_dag(alert_fixture)
    assert len(dag.tasks) == 5
    assert "TASK_ENTITY" in dag.tasks
    assert "TASK_FORENSICS" in dag.tasks
    assert "TASK_OSINT" in dag.tasks
    assert "TASK_SAR" in dag.tasks
    assert "TASK_CRITIC" in dag.tasks


def test_entity_resolution_agent(alert_fixture):
    """Test entity resolution micro-agent."""
    res = entity_resolution_agent.investigate(alert_fixture)
    assert res["agent"] == "EntityResolutionAgent"
    assert "is_synthetic_ring" in res
    assert "ubo_details" in res


def test_forensics_agent(alert_fixture):
    """Test transaction forensics micro-agent."""
    res = transaction_forensics_agent.investigate(alert_fixture)
    assert res["agent"] == "TransactionForensicsAgent"
    assert "pass_through_analysis" in res
    assert "is_peeling_chain" in res


def test_osint_agent(alert_fixture):
    """Test OSINT and adverse media micro-agent."""
    res = osint_agent.investigate(alert_fixture)
    assert res["agent"] == "OSINTAgent"
    assert "has_adverse_media" in res


def test_sar_synthesis_agent(alert_fixture):
    """Test SAR synthesis narrative compilation."""
    entity_data = {"summary": "Entity check complete.", "true_controllers": ["JOHN DOE"]}
    forensic_data = {"summary": "No peeling chain detected."}
    osint_data = {"summary": "No adverse media records found.", "adverse_media_articles": []}

    sar = sar_synthesis_agent.synthesize(
        alert=alert_fixture,
        entity_findings=entity_data,
        forensic_findings=forensic_data,
        osint_findings=osint_data,
    )
    assert sar.sar_id.startswith("SAR-")
    assert "EXECUTIVE SUMMARY" in sar.narrative
    assert len(sar.suspicious_activity_codes) > 0
