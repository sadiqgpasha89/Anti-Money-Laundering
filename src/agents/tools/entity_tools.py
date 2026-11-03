"""Entity Resolution and Recursive UBO Ownership Unrolling Tools."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.core.config import settings
from src.data_engineering.graph_builder import aml_graph


class EntityTools:
    """Agent toolset for resolving Ultimate Beneficial Ownership and digital identity linkage."""

    def __init__(self, registry_file: Optional[Path] = None):
        self.file_path = registry_file or settings.CORPORATE_REGISTRY_PATH
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self):
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    self._registry[entry["company_id"]] = entry
                    self._registry[entry["name"].upper()] = entry

    def unroll_ubo_tree(self, company_identifier: str) -> Dict[str, Any]:
        """
        Recursively unrolls nested corporate holdings to calculate Effective Indirect Control:
        C_effective = prod(M_ownership)
        Traverses through shell holding tiers across opaque jurisdictions.
        """
        lookup_key = company_identifier.upper().strip()
        comp = self._registry.get(lookup_key)

        if not comp:
            # Fallback search by company_id
            for c in self._registry.values():
                if c.get("company_id", "").upper() == lookup_key or c.get("name", "").upper() == lookup_key:
                    comp = c
                    break

        if not comp:
            return {
                "company_name": company_identifier,
                "ubo_resolved": False,
                "message": "Company not located in jurisdictional corporate registries.",
                "effective_controllers": [],
            }

        # Multi-tier recursive resolution
        controllers: Dict[str, float] = {}  # Person Name -> Total Effective Equity %
        visited_corps = set()

        def _traverse(current_comp: Dict[str, Any], accumulated_factor: float):
            cid = current_comp["company_id"]
            if cid in visited_corps:
                return
            visited_corps.add(cid)

            for sh in current_comp.get("shareholders", []):
                equity = sh.get("equity_percent", 0.0) / 100.0
                effective_share = accumulated_factor * equity

                if sh.get("entity_type") == "INDIVIDUAL":
                    person = sh["name"].upper()
                    controllers[person] = controllers.get(person, 0.0) + effective_share
                else:
                    parent_id = sh.get("parent_id")
                    if parent_id and parent_id in self._registry:
                        _traverse(self._registry[parent_id], effective_share)

        _traverse(comp, 1.0)

        # Format output
        effective_controllers = [
            {
                "individual_name": person,
                "effective_equity_percent": round(share * 100.0, 2),
                "is_ubo_statutory": (share * 100.0) >= 25.0,
                "is_fractional_concealment": 0.0 < (share * 100.0) < 25.0 and len(comp.get("shareholders", [])) > 2,
            }
            for person, share in controllers.items()
        ]

        # Check directorship commonalities
        directors = comp.get("directors", [])

        return {
            "company_name": comp.get("name"),
            "company_id": comp.get("company_id"),
            "jurisdiction": comp.get("jurisdiction"),
            "ubo_resolved": len(effective_controllers) > 0,
            "effective_controllers": effective_controllers,
            "directors": directors,
            "shareholder_structure": comp.get("shareholders", []),
            "has_opaque_jurisdiction": comp.get("jurisdiction") in ["BVI", "PANAMA", "MARSHALL_ISLANDS", "COOK_ISLANDS"],
        }

    def check_shared_device_cluster(self, customer_id: str) -> Dict[str, Any]:
        """Detect synthetic identity rings sharing identical hardware fingerprints."""
        shared = aml_graph.find_shared_devices(customer_id)
        return {
            "customer_id": customer_id,
            "shared_identities_count": len(shared),
            "linked_entities": shared,
            "is_synthetic_ring": len(shared) >= 1,
        }


entity_tools = EntityTools()
