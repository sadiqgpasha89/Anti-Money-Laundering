"""Structural Evasion Typologies Sandbox routes (Section 10)."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from src.core.config import settings
from src.data_engineering.ingestion import transaction_ingestor
from src.api.routes.transactions import ingest_transaction
from fastapi import BackgroundTasks

router = APIRouter(prefix="/api/typologies", tags=["Structural Evasion Typologies"])

TYPOLOGY_CATALOG = [
    {
        "id": 1,
        "key": "SMURFING_STRUCTURING",
        "title": "Structuring & Smurfing (Sub-Threshold Optimization)",
        "adversarial_pattern": "Laundering networks distribute large cash volumes into numerous deposits under statutory CTR threshold ($9,500 vs $10,000) using confederate smurfs across disparate branches.",
        "resolution_tier": "Feature Store Rolling Aggregation & GAT Graph Neighborhood",
        "resolution_details": "Tier 1 static rules miss sub-$10k deposits. The Streaming Feature Store aggregates cross-branch velocities and the Graph Neural Network isolates the fan-in structure to the central aggregation account.",
        "seed_id": "TXN-SMURF-001",
    },
    {
        "id": 2,
        "key": "RAPID_VELOCITY_PEELING_CHAINS",
        "title": "Rapid-Velocity Peeling Chains (Layering Sequences)",
        "adversarial_pattern": "Funds break up through transient multi-hop accounts within seconds (<120s dwell time) with 90%+ throughput ratio, peeling off small fractions at each hop.",
        "resolution_tier": "Graph Analytics Engine & Transaction Forensics Agent",
        "resolution_details": "Calculates low account dwell time (Δt < 120s) and high balance throughput ratio. Forensics agent traces and collapses the entire sequence into a single investigative event.",
        "seed_id": "TXN-PEEL-001",
    },
    {
        "id": 3,
        "key": "SLEEPER_MULE_NETWORKS",
        "title": "Sleeper and Mule Networks (Aged Account Activation)",
        "adversarial_pattern": "Dormant accounts seasoned >12 months with low historical balances suddenly burst with massive transfers before being abandoned.",
        "resolution_tier": "Unsupervised Reconstruction Autoencoder & Entity Resolution",
        "resolution_details": "Static rules fail due to account historical tenure. Unsupervised Autoencoder flags severe reconstruction error on velocity-to-tenure profile (L_anomaly > gamma).",
        "seed_id": "TXN-SLEEP-001",
    },
    {
        "id": 4,
        "key": "SYNTHETIC_IDENTITY_RINGS",
        "title": "Synthetic Identity Rings (Ghost Entities with Circular Linkage)",
        "adversarial_pattern": "Fabricated identities cross-guarantee credit and transact circularly while sharing digital footprints (IMEI, MAC, phone hashes).",
        "resolution_tier": "Heterogeneous Graph Engine & GNN Clustering",
        "resolution_details": "The multigraph maps shared physical infrastructure across nominally unrelated accounts, flagging high clustering coefficients (C_v) across synthetic rings.",
        "seed_id": "TXN-SYNTH-001",
    },
    {
        "id": 5,
        "key": "FRACTIONAL_UBO_CONCEALMENT",
        "title": "Fractional UBO Concealment (The <25% Shell Strategy)",
        "adversarial_pattern": "Corporate ownership partitioned into 24.5% / 12.5% holdings across offshore shell corporations (BVI, Panama) to evade the 25% KYC disclosure rule.",
        "resolution_tier": "Entity Resolution & KYC Agent (Recursive UBO Unroller)",
        "resolution_details": "Agent recursively queries corporate registries, traversing parent-subsidiary trees to calculate Effective Indirect Control: C_effective = prod(M_ownership), revealing the true beneficial owner.",
        "seed_id": "TXN-UBO-001",
    },
    {
        "id": 6,
        "key": "CRYPTO_TO_FIAT_BRIDGES",
        "title": "Crypto-to-Fiat Nested Exchanges and Mixer Bridges",
        "adversarial_pattern": "Illicit crypto proceeds routed through privacy mixers and off-ramped into fiat via P2P payment processors or unregistered nested VASPs.",
        "resolution_tier": "Forensics Agent & Ingestion Blockchain Intelligence",
        "resolution_details": "Forensics agent cross-references off-ramp counterparties against non-compliant VASP registers and unhosted wallet telemetry, flagging privacy mixer off-ramps.",
        "seed_id": "TXN-CRYPTO-001",
    },
    {
        "id": 7,
        "key": "TRADE_BASED_MONEY_LAUNDERING",
        "title": "Trade-Based Money Laundering (TBML) via Invoice Manipulation",
        "adversarial_pattern": "High-value cross-border commercial wire transfers disguised via over-invoiced or under-invoiced goods (e.g. $600/unit vs $125 benchmark).",
        "resolution_tier": "External OSINT Agent & Commodity Benchmark Verifier",
        "resolution_details": "OSINT agent parses customs trade manifests and calculates pricing deviation against international benchmarks: Delta_price = |P_inv - P_bm| / P_bm > tolerance, detecting phantom value transfers.",
        "seed_id": "TXN-TBML-001",
    },
    {
        "id": 8,
        "key": "ADVERSARIAL_ML_PERTURBATIONS",
        "title": "Adversarial Machine Learning Perturbations (Model Gaming)",
        "adversarial_pattern": "Laundering syndicates shape transactions to sit barely beneath classifier decision boundaries and mimic normal corporate payroll profiles.",
        "resolution_tier": "Ensemble Diversity (Autoencoder + Supervised) & Model Blender",
        "resolution_details": "Even if probe transactions perturb tabular features to evade the supervised tree, the unsupervised autoencoder flags the underlying systemic shift, preventing model evasion.",
        "seed_id": "TXN-ADVML-001",
    },
]


@router.get("/catalog")
def get_typology_catalog() -> List[Dict[str, Any]]:
    """Retrieve catalog of all 8 structural evasion typologies."""
    return TYPOLOGY_CATALOG


@router.post("/simulate/{typology_id}")
def simulate_typology(typology_id: int) -> Dict[str, Any]:
    """1-Click execution of an evasion typology simulation through Tiers 1, 2, and 3."""
    target = next((t for t in TYPOLOGY_CATALOG if t["id"] == typology_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Typology ID {typology_id} not found.")

    # Find matching seed transaction
    txns = transaction_ingestor.load_seed_transactions(str(settings.SEED_TRANSACTIONS_PATH))
    seed_txn = next((t for t in txns if t.transaction_id == target["seed_id"]), None)

    if not seed_txn:
        raise HTTPException(status_code=404, detail=f"Seed transaction '{target['seed_id']}' not found.")

    # Ingest and execute full pipeline
    result = ingest_transaction(seed_txn.model_dump(), BackgroundTasks())

    return {
        "typology": target,
        "simulation_result": result,
    }
