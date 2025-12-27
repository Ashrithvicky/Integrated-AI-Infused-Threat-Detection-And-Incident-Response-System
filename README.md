# Integrated AI-Infused Threat Detection and Incident Response System

## Abstract

Cloud infrastructures have become highly dynamic, distributed, and identity-driven. Traditional security systems, built around static rules or isolated telemetry streams, struggle to detect modern attacks that unfold gradually across identities, endpoints, networks, and configurations.

This project introduces an **Integrated AI-Infused Threat Detection and Incident Response System** that unifies **behavioral analytics, machine learning, graph correlation, sequence modeling, and automated response** into a single real-time security intelligence platform. The system is designed to observe how behavior evolves, correlate signals across domains, and respond safely before damage propagates.



## Why This System Matters

Modern cloud breaches are rarely loud. Attackers exploit:

* legitimate credentials
* slow privilege escalation
* subtle configuration drift
* short-lived infrastructure
* distributed attack paths

This system addresses the **fundamental gap**:

> security tools detect events, but fail to understand **intent, sequence, and relationship**.

By treating security as a **behavioral and relational problem**, this system enables:

* earlier detection
* fewer false positives
* explainable alerts
* safer automation
* scalable cloud adoption with confidence



## High-Level Architecture

1. **Telemetry ingestion** from cloud, endpoint, network, identity, and external intelligence
2. **Normalization & feature extraction**
3. **Parallel detection engines** (UEBA, EDR, NDR, sequence, rules, graph)
4. **Fusion & adaptive risk scoring**
5. **Explainable alerting & automated response**
6. **Continuous learning & feedback**



## Technologies Used

* **Python** for core services and ML pipelines
* **FastAPI** for model and service APIs
* **PyTorch** for sequence and deep learning models
* **Scikit-learn** for anomaly detection (Isolation Forest)
* **Graph analytics / GNN-style scoring**
* **Redis** for session state and streaming context
* **MySQL** for structured persistence
* **SHAP-style explainability**
* **Federated learning architecture** (client-server)



## The 20 Core Features (Mapped Exactly to Your List)

### 1. SIEM-Compatible Distributed Ingestion

Ingests logs from cloud platforms, endpoints, and network sources, enabling centralized analysis without losing source context.

**Impact**: Removes visibility silos.



### 2. UEBA Behavioral Features

Learns normal user and service behavior over time using unsupervised ML to detect subtle deviations.

**Impact**: Detects credential misuse and insider threats early.



### 3. Threat Intelligence System (Doubt-Based)

External threat intelligence is used conservatively, influencing risk only when corroborated by internal behavior.

**Impact**: Prevents false positives from noisy feeds.



### 4. Log Template Mining

Discovers recurring log patterns automatically, identifying deviations without handcrafted rules.

**Impact**: Scales across unknown workloads.



### 5. Sequence Modeling Features

Uses action order and temporal context to detect multi-stage attacks rather than single anomalies.

**Impact**: Detects slow, stealthy attacks.



### 6. Endpoint Behavior Detection (EDR)

Monitors endpoint actions such as process behavior and file access patterns.

**Impact**: Detects compromised hosts and lateral movement.



### 7. Network Detection Features (NDR)

Analyzes network flows for abnormal access paths and data movement.

**Impact**: Exposes east-west traffic abuse and exfiltration.



### 8. Configuration Drift Detection

Tracks infrastructure configuration changes and flags risky or unexpected deviations.

**Impact**: Prevents silent misconfiguration-based breaches.



### 9. Graph-Based Correlation

Builds an evolving graph of users, resources, services, and interactions.

**Impact**: Reveals hidden relationships attackers must traverse.



### 10. Fusion Model (Contrastive / Multimodal)

Combines outputs from all detectors into a single risk score using weighted evidence.

**Impact**: Eliminates single-point decision failures.



### 11. Adaptive Machine Learning

Models adapt continuously to environmental changes without retraining from scratch.

**Impact**: Long-term operational stability.



### 12. Digital Twin Attack Simulation

Simulates attack paths and behaviors in a controlled environment.

**Impact**: Improves readiness without production risk.



### 13. Keystroke Dynamics (Behavioral Biometrics)

Analyzes typing and interaction patterns for identity verification.

**Impact**: Detects session hijacking even with valid credentials.



### 14. SOAR Features

Automates investigation, enrichment, and response actions based on risk thresholds.

**Impact**: Reduces response time from hours to seconds.



### 15. Reinforcement Learning (Adaptive Thresholds)

Risk thresholds are adjusted dynamically based on outcomes and feedback.

**Impact**: Reduces alert fatigue over time.



### 16. Federated Learning (Client/Server)

