# Sentinel AML: diagrams (Mermaid)

Paste each block into https://mermaid.live (or any Mermaid viewer) and export PNG or SVG for Medium.

## 1. Architecture

```mermaid
flowchart TB
    SRC["Payment rails<br/>wires · ACH · cards · cash · P2P · crypto on-ramps"]

    subgraph ONPREM["On-premises / OpenStack enclave (raw PII never leaves)"]
        direction TB
        KAFKA["Kafka stream<br/>ISO 20022 canonical schema"]
        ING["Ingestion and normalization"]
        T1["Tier 1: rules engine<br/>sanctions · CTR · wires · velocity · FATF"]
        FS["Feature store<br/>Redis online + 30-day baselines"]
        KG[("Knowledge graph<br/>Neo4j / TigerGraph")]
        TOK["PII tokenization gateway<br/>HMAC-SHA256 tokens · vault stays on-prem"]
        HOLD["Ledger HOLD"]
        KAFKA --> ING
        ING --> T1
        ING --> FS
        ING --> KG
        T1 -- "hard stop" --> HOLD
        T1 -- "passed" --> TOK
    end

    subgraph GCP["Google Cloud enclave (tokens only)"]
        direction TB
        subgraph T2["Tier 2: ML and graph inference"]
            direction LR
            SUP["Supervised GBM"]
            AE["Autoencoder"]
            GR["Graph scorer"]
            BL["Model blender<br/>S_final = 0.4·S_sup + 0.3·S_ae + 0.3·S_graph"]
            XAI["SHAP-style attributions<br/>+ counterfactuals"]
            SUP --> BL
            AE --> BL
            GR --> BL
            BL --> XAI
        end
        GATE{"Triage gate"}
        subgraph T3["Tier 3: multi-agent swarm on GKE"]
            direction TB
            SUPV["Supervisor<br/>DAG planner"]
            ENT["Entity Resolution and KYC"]
            FOR["Transaction Forensics"]
            OS["OSINT and Adverse Media"]
            SAR["SAR Synthesis"]
            CRIT["Compliance Critic"]
            SUPV --> ENT
            SUPV --> FOR
            ENT --> OS
            ENT --> SAR
            FOR --> SAR
            OS --> SAR
            SAR --> CRIT
        end
        LAKE[("Lakehouse<br/>BigQuery / Cloud Storage")]
        MLOPS["MLOps: registry · drift · shadow validation"]
        BL --> GATE
        GATE -- "S_final ≥ 0.35" --> SUPV
    end

    subgraph T4["Tier 4: human in the loop"]
        direction TB
        CASE["Case manager"]
        COCK["Investigator cockpit"]
        ADJ["Approve / override<br/>mandatory reason code"]
        FIL["SAR submission gateway<br/>SHA-256 receipt"]
        CASE --> COCK --> ADJ --> FIL
    end

    AUDIT[("Cryptographic audit ledger<br/>SHA-256 hash chain")]

    SRC --> KAFKA
    TOK ==>|"private interconnect"| SUP
    TOK ==> GR
    TOK ==> AE
    GATE -- "S_final < 0.35" --> PASS["Approved, no alert"]
    CRIT --> CASE
    GATE -- "S_final ≥ 0.70" --> CASE
    T2 -.-> LAKE
    LAKE -.-> MLOPS
    ADJ -.-> AUDIT
    T1 -.-> AUDIT
    T2 -.-> AUDIT
    T3 -.-> AUDIT
```

## 2. End-to-end sequence

