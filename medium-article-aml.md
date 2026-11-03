# Fighting Money Laundering with Agentic AI: A Four-Tier Architecture of Rules, ML, Graphs and Multi-Agent Investigators

### How Sentinel AML combines a sub-20 ms rules engine, an ML and graph ensemble, a swarm of six investigation agents, and a human sign-off, with a hybrid-cloud design that keeps customer PII on-premises.

Every bank runs the same experiment every day. It receives millions of transactions and has to decide, within milliseconds, which ones might be money laundering. It gets it wrong most of the time.

Legacy transaction monitoring relies on static rules such as "flag any cash deposit over $10,000". Industry estimates put the false-positive rate of such systems at 95% to 99%. Compliance analysts then spend most of their time copying data between systems instead of thinking. Meanwhile, launderers adapt. They split deposits to $9,500, move money through five accounts in 45 seconds, and hide ownership behind shell companies that each hold 24.5% of a firm, just under the 25% disclosure rule.

I built **Sentinel AML**, an open-source reference architecture that tackles this with a cascade of four tiers. Each tier uses the cheapest method that can handle the job, and escalates only what it cannot resolve:

1. **Tier 1:** a deterministic rules engine for statutory mandates and sanctions.
2. **Tier 2:** an ML and graph ensemble that scores everything that gets past the rules.
3. **Tier 3:** a swarm of six cooperating investigation agents for the alerts that matter.
4. **Tier 4:** a human compliance officer who makes every final decision.

The code is on GitHub: **github.com/sadiqgpasha89/Anti-Money-Laundering**

This article walks through the architecture, the data flow, each tier's internals, a step-by-step example, and, just as importantly, which parts of the repo are real implementation and which are simulated stand-ins for production infrastructure.

---

## The core idea: a cascade, not a single model

It is tempting to throw one big model at the problem. Regulated finance punishes that approach, for three reasons:

- **Cost and latency differ by orders of magnitude.** A string match takes microseconds. A graph neural network takes milliseconds. An LLM-driven investigation takes seconds to minutes. Running the expensive step on every transaction would be wasteful, and running only the cheap step would miss sophisticated laundering.
- **Some decisions must be deterministic.** A sanctions hit is not a probability. It is a legal obligation, and a regulator will ask which rule fired.
- **Accountability cannot be delegated to a model.** A suspicious activity report (SAR) is a legal filing. Someone qualified has to stand behind it.

So Sentinel routes every transaction through a funnel. Most are approved by Tier 1 and Tier 2 within milliseconds. A small fraction becomes an alert, and only those alerts reach the expensive agent swarm. Only a human can file.

---

## The architecture at a glance

```
 Payment rails (wires, ACH, cards, cash, P2P, crypto on-ramps)
        │
 ┌──────▼────────── ON-PREMISES / OPENSTACK ──────────────────────┐
 │  Kafka stream (ISO 20022 canonical schema)                      │
 │     │                                                           │
 │     ├─► Tier 1: rules engine ── sanctions · CTR · velocity      │
 │     │        └─ hard stop ──► ledger HOLD                       │
 │     ├─► Feature store (Redis + historical baselines)            │
 │     ├─► Knowledge graph (Neo4j / TigerGraph)                    │
 │     └─► PII tokenization gateway (HMAC tokens, vault on-prem)   │
 │                                                                 │
 │  Crypto audit ledger: every step hashed into one chain          │
 └────────────────────────────┬────────────────────────────────────┘
                              │ tokens only, over private interconnect
 ┌────────────────────────────▼─────────── GOOGLE CLOUD ──────────┐
 │  Tier 2: ML + graph inference                                   │
 │     supervised GBM · autoencoder · graph scorer → S_final       │
 │     SHAP-style attributions · counterfactuals                   │
 │            │                                                    │
 │   Triage gate: S_final < 0.35 pass · ≥ 0.35 alert · ≥ 0.70 high │
 │            │                                                    │
 │  Tier 3: agent swarm on GKE (Vertex AI for reasoning)           │
 │     Supervisor ► Entity/KYC ┐                                   │
 │                ► Forensics  ├► OSINT ► SAR Synthesis ► Critic   │
 │  Lakehouse (BigQuery) · drift monitoring · model registry       │
 └────────────────────────────┬────────────────────────────────────┘
                              ▼
        Tier 4: investigator cockpit ► approve / override ► regulator
```

