"""Multi-Agent Cognitive Swarm (Tier 3)."""

from src.agents.state import ExecutionDAG, TaskNode, InvestigationDossier
from src.agents.supervisor import SupervisorAgent, supervisor_agent
from src.agents.entity_resolution import EntityResolutionAgent, entity_resolution_agent
from src.agents.forensics import TransactionForensicsAgent, transaction_forensics_agent
from src.agents.osint import OSINTAgent, osint_agent
from src.agents.sar_synthesis import SARSynthesisAgent, sar_synthesis_agent
from src.agents.compliance_critic import ComplianceCriticAgent, compliance_critic_agent
from src.agents.swarm_orchestrator import SwarmOrchestrator, swarm_orchestrator

__all__ = [
    "ExecutionDAG",
    "TaskNode",
    "InvestigationDossier",
    "SupervisorAgent",
    "supervisor_agent",
    "EntityResolutionAgent",
    "entity_resolution_agent",
    "TransactionForensicsAgent",
    "transaction_forensics_agent",
    "OSINTAgent",
    "osint_agent",
    "SARSynthesisAgent",
    "sar_synthesis_agent",
    "ComplianceCriticAgent",
    "compliance_critic_agent",
    "SwarmOrchestrator",
    "swarm_orchestrator",
]
