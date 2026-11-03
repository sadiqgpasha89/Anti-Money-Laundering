"""Typed state definitions for Tier 3 Multi-Agent Workspace."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.core.models import (
    Alert,
    SuspiciousActivityReport,
    ClaimEvidencePair,
    DecisionStatus,
)


class TaskNode(BaseModel):
    """A discrete task in the Supervisor's execution DAG."""
    task_id: str
    agent_name: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionDAG(BaseModel):
    """Directed Acyclic Graph of investigative tasks formulated by Supervisor Agent."""
    dag_id: str
    alert_id: str
    tasks: Dict[str, TaskNode] = Field(default_factory=dict)
    is_completed: bool = False
    has_errors: bool = False


class InvestigationDossier(BaseModel):
    """Comprehensive evidence dossier assembled across all micro-agents."""
    dossier_id: str
    alert: Alert
    execution_dag: Optional[ExecutionDAG] = None

    # Agent Findings
    entity_resolution_findings: Dict[str, Any] = Field(default_factory=dict)
    forensic_findings: Dict[str, Any] = Field(default_factory=dict)
    osint_findings: Dict[str, Any] = Field(default_factory=dict)

    # Narrative & Compliance Review
    draft_sar: Optional[SuspiciousActivityReport] = None
    grounding_evaluations: List[ClaimEvidencePair] = Field(default_factory=list)
    groundedness_score: float = 1.0
    critic_approved: bool = False
    triage_determination: DecisionStatus = DecisionStatus.TRIAGING
    clearance_rationale: Optional[str] = None

    # Execution telemetry
    total_tokens_consumed: int = 0
    total_tool_calls: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
