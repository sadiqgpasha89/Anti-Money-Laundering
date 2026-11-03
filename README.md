# Sentinel AML: Hybrid Architecture for Anti-Money Laundering

A production-grade, enterprise-scale Anti-Money Laundering (AML) platform designed for hybrid cloud deployments (**On-Premises OpenStack** and **Google Cloud Platform [GCP]**). The system implements a three-tier defense cascade combining ultra-low-latency deterministic rules, ensemble machine learning with topological Graph Neural Networks (GNN), and an autonomous cognitive multi-agent swarm.

---

## 1. Architectural Highlights

### 1.1 Hybrid Cloud Boundary (OpenStack + Google Cloud)
- **On-Premises / OpenStack Enclave**:
  - High-throughput distributed Kafka streaming ingestion (ISO 20022 canonical messages).
  - PII Tokenization & Scrubbing Gateway: deterministic HMAC/AES pseudonymization ensuring **zero raw customer PII** ever transits to the public cloud.
  - Sub-20ms Tier 1 Deterministic Rules Engine (Sanctions, statutory CTR thresholds, velocity gatekeepers).
  - Sensitive Property Knowledge Graph (TigerGraph/Neo4j on Ceph).
  - Dual Online/Offline Feature Store (Redis cache + historical baseline windows).
- **Public Cloud / Google Cloud Platform (GCP) Enclave**:
  - Google Kubernetes Engine (GKE Autopilot) running containerized Tier 3 agent microservices.
  - Tier 2 ML & Graph Inference Orchestrator (Supervised Gradient Boosting, Deep Reconstruction Autoencoders, Relational GCN/GAT topological learning).
  - Private Vertex AI Endpoints with Zero-Data-Retention guarantees for cognitive reasoning and SAR narrative drafting.
  - Vertex AI Vector Search for adverse media and customs commodity benchmarks.
  - BigQuery & Cloud Storage analytical lakehouse for continuous drift monitoring.
- **Safe Degradation Mode**: If connectivity drops between OpenStack and GCP, the system automatically falls back to local rules and baseline ML, buffering agent tasks in local Kafka queues without dropping regulatory reviews.

### 1.2 Cascade Defense Paradigm
1. **Tier 1: Deterministic Engine**: Sub-20ms SLA. Enforces statutory mandates, OFAC/UN/EU sanctions string matching (Jaro-Winkler, Levenshtein, Soundex), $10,000+ CTR thresholds, and velocity limits. Dispatches immediate ledger holds on sanctions matches.
2. **Tier 2: ML & Graph Inference**: Sub-100ms SLA. Combines Supervised GBM ($S_{supervised}$), Unsupervised Autoencoder ($S_{unsupervised}$), and Topological Graph Analytics ($S_{graph}$) into a calibrated composite score $S_{final}$. Generates local SHAP feature attributions and compliance counterfactuals.
3. **Tier 3: Multi-Agent Swarm**: Dispatches alerts with $S_{final} \ge 0.35$ to a hierarchical collective of 6 specialized agents:
   - **Supervisor Agent**: Formulates Directed Acyclic Graph (DAG) plan of execution.
   - **Entity Resolution & KYC Agent**: Traverses knowledge graph and unrolls recursive corporate UBO ownership trees ($C_{effective} = \prod M_{ownership}$).
   - **Transaction Forensics Agent**: Analyzes dwell times ($\Delta t < 120s$), pass-through throughput ratios ($\approx 1.0$), and peeling chains.
   - **External OSINT & Adverse Media Agent**: Queries adverse media vector databases and customs commodity benchmarks.
   - **SAR Synthesis Agent**: Auto-drafts FinCEN-compliant Suspicious Activity Report narratives and activity codes.
   - **Compliance Critic Agent**: Enforces factual entailment ($\forall c \in \text{Narrative}, \exists e \in \text{Dossier} \text{ s.t. Entailment}(e, c) \ge 0.90$) to eliminate hallucinations.
4. **Tier 4: Human-in-the-Loop Cockpit**: Compliance officers review the evidence dossier, graph topology, counterfactual explanations, and auto-drafted SAR, with 1-click regulatory submission to FinCEN or auditable override justification codes.

---

## 2. Multi-Dimensional 5-Tier Metrics Framework

System efficacy is continuously measured across 5 distinct dimensions:
1. **Business Impact**: Alert-to-SAR Conversion Rate ($>25\%$), Mean Time to Investigate (MTTI $<20$ min vs 240 min manual baseline), Cost per Resolved Alert, Net Labor Savings.
2. **System Engineering**: Latency percentiles (Tier 1 p99 $<20$ms, Tier 2 p99 $<100$ms), Throughput Capacity ($>10,000$ TPS), Cloud Interconnect Saturation.
3. **RAG Triad**: Context Relevance, Faithfulness / Groundedness, Answer / Narrative Completeness (5Ws regulatory coverage).
4. **Agentic & Cognitive**: Tool Invocation Precision/Recall, Plan Completion Rate, Reasoning Step Efficiency, Autonomous Clearance Accuracy, Critic Rejection Rate.
5. **Machine Learning**: Area Under PR Curve (PR-AUC), Precision@Top-K, Expected Calibration Error (ECE), Brier Score.

---

## 3. Structural Evasion Typologies Resolved (Section 10)

The platform includes targeted detection and agentic investigation for all 8 advanced money laundering typologies:
1. **Smurfing & Structuring**: Sub-$10,000 deposits across multi-branch smurfs caught via rolling feature velocity ratios and GAT fan-in aggregation.
2. **Rapid-Velocity Peeling Chains**: Fast pass-through sequences ($<120$s dwell time, $90\%+$ throughput ratio) isolated and collapsed into single investigative events.
3. **Sleeper and Mule Networks**: Dormant accounts seasoned $>12$ months that suddenly burst with volume, surfaced by Autoencoder reconstruction loss ($\mathcal{L}_{anomaly} > \gamma$).
4. **Synthetic Identity Rings**: Ghost identities cross-guaranteeing credit lines detected by multigraph clustering over shared digital footprints (IMEI, MAC, phone hashes).
5. **Fractional UBO Concealment**: Ownership partitioned into $<25\%$ holdings across offshore shell corporations unrolled by the Entity Resolution Agent ($C_{effective} = \prod M_{ownership}$).
6. **Crypto-to-Fiat Mixer Bridges**: Off-ramps from privacy mixers and non-compliant VASPs identified by forensics blockchain intelligence tooling.
7. **Trade-Based Money Laundering (TBML)**: Over-invoiced and under-invoiced commercial wires flagged by OSINT commodity benchmark pricing analysis.
8. **Adversarial ML Perturbations**: Transactions shaped near decision boundaries caught by ensemble diversity (Autoencoder + Supervised + Graph).

---

## 4. Quick Start & Execution

### Prerequisites
- Python 3.11+
- Virtual environment with dependencies from `requirements.txt`

### Setup & Run
```bash
# Create and activate environment
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run API and Web Mission Control UI
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
```

Open your browser to:
- **Investigator Cockpit UI**: `http://localhost:8080/`
- **Interactive OpenAPI Documentation**: `http://localhost:8080/docs`

### Running Tests & Benchmarks
```bash
# Full test suite with coverage
make test

# Unit tests
make test-unit

# Structural typologies edge-case tests
make test-edge

# Latency and performance SLA benchmarks (<20ms Tier 1, <100ms Tier 2)
make test-perf
```
