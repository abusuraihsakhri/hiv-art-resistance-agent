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

**Hiv Art Resistance Agent** is an advanced analytical and computational platform implementing Stanford HIVdb Genotypic Resistance & ART Regimen Optimizer.

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
- **`build_parser()`**: Build the argument parser.

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t hiv-art-resistance-agent .
docker run -p 8000:8000 hiv-art-resistance-agent
```
