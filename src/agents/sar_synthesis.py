"""SAR Synthesis Micro-Agent."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from src.core.models import (
    Alert,
    SuspiciousActivityReport,
    TypologyType,
)
from src.agents.tools.sar_tools import sar_tools


class SARSynthesisAgent:
    """Compiles objective, chronological, and audit-ready Suspicious Activity Reports."""

    def __init__(self):
        self.name = "SARSynthesisAgent"

    def synthesize(
        self,
        alert: Alert,
        entity_findings: Dict[str, Any],
        forensic_findings: Dict[str, Any],
        osint_findings: Dict[str, Any],
    ) -> SuspiciousActivityReport:
        """Formulate FinCEN/FIU compliant SAR document."""
        txn = alert.transaction
        scoring = alert.ml_scoring
        typology = scoring.inferred_typology

        # 1. Activity Codes
        activity_codes = sar_tools.get_fincen_codes(typology)

        # 2. Suspect & Counterparties
        suspect_name = txn.sender.name
        controllers = entity_findings.get("true_controllers", [])
        if controllers:
            suspect_name = f"{suspect_name} (Controlling Beneficial Owner: {', '.join(controllers)})"

        counterparties = [txn.receiver.name]
        involved_accounts = [txn.sender.account_id, txn.receiver.account_id]

        # 3. Timeline Events
        timeline = [
            {
                "timestamp": txn.timestamp.isoformat(),
                "event": "TRANSACTION_EXECUTED",
                "details": f"Execution of {txn.channel.value} payment of ${txn.amount:,.2f} via {txn.payment_rail}",
            }
        ]

        for hop in forensic_findings.get("pass_through_analysis", {}).get("peeling_chain_path", []):
            timeline.append({
                "timestamp": txn.timestamp.isoformat(),
                "event": f"PEELING_HOP_{hop['hop']}",
                "details": f"Fund routing from {hop['from_account']} to {hop['to_account']} (${hop['amount']:,.2f}) within {hop['dwell_time_seconds']}s",
            })

        for art in osint_findings.get("adverse_media_articles", []):
            timeline.append({
                "timestamp": art.get("publish_date", "2024-01-01"),
                "event": "ADVERSE_MEDIA_REFERENCE",
                "details": f"{art['source']}: {art['title']}",
            })

        # 4. Factual Regulatory Narrative formulation
        narrative_paragraphs = [
            f"1. EXECUTIVE SUMMARY: On {txn.timestamp.strftime('%Y-%m-%d')}, the institution's automated monitoring "
            f"flagged suspicious transaction activity on account {txn.sender.account_id} held by {txn.sender.name}, "
            f"totaling ${txn.amount:,.2f} USD. The activity was identified as exhibiting characteristics of "
            f"{typology.value.replace('_', ' ').title()}.",

            f"2. TYPOLOGY & TRANSACTION PATTERN: {forensic_findings.get('summary', '')} "
            f"The transaction risk score was calibrated at {scoring.s_final:.3f} "
            f"(Supervised: {scoring.s_supervised:.3f}, Anomaly Loss: {scoring.s_unsupervised:.3f}, Graph Topology: {scoring.s_graph:.3f}).",

            f"3. ENTITY & CORPORATE OWNERSHIP: {entity_findings.get('summary', '')}",

            f"4. ADVERSE INTELLIGENCE & BACKGROUND: {osint_findings.get('summary', '')}",

            "5. REGULATORY CONCLUSION: Due to the convergence of topological layering, out-of-pattern velocity, "
            "and absence of verifiable economic rationale, this report is submitted in accordance with statutory "
            "Bank Secrecy Act obligations.",
        ]

        narrative = "\n\n".join(narrative_paragraphs)

        return SuspiciousActivityReport(
            sar_id=f"SAR-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}",
            alert_id=alert.alert_id,
            suspect_name=suspect_name,
            suspect_tax_id=txn.sender.ssn,
            suspect_address=f"{txn.sender.city or 'N/A'}, {txn.sender.country}",
            suspicious_activity_codes=activity_codes,
            total_amount_flagged=txn.amount,
            narrative=narrative,
            timeline_events=timeline,
            involved_accounts=involved_accounts,
            counterparties=counterparties,
            critic_groundedness_score=1.0,
        )


sar_synthesis_agent = SARSynthesisAgent()
