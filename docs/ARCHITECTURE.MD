# ARCHITECTURE.md

## 1. System Overview
The system is a cloud-native, multitenant platform deployed on **Azure**. It is designed to answer queries over external data by combining **Retrieval-Augmented Generation (RAG)** with an **Agentic Layer**. 

The architecture bridges static knowledge bases with dynamic external actions through a modular design optimized for scalability, low latency, and enterprise-grade security.

---

## 2. Data Ingestion & Indexing
To ensure high retrieval precision, the system employs a hybrid strategy for processing and storing data.

* **Chunking Strategy:** Text is split into overlapping chunks (**512 tokens**, **50-token overlap**) to preserve semantic context across boundaries.
* **Indexing & Search:** * **Provider:** Azure AI Search.
    * **Mechanism:** **Hybrid Search** combines vector embeddings (`text-embedding-3-large`) with **BM25 keyword search** to balance semantic intent with exact term matching.

---

## 3. Agentic Layer (The Planner)
The system uses a **ReAct (Reasoning + Acting)** loop to handle complex or multi-step queries.



### Decision Cycle
1.  **Thought:** The LLM generates a reasoning step to determine what info is missing.
2.  **Action:** The LLM selects a tool from the registry (e.g., Web Search, Weather, Currency).
3.  **Observation:** The system executes the tool and captures the output.
4.  **Synthesis:** The cycle repeats until the LLM has sufficient data to provide the final answer.

### Tool Registry
Tools are defined via **JSON Schema**, allowing the planner to automatically validate parameters (e.g., ensuring a `location` string is provided for weather requests).

---

## 4. Performance & Caching
The system achieves sub-200ms latency through aggressive parallelism and a three-tier caching hierarchy.

### Tiered Caching Model
| Tier | Type | Technology | Purpose |
| :--- | :--- | :--- | :--- |
| **L1** | **Prompt Cache** | Native LLM | Reduces latency/cost for repeating system instructions. |
| **L2** | **Vector Cache** | Redis | Stores frequent embedding results for common queries. |
| **L3** | **HTTP Cache** | TTL-based | Stores transient external data (e.g., current weather). |

> **Parallelism:** All tool calls run concurrently using `asyncio` to prevent linear latency accumulation.

---

## 5. Security & Multitenancy
Built for enterprise compliance, the platform enforces strict isolation and governance.

* **Tenant Isolation:** All requests and documents are tagged with a `TenantID`. Search queries enforce mandatory per-tenant security filters at the index level.
* **Secrets Management:** **Azure Key Vault** stores all sensitive API tokens and tool credentials.
* **Governance:** * **RBAC:** Restricted access via authorized service principals.
    * **Audit Logging:** Comprehensive tracking of tenant activity and tool usage.

---

## 6. Observability & Deployment
### Observability
Full **OpenTelemetry** integration provides deep tracing through the planner, tools, and synthesis phases. We track:
* Token usage and cost impact.
* Per-tool latency and error rates.
* Performance bottleneck dashboards.

### Deployment Strategy
* **Infrastructure:** Containerized via **Docker**, orchestrated by **Azure Container Apps**.
* **Pipeline:** Automated CI/CD with **Blue-Green deployments** to ensure zero downtime.
* **Scaling:** Horizontal autoscaling (scales to zero when idle; bursts during high load).

---

## 7. Logical Flow
The following diagram illustrates the lifecycle of a request from ingestion to validation.



```mermaid
graph TD
    User([User Request]) --> Policy[Policy Enforcer]
    Policy --> Planner{Agentic Planner}
    
    subgraph Tools
    Planner --> Search[Azure AI Search]
    Planner --> Weather[Weather API]
    Planner --> Misc[Other Tools]
    end
    
    Search --> Synth[LLM Synthesizer]
    Weather --> Synth
    Misc --> Synth
    
    Synth --> Validator[Output Validator]
    Validator --> Response([Final Response])