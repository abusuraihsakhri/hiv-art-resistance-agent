# Hiv Art Resistance Agent

> **Domain:** Infectious Disease Surveillance & Microbiology
> **Reference Guidelines & Standards:** `CLSI M100, EUCAST & CDC NHSN Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Hiv Art Resistance Agent** is an advanced analytical and computational platform implementing Stanford HIVdb Genotypic Resistance & ART Regimen Optimizer. It interprets HIV resistance mutations, scores drug susceptibility, recommends antiretroviral therapy (ART) regimens, and provides enterprise-grade security with PHI protection and cryptographic audit trails.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`interpret_drug_resistance()`**: Interpret HIV resistance mutations and score each drug.

  Args:
      mutations: List of mutation strings (e.g., ['M184V', 'K103N', 'N155H'])

  Returns:
      Dict mapping each drug to its resistance score and level

- **`recommend_regimen()`**: Recommend ART regimen based on resistance profile.

  Args:
      resistance_interpretation: Output from interpret_drug_resistance()
      tropism: 'CCR5', 'CXCR4', or 'dual_mixed' (optional)
      hla_b5701_positive: Whether HLA-B*5701 is positive (abacavir hypersensitivity)
      hepatitis_b_coinfected: Whether patient has HBV coinfection

  Returns:
      Dict with recommended regimen and alternatives

- **`interpret_tropism()`**: Interpret HIV tropism testing result.

  Args:
      tropism_result: 'CCR5', 'CXCR4', 'DUAL_MIXED', or 'NON_R5'

  Returns:
      Dict with interpretation and clinical implications

- **`analyze_hiv_resistance()`**: Complete HIV ART resistance analysis.

  Args:
      mutations: List of detected resistance mutations
      tropism: Tropism test result (optional)
      hla_b5701_positive: HLA-B*5701 status
      hepatitis_b_coinfected: HBV coinfection status

  Returns:
      Comprehensive analysis with resistance interpretation and regimen recommendations

### 🏢 Enterprise Agent System

- **SystemSupervisor**: Multi-agent orchestrator coordinating QC, Safety, and Protocol Conformance workers
- **PHIGuard**: Zero-PHI outbound interceptor blocking SSNs, MRNs, phone numbers, and patient identifiers
- **AuditLogger**: Tamper-evident HMAC-SHA256 cryptographic audit trail with integrity verification
- **LLMFactory**: Air-gapped LLM reasoning adapter supporting Ollama, Claude, OpenAI, and deterministic mocks

---

## 💻 CLI Quickstart & Usage

### Installation

```bash
pip install fastapi uvicorn pydantic pytest
```

Set the audit secret key for persistent audit integrity:
```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key
```

### 1. Interpret Resistance Mutations
```bash
python hiv_resistance_agent.py interpret --mutations M184V,K103N,N155H --tropism CCR5
```

### 2. Interpret Tropism
```bash
python hiv_resistance_agent.py tropism --result CCR5
```

### 3. Run Clinical Audit
```bash
python cli.py audit --case-id CASE-001 --primary 26.2 --secondary 12.5 --stat --status DISCORDANT
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. System Query Chat
```bash
python cli.py chat "system status"
```

### 6. Batch Process CSV
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 7. Launch REST API Server
```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

### Parameter Reference
- `interpret`: Interpret HIV resistance mutations
  - `--mutations`: Comma-separated list of mutations (e.g., M184V,K103N)
  - `--tropism`: Tropism result (CCR5, CXCR4, DUAL_MIXED)
  - `--hla-b5701`: HLA-B*5701 positive flag
  - `--hbv`: Hepatitis B coinfection flag
- `tropism`: Interpret tropism test result
  - `--result`: Tropism result
- `audit`: Run clinical audit
  - `--case-id`/`--task-id`: Case identifier
  - `--primary`: Primary metric value
  - `--secondary`: Secondary metric value
  - `--stat`: STAT priority flag
  - `--status`: Status descriptor
- `verify-audit`: Verify HMAC-SHA256 audit trail integrity
- `chat`: System configuration query
- `batch`: Batch process CSV records
  - `-i/--input`: Input CSV file
  - `-o/--output`: Output CSV file
- `serve`: Launch FastAPI REST server
  - `--host`: Server host (default: 127.0.0.1)
  - `--port`: Server port (default: 8000)

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition. Integrity verification detects both chain linkage breaks and signature tampering.
* **Secure Key Management:** Audit signing key sourced from `AUDIT_SECRET_KEY` environment variable. Runtime warning issued if not set; a cryptographically random key is generated per session.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

The test suite includes:
- HIV drug class and mutation database validation
- Resistance scoring accuracy (M184V, K65R, K103N, N155H, etc.)
- Regimen recommendation logic (INSTI-based, PI-based, NNRTI-based)
- Tropism interpretation (CCR5, CXCR4, dual/mixed)
- Full multi-class resistance analysis
- CLI command validation (interpret, tropism, audit, chat, verify-audit)
- PHI guard enforcement
- Worker agent evaluation (QC, Safety, Protocol Conformance)
- Supervisor consensus and audit integrity
- Audit trail tamper detection
- Enrichment suite execution

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t hiv-art-resistance-agent .
docker run -p 8000:8000 hiv-art-resistance-agent
```

---

## 📁 Project Structure

```
hiv-art-resistance-agent/
├── agents/                          # Enterprise agent system
│   ├── base.py                      # PHI Guard, Audit Trail, Security
│   ├── models.py                    # Pydantic data models
│   ├── workers.py                   # QC, Safety, Protocol workers
│   ├── supervisor.py                # Multi-agent orchestrator
│   ├── llm_factory.py               # LLM provider factory
│   ├── api.py                       # FastAPI REST endpoints
│   ├── streamer.py                  # WebSocket telemetry
│   ├── learning.py                  # Bayesian calibration
│   └── metrics.py                   # Prometheus metrics
├── hiv_art_resistance_agent/        # Core application package
│   ├── cli.py                       # Full-featured CLI
│   ├── server.py                    # FastAPI app factory
│   ├── agents.py                    # Agent hierarchy
│   ├── engine.py                    # Clinical domain engine
│   └── models.py                    # Clinical data models
├── tests/                           # Test suite
│   ├── test_hiv_art_resistance_agent.py
│   └── test_enrichment.py
├── hiv_resistance_agent.py          # HIVdb resistance interpreter
├── enrichment.py                    # Enrichment feature engines
├── simulator.py                     # High-throughput simulator
├── cli.py                           # CLI entry point
├── pyproject.toml                   # Project configuration
├── Dockerfile                       # Container definition
└── README.md                        # This file
```