Models learn across environments without sharing raw data.

**Impact**: Preserves privacy and scales across organizations.



### 17. Explainability Features

Every alert includes reasoning: contributing signals, sequence context, and graph evidence.

**Impact**: Builds analyst trust and auditability.



### 18. Streaming Processing

Processes events as continuous streams rather than batch jobs.

**Impact**: Enables true real-time defense.



### 19. MySQL-Based Persistent Store

Stores alerts, features, scores, and explanations for auditing and analytics.

**Impact**: Supports compliance and forensics.



### 20. Frontend Visualization Features

Provides dashboards for alerts, system health, behavior trends, and risk evolution.

**Impact**: Makes advanced security accessible to humans.



## How This System Works in Practice

1. A user performs actions in the cloud
2. Events are ingested and normalized
3. UEBA, sequence, graph, EDR, NDR, and rules analyze behavior
4. Fusion engine aggregates evidence
5. Risk score evolves over time
6. Explainable alert is generated
7. Automated or human-guided response is executed

This mirrors how a skilled security analyst thinks — but at machine speed.



## Impact on Cloud Infrastructure Growth

This system enables organizations to:

* adopt cloud faster with reduced risk
* operate with fewer security staff
* trust automation without blind action
* prevent breaches instead of reacting to them
* scale securely across hybrid environments

**Security becomes an enabler, not a blocker.**



## Project Execution Commands & Their Purpose

This section explains the role of every command required to run the **Integrated AI-Infused Threat Detection and Incident Response System** end-to-end.


### 1. Activate Python Virtual Environment

```powershell
.\.venv\Scripts\Activate
$env:PYTHONPATH="."
```

Initializes the isolated Python runtime containing all project dependencies and ensures the project root is available for module imports.


### 2. Start Backend Threat Processing API

```powershell
python services\consumer\api.py
```

Launches the core backend API responsible for ingesting events, normalizing data, enriching threat context, and publishing detections across the system.


### 3. Replay CloudTrail Logs (Threat Simulation)

```powershell
python services/ingest/cloudtrail_replay.py examples/cloudtrail_demo_30.json 0.2
```

Replays AWS CloudTrail logs into the system at a controlled speed to simulate real-world attacks and validate detection accuracy across all AI engines.



### 4. Start SOC Web Dashboard

```powershell
cd Frontend
npm install
npm run dev
```

Starts the interactive Security Operations Center dashboard used for real-time alert monitoring, threat visualization, and investigation workflows.



### 5. Train Multi-Modal Fusion Engine

```powershell
python services\ml\fusion\contrastive_train.py
```

Trains the contrastive learning model that fuses UEBA, sequence intelligence, and graph correlation signals into a unified risk scoring engine.



### 6. Capture Initial Configuration Snapshot

```powershell
python services\drift\config_snapshot.py
```

Creates the baseline snapshot of cloud configuration used to detect infrastructure drift and policy violations.



### 7. Launch Sequence Modeling Service

```powershell
python services\ml\sequence\serve_transformer.py
```

Starts the transformer-based deep learning service that detects chained attack patterns and multi-stage intrusions.



### 8. Start Graph Correlation Engine

```powershell
python services\graph_service\graph_api.py
```

Runs the graph analytics service that constructs real-time relationship graphs between users, IPs, and cloud resources.



### 9. Start Drift Detection Engine

```powershell
python services\drift\drift_service.py
```

Continuously monitors configuration changes and emits drift-based security alerts and policy violation events.



### 10. Execute Snapshot Comparison Engine

```powershell
python services\drift\config_drift.py
```

Performs deep structural comparison between configuration snapshots to detect unauthorized or risky changes.



### 11. Evaluate UEBA Detection Accuracy

```powershell
python scripts/eval_ueba.py
```

Evaluates the User and Entity Behavior Analytics model for insider threat detection and anomaly classification.



### 12. Evaluate Sequence Attack Detection

```powershell
python scripts/eval_sequence.py
```

Benchmarks the transformer-based temporal detection model for identifying multi-step attack chains.


### 13. Evaluate Graph Threat Correlation

```powershell
python scripts/eval_graph.py
```

Measures the accuracy of the graph-based correlation engine in identifying hidden lateral movement and privilege escalation paths.



## Validation Status

The system has been fully implemented and validated in a controlled laboratory environment using realistic telemetry and attack simulations. Experimental results confirm correct behavior of detection engines, fusion logic, and response workflows, achieving readiness for further deployment and evaluation.



## Conclusion

This project represents a shift from **event-based security** to **behavior-centric, relationship-aware, adaptive defense**. By unifying multiple detection paradigms into a single intelligent system, it offers a practical, scalable, and explainable approach to modern cloud security.