Two design decisions shape everything else.

**1. A hybrid-cloud boundary built around data sovereignty.** Steady, high-volume work such as streaming ingestion, rules, feature caches and the graph runs on-premises on OpenStack, where costs are predictable. Burst-heavy work such as agent reasoning and model retraining runs on Google Cloud, where you pay only while investigations are active. The boundary exists mainly for compliance: raw names, national IDs and account numbers never cross it. A **tokenization gateway** replaces them with deterministic tokens first.

**2. Safe degradation.** If the link between the two environments drops, the on-premises side keeps screening with the rules and baseline models. Alerts that would have gone to the agent swarm are buffered in local queues instead of being dropped. No regulatory review is lost; it is only delayed.

---

## The data layer

### A canonical transaction

Everything that enters the system is normalized into one Pydantic model modeled on ISO 20022. It covers **11 payment channels**: SWIFT wire, domestic ACH, instant ACH, card-not-present, card-present, cash deposit, P2P transfer, cross-border wire, crypto-to-fiat on-ramp, commercial letter of credit and corporate payroll. It carries the sender and receiver profiles (tenure, historical monthly volume, risk rating, PEP and sanctions flags), plus device telemetry such as device ID, MAC address, phone hash, geohash and failed-authentication count.

Every decision uses one of **8 status values**: `PASSED`, `HOLD`, `TRIAGING`, `AUTO_CLEARED`, `ESCALATED_HUMAN`, `SAR_APPROVED`, `SAR_OVERRIDDEN` and `REJECTED`. A closed set of states makes the audit trail and the metrics unambiguous.

### Privacy by tokenization

The tokenizer turns each identifier into a keyed hash, with the PII type mixed in:

`token = "TOK_" + type + "_" + HMAC-SHA256(secret, type + ":" + normalized_value)[:12]`

The same input always produces the same token, so graph relationships and joins survive. A customer who appears in 50 transactions is still one node. But the cloud side sees only tokens. The reverse-lookup vault stays inside the on-premises boundary, and only the investigator cockpit can resolve a token back to a name.

### The feature store

The feature store keeps a rolling 30-day window per account and computes **15 online features** on demand, among them:

- volume and count over 1 hour, 24 hours and 7 days
- the ratio of 1-hour volume to the 30-day baseline, and 24-hour volume to the daily baseline
- the amount's z-score against the account's own history
- **geolocation entropy**, `H = −Σ p·log₂(p)` over the account's geohashes, normalized to 0–1
- a tenure-adjusted deviation that doubles the weight for accounts younger than six months

Seven of these form the feature vector used by the ML models.

### The knowledge graph

A heterogeneous directed multigraph (NetworkX in this reference build, Neo4j or TigerGraph in the target design) holds five node types: **Customer, Account, Device, LegalEntity and PhysicalAddress**. It has four edge types: **Transacted, Owns, SharedDevice and AssociatedAddress**. Graph methods find shared devices across customers, detect circular fund flows, trace peeling chains hop by hop, and compute clustering coefficient and PageRank.

### The audit ledger

Every stage writes to a **cryptographic hash chain**. Each block stores the hash of its payload and the hash of the previous block:

`current_hash = SHA-256(index : timestamp : event_type : payload_hash : previous_hash : actor)`

Change any historical record and every later hash breaks. A `verify` endpoint walks the chain from genesis and reports the first corrupted block. The recorded events follow the whole lifecycle: ingress, rules execution, ML scores, agent trace, human decision and regulatory submission.

---

## Tier 1: deterministic rules (target: under 20 ms)

Tier 1 runs six checks entirely in memory:

