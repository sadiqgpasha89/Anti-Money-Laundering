"""Swarm Orchestrator with Circuit Breakers and Graceful Fallback."""

from typing import Dict, Any, Optional
from src.core.config import settings
from src.core.models import Alert, DecisionStatus
from src.agents.state import InvestigationDossier
from src.agents.supervisor import supervisor_agent


class SwarmOrchestrator:
    """Coordinates multi-agent execution with circuit breakers and fallback modes."""

    def __init__(self):
        self.circuit_breaker_active = False
        self.consecutive_failures = 0
        self.max_failures = 3

    def investigate_alert(self, alert: Alert) -> InvestigationDossier:
        """Run multi-agent investigation, handling circuit breakers and fallback."""
        if settings.SAFE_DEGRADATION_MODE or self.circuit_breaker_active:
            # Fallback: Create degraded dossier without heavy cloud LLM agents
            return self._execute_fallback(alert)

        try:
            dossier = supervisor_agent.execute_investigation(alert)
            self.consecutive_failures = 0
            return dossier
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures:
                self.circuit_breaker_active = True
            # Return graceful fallback
            return self._execute_fallback(alert, error_reason=str(e))

    def _execute_fallback(self, alert: Alert, error_reason: Optional[str] = None) -> InvestigationDossier:
        """Safe degradation fallback: Route alert directly to human investigator."""
        reason = error_reason or "Safe degradation mode active (OpenStack on-prem fallback)."
        return InvestigationDossier(
            dossier_id=f"DOSSIER-DEGRADED-{alert.alert_id}",
            alert=alert,
            triage_determination=DecisionStatus.ESCALATED_HUMAN,
            clearance_rationale=f"Escalated due to circuit breaker: {reason}",
            groundedness_score=1.0,
            critic_approved=True,
        )

    def reset_circuit_breaker(self):
        """Reset the circuit breaker after system health is restored."""
        self.circuit_breaker_active = False
        self.consecutive_failures = 0


swarm_orchestrator = SwarmOrchestrator()