```mermaid
sequenceDiagram
    autonumber
    participant SRC as Payment source
    participant API as FastAPI
    participant PIPE as Data pipeline
    participant T1 as Tier 1 rules
    participant T2 as Tier 2 ML and graph
    participant TG as Triage gate
    participant SW as Swarm orchestrator
    participant SUP as Supervisor
    participant AG as Entity / Forensics / OSINT
    participant SAR as SAR synthesis
    participant CR as Compliance critic
    participant CM as Case manager
    actor AN as Analyst
    participant GW as SAR gateway
    participant L as Audit ledger

    SRC->>API: POST /api/transactions/ingest
    API->>PIPE: parse, update graph, hydrate features
    PIPE->>L: EVENT_INGRESS
    PIPE->>PIPE: tokenize PII, sink to lakehouse
    PIPE-->>API: raw txn + tokenized txn + features

    API->>T1: evaluate(raw txn)
    T1->>L: RULES_EXEC
    alt Hard stop (sanctions, embargo, auth burst)
        T1-->>API: HOLD
        API->>TG: build HOLD alert
        TG-->>API: alert (swarm bypassed)
    else Passed or soft flags
        API->>T2: score(tokenized txn)
        T2->>T2: GBM, autoencoder, graph, blend
        T2->>L: ML_SCORES
        T2-->>API: S_final, tier, typology, SHAP, counterfactual
        API->>TG: evaluate_gate()
        alt S_final < 0.35
            TG-->>API: no alert (approved)
        else S_final ≥ 0.35
            TG-->>API: alert (TRIAGING or ESCALATED_HUMAN)
            API->>SW: investigate_alert()
            alt Safe-degradation mode or circuit breaker open
                SW-->>API: degraded dossier, ESCALATED_HUMAN
            else Normal
                SW->>SUP: execute_investigation()
                SUP->>SUP: formulate 5-task DAG
                SUP->>AG: entity resolution (UBO, shared devices)
                SUP->>AG: forensics (dwell, pass-through, structuring)
                SUP->>AG: OSINT (adverse media, TBML) using resolved controllers
                AG-->>SUP: findings
                SUP->>SAR: synthesize narrative and activity codes
                SAR-->>SUP: draft SAR
                SUP->>CR: audit_narrative(draft, evidence)
                CR-->>SUP: approved?, groundedness, ungrounded claims
                SUP->>SUP: autonomous clearance?
                SUP->>L: AGENT_TRACE
                SUP-->>SW: dossier
                SW-->>API: dossier
            end
            API->>CM: create_case_from_dossier()
        end
    end

    AN->>CM: review dossier, graph, counterfactual, draft SAR
    alt Approve
        AN->>CM: approve_sar(notes, edited narrative)
        CM->>L: HUMAN_DECISION_APPROVE
        AN->>GW: submit_sar(case)
        GW->>L: REGULATORY_SUBMISSION
        GW-->>AN: filing receipt (SHA-256)
    else Override
        AN->>CM: override(reason code, justification)
        CM->>L: HUMAN_DECISION_OVERRIDE
    end
```

## 3. Case state machine

```mermaid
stateDiagram-v2
    [*] --> PASSED: Tier 1 clear and S_final < 0.35
    [*] --> HOLD: Tier 1 hard stop
    [*] --> TRIAGING: 0.35 ≤ S_final < 0.70
    [*] --> ESCALATED_HUMAN: S_final ≥ 0.70

    TRIAGING --> AUTO_CLEARED: swarm finds no severe evidence and S_final < 0.45
    TRIAGING --> ESCALATED_HUMAN: severe evidence, agent failure or circuit breaker

    ESCALATED_HUMAN --> SAR_APPROVED: analyst approves
    ESCALATED_HUMAN --> SAR_OVERRIDDEN: analyst overrides with reason code
    SAR_APPROVED --> [*]: submitted to regulator
    SAR_OVERRIDDEN --> [*]
    AUTO_CLEARED --> [*]
    PASSED --> [*]
    HOLD --> [*]
```

## 4. Agent task DAG

```mermaid
flowchart LR
    A["TASK_ENTITY<br/>Entity Resolution and KYC"] --> C["TASK_OSINT<br/>OSINT and Adverse Media"]
    A --> D["TASK_SAR<br/>SAR Synthesis"]
    B["TASK_FORENSICS<br/>Transaction Forensics"] --> D
    C --> D
    D --> E["TASK_CRITIC<br/>Compliance Critic"]
    E --> F{"Grounded<br/>≥ 0.90?"}
    F -- yes --> G["Dossier to case manager"]
    F -- no --> H["Flag ungrounded claims<br/>for analyst"]
```
