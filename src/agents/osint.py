"""External OSINT and Adverse Media Micro-Agent."""

from typing import Dict, Any, List
from src.core.models import Alert
from src.agents.tools.osint_tools import osint_tools


class OSINTAgent:
    """Investigates adverse media, law enforcement bulletins, and TBML price deviations."""

    def __init__(self):
        self.name = "OSINTAgent"

    def investigate(self, alert: Alert, resolved_entities: List[str] = None) -> Dict[str, Any]:
        """Search adverse media and evaluate trade invoices for suspect entities."""
        txn = alert.transaction
        targets = [txn.sender.name, txn.receiver.name]
        if resolved_entities:
            targets.extend(resolved_entities)

        media_hits = []
        for entity in set(targets):
            hits = osint_tools.search_adverse_media(entity)
            if hits:
                media_hits.extend(hits)

        # Check TBML if commercial or trade invoice metadata exists
        tbml_data = {}
        hs_code = txn.metadata.get("hs_code")
        invoiced_price = txn.metadata.get("invoiced_unit_price")
        if hs_code and invoiced_price:
            tbml_data = osint_tools.verify_tbml_pricing(hs_code, float(invoiced_price))

        has_adverse_media = len(media_hits) > 0
        has_tbml = tbml_data.get("is_tbml_flagged", False)

        top_article = media_hits[0]["title"] if media_hits else "None"
        summary = (
            f"OSINT Review: Adverse Media Hits: {len(media_hits)}. "
            f"Top Article: '{top_article}'. "
            f"TBML Price Anomaly: {has_tbml} ({tbml_data.get('anomaly_direction', 'N/A')})."
        )

        return {
            "agent": self.name,
            "entities_queried": list(set(targets)),
            "has_adverse_media": has_adverse_media,
            "adverse_media_articles": media_hits,
            "tbml_analysis": tbml_data,
            "summary": summary,
        }


osint_agent = OSINTAgent()
