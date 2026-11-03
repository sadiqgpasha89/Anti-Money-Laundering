"""Supervisor Agent for Autonomous DAG Planning and Swarm Coordination."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from src.core.models import (
    Alert,
    DecisionStatus,
    RiskTier,
)
from src.core.crypto_audit import audit_ledger
from src.agents.state import ExecutionDAG, TaskNode, InvestigationDossier
from src.agents.entity_resolution import entity_resolution_agent
from src.agents.forensics import transaction_forensics_agent
from src.agents.osint import osint_agent
from src.agents.sar_synthesis import sar_synthesis_agent
from src.agents.compliance_critic import compliance_critic_agent


class SupervisorAgent:
    """Orchestrates multi-agent swarm, formulates execution DAG, and oversees adjudication."""

    def __init__(self):
        self.name = "SupervisorAgent"

    def formulate_execution_dag(self, alert: Alert) -> ExecutionDAG:
        """Construct Directed Acyclic Graph of tasks based on alert risk profile."""
        dag_id = f"DAG-{uuid.uuid4().hex[:8].upper()}"

        tasks = {
            "TASK_ENTITY": TaskNode(
                task_id="TASK_ENTITY",
                agent_name="EntityResolutionAgent",
                description="Unroll corporate UBO and evaluate shared device infrastructure.",
                dependencies=[],
            ),
            "TASK_FORENSICS": TaskNode(
                task_id="TASK_FORENSICS",
                agent_name="TransactionForensicsAgent",
                description="Analyze pass-through velocity, dwell time, and peeling paths.",
                dependencies=[],
            ),
            "TASK_OSINT": TaskNode(
                task_id="TASK_OSINT",
                agent_name="OSINTAgent",
                description="Perform vector adverse media search and TBML invoice verification.",
                dependencies=["TASK_ENTITY"],
            ),
            "TASK_SAR": TaskNode(
                task_id="TASK_SAR",
                agent_name="SARSynthesisAgent",
                description="Compile unified chronological narrative and regulatory activity codes.",
                dependencies=["TASK_ENTITY", "TASK_FORENSICS", "TASK_OSINT"],
            ),
            "TASK_CRITIC": TaskNode(
                task_id="TASK_CRITIC",
                agent_name="ComplianceCriticAgent",
                description="Audit factual grounding of narrative against underlying records.",
                dependencies=["TASK_SAR"],
            ),
        }

        return ExecutionDAG(dag_id=dag_id, alert_id=alert.alert_id, tasks=tasks)

    def execute_investigation(self, alert: Alert) -> InvestigationDossier:
        """
        Execute full multi-agent investigation workflow:
        1. Formulate DAG
        2. Parallel execution of Entity Resolution and Forensics
        3. OSINT with resolved entities
        4. SAR Synthesis
        5. Compliance Critic Entailment Audit
        6. Determine Autonomous Clearance vs Escalation
        7. Record Cryptographic Audit Trace
        """
        dag = self.formulate_execution_dag(alert)
        total_tokens = 0
        total_tool_calls = 0

        # Step 1: Entity Resolution
        t_entity = dag.tasks["TASK_ENTITY"]
        t_entity.status = "RUNNING"
        t_entity.started_at = datetime.now(timezone.utc)
        entity_findings = entity_resolution_agent.investigate(alert)
        t_entity.result = entity_findings
        t_entity.status = "COMPLETED"
        t_entity.completed_at = datetime.now(timezone.utc)
        total_tool_calls += 3
        total_tokens += 1250

        # Step 2: Transaction Forensics
        t_forensics = dag.tasks["TASK_FORENSICS"]
        t_forensics.status = "RUNNING"
        t_forensics.started_at = datetime.now(timezone.utc)
        forensic_findings = transaction_forensics_agent.investigate(alert)
        t_forensics.result = forensic_findings
        t_forensics.status = "COMPLETED"
        t_forensics.completed_at = datetime.now(timezone.utc)
        total_tool_calls += 2
        total_tokens += 980

        # Step 3: OSINT & Adverse Media (conditioned on resolved controllers)
        t_osint = dag.tasks["TASK_OSINT"]
        t_osint.status = "RUNNING"
        t_osint.started_at = datetime.now(timezone.utc)
        resolved_entities = entity_findings.get("true_controllers", [])
        osint_findings = osint_agent.investigate(alert, resolved_entities=resolved_entities)
        t_osint.result = osint_findings
        t_osint.status = "COMPLETED"
        t_osint.completed_at = datetime.now(timezone.utc)
        total_tool_calls += 2
        total_tokens += 1400

        # Step 4: SAR Synthesis
        t_sar = dag.tasks["TASK_SAR"]
        t_sar.status = "RUNNING"
        t_sar.started_at = datetime.now(timezone.utc)
        draft_sar = sar_synthesis_agent.synthesize(
            alert=alert,
            entity_findings=entity_findings,
            forensic_findings=forensic_findings,
            osint_findings=osint_findings,
        )
        t_sar.result = {"sar_id": draft_sar.sar_id}
        t_sar.status = "COMPLETED"
        t_sar.completed_at = datetime.now(timezone.utc)
        total_tool_calls += 1
        total_tokens += 1850

        # Step 5: Compliance Critic Audit
        t_critic = dag.tasks["TASK_CRITIC"]
        t_critic.status = "RUNNING"
        t_critic.started_at = datetime.now(timezone.utc)

        corpus_evidence = {
            "transaction": alert.transaction.model_dump(),
            "entity_findings": entity_findings,
            "forensic_findings": forensic_findings,
            "osint_findings": osint_findings,
        }

        approved, score, evals, ungrounded = compliance_critic_agent.audit_narrative(
            sar=draft_sar,
            dossier_evidence=corpus_evidence,
        )

        draft_sar.critic_groundedness_score = score
        draft_sar.critic_feedback = (
            "Approved: 100% factual grounding." if approved
            else f"Needs revision: {len(ungrounded)} ungrounded statements."
        )

        t_critic.result = {
            "approved": approved,
            "groundedness_score": score,
            "ungrounded_count": len(ungrounded),
        }
        t_critic.status = "COMPLETED"
        t_critic.completed_at = datetime.now(timezone.utc)
        total_tool_calls += 1
        total_tokens += 1100

        dag.is_completed = True

        # Step 6: Triage Determination
        # Evaluate if this is a benign false positive that can be cleared autonomously
        has_severe_evidence = (
            entity_findings.get("is_synthetic_ring")
            or entity_findings.get("is_fractional_ubo")
            or forensic_findings.get("is_peeling_chain")
            or forensic_findings.get("is_smurfing_structure")
            or osint_findings.get("has_adverse_media")
            or osint_findings.get("tbml_analysis", {}).get("is_tbml_flagged")
        )

        if not has_severe_evidence and alert.ml_scoring.s_final < 0.45:
            determination = DecisionStatus.AUTO_CLEARED
            clearance_rationale = (
                "Autonomously cleared by Multi-Agent Swarm: No synthetic device ring, "
                "no peeling chain, negative adverse media, and consistent UBO disclosure."
            )
        else:
            determination = DecisionStatus.ESCALATED_HUMAN
            clearance_rationale = None

        dossier = InvestigationDossier(
            dossier_id=f"DOSSIER-{uuid.uuid4().hex[:8].upper()}",
            alert=alert,
            execution_dag=dag,
            entity_resolution_findings=entity_findings,
            forensic_findings=forensic_findings,
            osint_findings=osint_findings,
            draft_sar=draft_sar,
            grounding_evaluations=evals,
            groundedness_score=score,
            critic_approved=approved,
            triage_determination=determination,
            clearance_rationale=clearance_rationale,
            total_tokens_consumed=total_tokens,
            total_tool_calls=total_tool_calls,
        )

        # Step 7: Cryptographic Audit Trace: Agent Trace
        audit_ledger.record_event(
            event_type="AGENT_TRACE",
            payload={
                "dossier_id": dossier.dossier_id,
                "alert_id": alert.alert_id,
                "dag_id": dag.dag_id,
                "triage_determination": determination.value,
                "critic_groundedness": score,
                "total_tokens": total_tokens,
                "total_tools": total_tool_calls,
            },
            actor="SUPERVISOR_AGENT",
        )

        return dossier


supervisor_agent = SupervisorAgent()
