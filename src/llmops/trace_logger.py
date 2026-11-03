"""Agent Action Provenance and Execution Trace Logger."""

from typing import Dict, Any, List
from src.core.crypto_audit import audit_ledger


class TraceLogger:
    """Records detailed agent execution traces and tool outputs with cryptographic provenance."""

    def __init__(self):
        self._traces: List[Dict[str, Any]] = []

    def log_agent_step(
        self,
        alert_id: str,
        agent_name: str,
        step_name: str,
        tool_name: str,
        tool_input: Any,
        tool_output: Any,
    ):
        """Append step trace and record hash in audit ledger."""
        trace_entry = {
            "alert_id": alert_id,
            "agent_name": agent_name,
            "step_name": step_name,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
        }
        self._traces.append(trace_entry)

        # Mirror in cryptographic ledger
        audit_ledger.record_event(
            event_type="AGENT_STEP_EXEC",
            payload=trace_entry,
            actor=agent_name,
        )

    def get_traces_for_alert(self, alert_id: str) -> List[Dict[str, Any]]:
        """Retrieve execution trace history for an alert."""
        return [t for t in self._traces if t["alert_id"] == alert_id]


trace_logger = TraceLogger()