- **Sanctions screening** of both sender and receiver, using three string-matching techniques together. **Jaro-Winkler** similarity (hard-stop threshold 0.88) catches typos and transposed letters. **Soundex** adds a small phonetic bonus so that "Korolev" and "Korolyov" are treated as close. Every alias on a watch-list entry is checked too.
- **Embargoed jurisdictions** (North Korea, Iran, Syria) are an automatic hard stop.
- **Statutory CTR threshold:** a cash deposit of $10,000 or more triggers mandatory reporting. This is a flag, not a freeze.
- **High-value wires:** cross-border wires of $500,000 or more get priority review.
- **Failed-authentication bursts:** five or more failures is a hard stop.
- **FATF high-risk jurisdictions:** flagged, with North Korea and Iran treated as hard stops.

Each hit is a typed `RuleHit` with a rule ID, a confidence, a human-readable description and the trigger value. If any hit is a hard stop, the transaction gets status `HOLD` and an alert is raised immediately. In the target design that status freezes the payment at the core-banking ledger, and Tier 2 and Tier 3 cannot override it.

---

## Tier 2: the ML and graph ensemble

Three independent models each answer a different question:

- **Supervised gradient boosting** asks: *does this look like laundering I have seen before?* It is a 50-tree classifier over the seven-feature vector.
- **An autoencoder** asks: *is this unlike anything normal?* It is a 7→4→2→4→7 network trained only on normal behavior. Its reconstruction error, normalized against the baseline error distribution and passed through a sigmoid, becomes an anomaly score. This is what catches zero-day patterns and sleeper accounts that have no labeled examples.
- **A graph scorer** asks: *does the surrounding network look wrong?* It combines shared-device rings, circular flows, peeling-chain indicators, fan-in/fan-out hubs, clustering coefficient and PageRank.

The blender combines them:

`S_final = 0.40 × S_supervised + 0.30 × S_unsupervised + 0.30 × S_graph`

Diversity is the point. A launderer who perturbs features to slip under the supervised model's decision boundary (typology 8 below) still shows up as a systemic shift to the autoencoder.

### The triage gate

`S_final` drives the routing:

- **Below 0.35:** approved with no alert. This is the vast majority of traffic.
- **0.35 to 0.70:** an alert in `TRIAGING`, sent to the agent swarm for autonomous evaluation.
- **0.70 and above:** escalated to a human, with the swarm still running to assemble the evidence. At 0.85 and above the tier is `CRITICAL`.

### Explainability

A score alone is not acceptable in a regulated setting. For every score the engine produces per-feature contributions (a SHAP-style approximation weighted by the model's feature importances) and a plain-language **counterfactual**: *the risk score falls below the investigation threshold if the transaction amount drops below $X and 1-hour turnover stays below $Y with zero authorization failures.* Counterfactuals help analysts understand a decision and help regulators see that the model is not a black box.

---

## Tier 3: the agent swarm

Alerts above the threshold go to a **Supervisor agent**, which writes an execution plan as a directed acyclic graph (DAG) of five tasks with explicit dependencies:

- **Entity Resolution and KYC** has no dependencies.
- **Transaction Forensics** has no dependencies.
- **External OSINT** depends on Entity Resolution, because it needs to know who the real controllers are before searching for them.
- **SAR Synthesis** depends on all three.
- **Compliance Critic** depends on SAR Synthesis.

Each agent is a small specialist with its own toolset.

### 1. Entity Resolution and KYC agent

This agent attacks identity and ownership concealment with three tools:

- **Shared-device clustering** finds other customers authenticating from the same device. One or more links flags a possible synthetic-identity ring.
- **The UBO unroller** recursively walks the corporate registry and computes effective indirect ownership as the product of stakes along each path, `C_effective = Π M_ownership`, summing the results per individual. This defeats the "fractional UBO" trick. In the sample registry, a BVI company is held by four shells (Panama, Marshall Islands, Cyprus, Cook Islands) at 24.5%, 24.5%, 24% and 27%, so no shell crosses a naive disclosure threshold at the first level. Unrolling the tree shows that **one individual controls 100% of the structure**.
- **Subgraph metrics** pull the account's degree, clustering and PageRank.

### 2. Transaction Forensics agent

This agent reads fund-flow behavior:

- **Dwell time**: how long money sits before moving on (under 120 seconds is suspicious).
- **Pass-through ratio**: how much of the inflow leaves again (above 0.90 suggests layering).
- Dwell time plus pass-through together flag a **peeling chain**.
- **Circular loops** and **sub-threshold structuring** (deposits between $9,000 and $9,999) round out the checks.

### 3. OSINT and Adverse Media agent

This agent searches adverse-media records for the sender, the receiver and every controller that the entity agent unmasked. It also checks **trade-based money laundering** by comparing invoiced prices to commodity benchmarks:

`Δ_price = |P_invoiced − P_benchmark| / P_benchmark`, flagged when it exceeds the 25% tolerance.

In the sample data, processors invoiced at $600 per unit against a $125 benchmark give a 380% deviation, flagged as over-invoiced.

### 4. SAR Synthesis agent

This agent assembles a five-part, FinCEN-style narrative: executive summary, typology and pattern, entity and ownership, adverse intelligence, and regulatory conclusion. It maps the inferred typology to suspicious activity codes (for example structuring, rapid movement of funds, shell-company concealment, TBML), builds a timeline of events, and lists accounts and counterparties.

### 5. Compliance Critic agent

This is the guardrail against hallucination. It splits the narrative into individual claims and checks each one against the evidence in the dossier. The design goal is:

`∀ claim c in the narrative, ∃ evidence e in the dossier with Entailment(e, c) ≥ 0.90`

A draft is approved only if enough of its claims are grounded. Anything else goes back as "needs revision" with the list of ungrounded statements.

### Autonomous clearance and fault tolerance

The Supervisor can clear a case on its own, but only under a narrow rule: **no severe evidence** (no synthetic ring, no fractional UBO, no peeling chain, no smurfing structure, no adverse media, no TBML flag) **and** `S_final` below 0.45. Everything else is escalated.

A **circuit breaker** protects the swarm itself. After three consecutive agent failures, or whenever safe-degradation mode is on, the orchestrator stops calling agents and routes alerts straight to a human with the reason attached. A broken agent can slow the process down, but it can never make it silently drop a case.

---

## Tier 4: the human in the loop

Every escalated alert becomes a **case** holding the full dossier, the draft SAR and the critic's findings. The analyst has two actions:

- **Approve:** optionally edit the narrative, add notes, and sign off. The SAR is marked human-approved, and the analyst's identity is written to the audit chain.
- **Override:** reject the system's recommendation, but only with a mandatory reason code (for example a known legitimate business, or insufficient evidence) and written justification. Overrides are logged just like approvals, so the organization can later study where and why people disagreed with the machine.

Only a case in `SAR_APPROVED` state can be submitted. The submission gateway builds the regulatory payload and a SHA-256 filing receipt, and records the submission in the ledger. The system can clear obvious false positives with an auditable rationale, but **it can never file a SAR without a human approval**. That boundary is enforced in code, not by convention.

---

## Step by step: two transactions through the system

I ran the 11 seed transactions through the pipeline. Here are two of them.

### A sanctions hit

`TXN-SANC-001`: a $45,000 SWIFT wire from a person whose name matches an OFAC SDN entry.

1. The ingestor normalizes the payload into the canonical model.
2. The pipeline updates the graph and feature store, and writes an `EVENT_INGRESS` block to the ledger.
3. Tier 1 screens both parties. The sender matches the sanctions list (rule `RULE_SANC_001`, a hard stop) and also trips the high-risk-jurisdiction rule.
4. The status becomes `HOLD`. The triage gate creates a sanctions alert immediately, and the swarm is bypassed because the decision is statutory, not probabilistic.

### A rapid-velocity peeling chain

`TXN-PEEL-001`: a $185,000 instant ACH payment from a logistics company, with a 45-second dwell time and a 0.98 throughput ratio.

1. **Pipeline:** the transaction is added to the graph, features are computed, the PII is tokenized, and the tokenized version is sunk to the lakehouse.
2. **Tier 1:** no rule fires, so the status is `PASSED`. A static rule sees nothing wrong here, which is exactly the problem.
3. **Tier 2:** supervised 0.87, autoencoder 1.00, graph 0.82. `S_final = 0.4×0.87 + 0.3×1.00 + 0.3×0.82 = 0.894`, so the tier is **CRITICAL** and the action is escalation.
4. **Triage:** an alert is created and the swarm is dispatched.
5. **Supervisor:** builds the five-task DAG. Entity and Forensics run first.
6. **Forensics:** dwell time 45 s (under 120 s) and throughput 0.98 (above 0.90) flag a **peeling chain**.
7. **OSINT:** searches media for the sender, receiver and any resolved controllers.
8. **SAR Synthesis:** drafts the narrative and maps the typology to activity codes such as rapid movement of funds and peeling-chain layering.
9. **Critic:** checks the narrative against the evidence. In my run the groundedness score was 0.92 and the draft was approved.
10. **Determination:** severe evidence is present, so the case is `ESCALATED_HUMAN`.
11. **Case manager:** creates a case with the dossier and draft SAR.
12. **Analyst:** reviews in the cockpit, approves or overrides, and the decision is hashed into the ledger. If approved, the gateway submits the filing and returns a SHA-256 receipt.

Across all 11 seed transactions, one benign grocery purchase passed, one sanctions case was held, and nine suspicious cases were escalated, covering all eight typologies. The ledger verified as intact after the run.

---

## The sequence flow

```
 Pipeline        Tier 1          Tier 2          Swarm          Analyst
    │ 1. ingest,     │               │               │               │
    │    graph,      │               │               │               │
    │    features    │               │               │               │
    │ 2. raw txn     │               │               │               │
    │───────────────►│               │               │               │
    │                │ 3. rules      │               │               │
    │◄── HOLD ───────│  hard stop?   │               │               │
    │  (stop here)   │               │               │               │
    │ 4. tokenized txn (no raw PII)  │               │               │
    │───────────────────────────────►│               │               │
    │                │               │ 5. score,     │               │
    │                │               │    triage     │               │
    │                │               │ < 0.35: pass  │               │
    │                │               │ 6. alert ────►│               │
    │                │               │               │ 7. plan DAG   │
    │                │               │               │    entity +   │
    │                │               │               │    forensics, │
    │                │               │               │    then OSINT │
    │                │               │               │ 8. draft SAR  │
    │                │               │               │ 9. critic     │
    │                │               │               │ 10. dossier ─►│
    │                │               │               │               │ 11. review
    │                │               │               │               │  approve or
    │                │               │               │               │  override
    │                │               │               │               │ 12. submit
 ═══╧════════════════╧═══════════════╧═══════════════╧═══════════════╧═══
   Every step appends a block to the SHA-256 audit ledger
```

The Mermaid source for the architecture diagram, a full UML-style sequence diagram and the case state machine is in `aml-diagrams.md` in the repo, ready to export as images.

---

## Governance: making it auditable

Financial regulators care less about how clever a system is than whether it can be explained and controlled. The repo includes the scaffolding for that.

### Model risk management

A **model registry** tracks each model's version, type (supervised, autoencoder, graph), status (champion, challenger, shadow, retired), training-data hash and parameters, in the spirit of the Federal Reserve's SR 11-7 guidance. A **shadow validator** compares a challenger to the champion on live traffic and flags any transaction where `|S_champion − S_challenger|` exceeds a tolerance of 0.15, so reviewers can see whether the challenger finds new patterns or just adds false positives.

### Drift detection

A drift detector watches three kinds of change:

- **Covariate drift:** the **Population Stability Index** (below 0.10 is stable, 0.10 to 0.25 is moderate, above 0.25 triggers retraining) and the **Wasserstein distance** for each feature.
- **Concept drift:** the **Page-Hinkley** sequential test on the error series.
- **Recommended action:** stable, inspect distributions, or recalibrate.

### A five-dimension metrics framework

Performance is measured on five axes, not one:

- **Business:** alert-to-SAR conversion, mean time to investigate against a 240-minute manual baseline, cost per alert, labor savings.
- **System:** latency percentiles (p50/p95/p99), throughput, interconnect saturation.
- **RAG triad:** context relevance, faithfulness, and narrative completeness (the "5 Ws": who, what, when, where, why).
- **Agentic:** plan completion rate, critic rejection rate, tokens per tool call, autonomous clearance accuracy.
- **ML:** PR-AUC, precision at top-K, expected calibration error and Brier score. PR-AUC matters more than accuracy here because laundering is rare.

### Prompt governance

Agent prompts are versioned templates with a groundedness benchmark and one-call rollback to a certified earlier version, so a bad prompt change can be reversed instantly.

---

## The eight typologies it is designed to catch

1. **Smurfing and structuring:** deposits kept just under $10,000 across several people and branches.
2. **Rapid-velocity peeling chains:** funds hopping through accounts in seconds, peeling off small slices.
3. **Sleeper and mule networks:** dormant accounts that suddenly move large volumes.
4. **Synthetic identity rings:** fabricated identities that share devices and transact in circles.
5. **Fractional UBO concealment:** ownership split across offshore shells, each holding under 25%.
6. **Crypto-to-fiat mixer bridges:** proceeds from mixers off-ramped into fiat.
7. **Trade-based money laundering:** over- or under-invoiced goods that move value across borders.
8. **Adversarial ML perturbations:** transactions shaped to sit just beneath a model's decision boundary.

Each has a one-click simulation in the cockpit that sends a seeded example through all four tiers.

---

## Interfaces and tech stack

The platform exposes **29 REST endpoints across 9 routers** (FastAPI): transaction ingestion and stream, pipeline inspection, model scoring and counterfactuals, agent investigation and traces, case management (list, get, approve, override, submit), metrics for all five dimensions, MLOps (models, drift, shadow), the typology catalog and simulator, and audit chain retrieval and verification. A browser **investigator cockpit** has seven tabs: live stream, cases, agent swarm, metrics, MLOps, typologies and audit.

- **Language:** Python 3.11+
- **API:** FastAPI, Uvicorn, Pydantic v2
- **ML and graph:** scikit-learn, NumPy, SciPy, pandas, NetworkX
- **Design targets:** Kafka, Redis, Neo4j or TigerGraph, Ceph, OpenStack, GKE Autopilot, Vertex AI, Vertex AI Vector Search, BigQuery
- **Tests:** pytest, pytest-cov, with 50 tests across unit, integration, typology edge-case and latency suites

The Python source is about 5,000 lines in a layered layout: `core`, `data_engineering`, `datascience` (tier 1 and tier 2), `agents` (with `tools`), `hitl`, `mlops`, `llmops`, `metrics` and `api`.

To run it:

```
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn src.api.main:app --port 8080
```

Open `http://localhost:8080/` for the cockpit and `/docs` for the API.

---

## What is real, and what is simulated

A reference architecture is only useful if you know which parts you can trust. Here is the honest picture of the current repo.

**Implemented and tested:**

- The full tier cascade and triage logic, end to end, in code
- The sanctions matcher (Jaro-Winkler, Soundex, aliases), CTR, wire, velocity and jurisdiction rules
- The feature store, knowledge graph, tokenizer and cryptographic audit chain, including tamper detection
- The recursive UBO unroller, TBML price check, SAR code mapping and SAR payload builder
- The human approve and override workflow, with the state machine enforced
- PSI, Wasserstein, Page-Hinkley, ECE and Brier calculations
- The circuit breaker and safe-degradation fallback
- 50 automated tests, all passing

**Simulated stand-ins for production infrastructure:**

- Kafka, Redis, Neo4j or TigerGraph, BigQuery and Vertex AI are represented by in-memory structures and JSON files. The lakehouse sink is a list. Adverse-media search is keyword matching over a small file.
- The supervised and autoencoder models are real scikit-learn models, but they are fitted at startup on synthetic data, not trained on real labeled transactions.
- The "graph neural network" is a rule-weighted topological scorer, not a trained RGCN or GAT.
- The six "agents" are deterministic Python components calling tools. The repo does not yet call an LLM. Prompt templates are registered but not yet wired to a model, and the token counts in the dossier are placeholders.
- The Compliance Critic currently checks claims by lexical overlap with the evidence, not by true entailment with an NLI model, and the pass mark is a fraction of grounded claims.
- The dashboard's business, RAG and throughput numbers are seeded sample values. They are not measurements, and the 10,000 TPS and 20-minute investigation figures are design targets, not benchmarks. The in-process latency tests show the logic is fast on tiny models, which says nothing about production throughput.
- The demo seed data carries scenario labels, and the typology inference uses them. With the labels removed, the demo's Tier 2 stops distinguishing typologies. That tells me the next step is training on real or realistic labeled data, not tuning thresholds.
- The regulator "acceptance" in the submission gateway is simulated.

Writing this article also exposed a real bug at the tokenization boundary, which I have since fixed. Tier 2 and the agents receive the tokenized transaction, but the graph and the feature store were keyed by raw identifiers. Every lookup made with a token came back empty. The graph score of a smurfing transaction dropped from 0.85 to 0.05, and the agents could not resolve a single company registry entry or adverse-media hit for a tokenized name. The pipeline now tokenizes first and keys the graph and the feature store by token. The agents' registry and media tools resolve tokens at the tool boundary, which models the on-premises side of the design. Four regression tests cover it, and fixing it also exposed a small double-counting error in the feature store, now covered by its own test. It is a good example of why tokenization boundaries need integration tests, and why a demo that "works" can hide a broken data path.

---

## What I would build next

- **Real agents.** Replace the deterministic agent bodies with LLM-driven tool-using agents (planning, tool selection, self-correction) on a private, zero-data-retention endpoint, keeping the existing DAG, tools and circuit breaker as the control plane.
- **A real critic.** Use an entailment model or a cross-encoder to verify each claim against specific evidence snippets, and report a score per claim, as the design specifies.
- **A trained graph model.** Train an RGCN or GAT on a realistic transaction graph, and key the graph by token from the start.
- **Real data and evaluation.** Use labeled or realistic synthetic data with temporal backtesting, and report PR-AUC, precision at K and calibration from actual runs.
- **Real infrastructure.** Kafka with partitioning by customer, Redis for online features, a graph database, persistent case storage, authentication and role separation for the cockpit, and WORM storage for the ledger.
- **LLMOps in the loop.** Wire in the cost tracker, trace logger and evaluation harness so every agent step is traced, costed and scored.

---

## What I learned

1. **Put the cheap, certain things first.** Rules handle laws; models handle patterns; agents handle context. Matching the method to the question is what keeps cost and latency under control.
2. **Make disagreement visible.** Three different models, a champion and a challenger, and a critic that argues with the writer all exist to expose errors early.
3. **Guardrails around AI beat trust in AI.** The circuit breaker, the narrow auto-clear rule and the human-only filing gate mean a failure degrades the system gracefully instead of silently.
4. **Auditability is a feature, not a log file.** A hash chain, model versions, counterfactuals and override codes are what let an institution defend a decision years later.
5. **Be honest about what is simulated.** A clearly labeled prototype is a foundation. An unlabeled one is a liability.

Financial crime detection is, at heart, an orchestration problem: the right method at the right stage, with a human accountable at the end. That is the idea behind Sentinel AML.

Explore the code, run the eight typology simulations, and let me know what you would change: **github.com/sadiqgpasha89/Anti-Money-Laundering**
