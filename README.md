# TyCAT — AI-Augmented ETL Test Case Generation for AML Transaction Monitoring

**Typology-Conditioned AI Testing (TyCAT)** is a Python toolkit that automates the generation of ETL test cases for Anti-Money Laundering (AML) transaction-monitoring systems. Test suites are anchored to FinCEN's eight National AML/CFT Priorities and the AMLA 2020 Section 6209 technology-testing mandate.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](CITATION.cff)

---

## Table of Contents

1. [Overview](#overview)
2. [Regulatory Alignment](#regulatory-alignment)
3. [Architecture](#architecture)
4. [Typology Catalog](#typology-catalog)
5. [Installation](#installation)
6. [Quick Start](#quick-start)
7. [CLI Reference](#cli-reference)
8. [Python API](#python-api)
9. [Project Structure](#project-structure)
10. [How It Works](#how-it-works)
11. [Extending TyCAT](#extending-tycat)
12. [Testing](#testing)
13. [Citation](#citation)
14. [License](#license)

---

## Overview

AML compliance teams routinely build ETL pipelines that ingest, transform, and route transaction data into alert-generation engines. Validating these pipelines against the full breadth of financial crime typologies is expensive and labour-intensive. TyCAT solves this by:

- **Generating structured fixture datasets** for each known money-laundering typology.
- **Attaching oracle assertions** (row counts, column sums, set membership, temporal gap constraints, alert polarity) to every fixture, enabling automated pass/fail evaluation.
- **Covering all 8 FinCEN AML/CFT Priorities** with a catalog of 24 typologies.
- **Supporting both a deterministic mock backend** (no API keys required) and plug-in LLM backends (OpenAI, Anthropic) for richer, narrative-enriched fixtures.
- **Measuring test quality** via typology coverage, priority coverage, and mutation score metrics.

---

## Regulatory Alignment

| Regulation / Guidance | How TyCAT addresses it |
|---|---|
| **FinCEN National AML/CFT Priorities (June 30, 2021)** | All 8 priorities mapped to typology codes; coverage metrics computed per priority. |
| **AMLA 2020 Section 6209** | Testing taxonomy and reproducible fixture generation support technology-testing mandate. |
| **FinCEN NPRM 89 FR 55428 (2024) / 2026 successor docket** | Typology catalog and oracle schema extensible to accommodate future rule updates. |
| **Interagency MRM Guidance (OCC 2026-13 / SR 26-2 / FIL-15-2026)** | Deterministic seeds, JSON schemas, and oracle assertions support model-risk documentation. |
| **NIST AI RMF 1.0 and NIST AI 600-1** | MockBackend ensures reproducibility; LLM outputs are validated against a strict JSON schema before use. |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    TyCAT CLI / API                  │
└───────────────┬──────────────────────┬──────────────┘
                │                      │
     ┌──────────▼──────┐    ┌──────────▼──────────┐
     │  LLM Generator  │    │  Synthetic Data Gen  │
     │  (MockBackend / │    │  (50 k transactions, │
     │   OpenAI /      │    │   5 k accounts)      │
     │   Anthropic)    │    └─────────────────────┘
     └──────────┬──────┘
                │  TestSpec (typology + fixtures + oracle + tags)
     ┌──────────▼──────────────────────────────────────┐
     │               Oracle Engine                     │
     │  row_count_gte · sum_gte · distinct_count_gte   │
     │  column_unique · column_in_set · max_gap_lte    │
     │  alert_raised  · no_alert                       │
     └──────────┬──────────────────────────────────────┘
                │
     ┌──────────▼──────────────────────────────────────┐
     │           AML Detectors (rule_based.py)         │
     │  7 rules: amount · fan_out · velocity ·         │
     │  round_number · cross_border · structuring ·    │
     │  dormant_active                                 │
     └──────────┬──────────────────────────────────────┘
                │
     ┌──────────▼──────────────────────────────────────┐
     │          Metrics & Validators                   │
     │  typology_coverage · priority_coverage ·        │
     │  mutation_score · GE suite · Pandera schema     │
     └─────────────────────────────────────────────────┘
```

---

## Typology Catalog

TyCAT ships with **24 typologies** spanning all 8 FinCEN priorities:

| Code | Name | FinCEN Priority | ETL Dimensions |
|---|---|---|---|
| `shell_company` | Shell Company Laundering | P1 Corruption | entity, counterparty, jurisdiction, amount, time |
| `pep_layering` | PEP Layering | P1 Corruption | customer_risk, counterparty, amount, time |
| `real_estate_layering` | Real Estate Layering | P1 Corruption | merchant, amount, asset, time |
| `crypto_layering` | Crypto Layering | P2 Cybercrime / Virtual Currency | counterparty, channel, amount, time |
| `ransomware_payouts` | Ransomware Payouts | P2 Cybercrime / Virtual Currency | channel, counterparty, amount, time |
| `mule_account` | Mule Account | P2 Cybercrime / Virtual Currency | graph, counterparty, time, amount |
| `small_value_funnel` | Small Value Funnel | P3 Terrorist Financing | graph, counterparty, time, amount |
| `hawala_proxy` | Hawala Proxy | P3 Terrorist Financing | graph, channel, jurisdiction, time |
| `ngo_misuse` | NGO Misuse | P3 Terrorist Financing | entity, counterparty, jurisdiction, amount |
| `account_takeover` | Account Takeover | P4 Fraud | behavior, channel, time, amount |
| `first_party_fraud` | First Party Fraud | P4 Fraud | identity, behavior, amount, time |
| `elder_financial_abuse` | Elder Financial Abuse | P4 Fraud | customer_risk, behavior, amount, time |
| `trade_based_ml` | Trade-Based Money Laundering | P5 Transnational Criminal Orgs | trade, jurisdiction, amount, counterparty |
| `professional_money_launderer` | Professional Money Launderer | P5 Transnational Criminal Orgs | graph, jurisdiction, counterparty, time |
| `bulk_cash_smurfing` | Bulk Cash Smurfing | P6 Drug Trafficking | channel, amount, time, branch |
| `bulk_cash_structuring` | Bulk Cash Structuring | P6 Drug Trafficking | channel, amount, time, account |
| `funnel_account` | Funnel Account | P6 Drug Trafficking | graph, counterparty, amount, time |
| `casino_layering` | Casino Layering | P6 Drug Trafficking | merchant, channel, amount, time |
| `hotel_transport_pattern` | Hotel / Transport Pattern | P7 Human Trafficking | merchant, channel, amount, time |
| `small_value_recurring` | Small Value Recurring | P7 Human Trafficking | counterparty, amount, time, frequency |
| `sanctioned_jurisdiction` | Sanctioned Jurisdiction | P8 Proliferation Financing | jurisdiction, counterparty, amount, channel |
| `proliferation_network` | Proliferation Network | P8 Proliferation Financing | graph, jurisdiction, counterparty, amount |
| `virtual_asset_obfuscation` | Virtual Asset Obfuscation | P8 Proliferation Financing | channel, counterparty, amount, time |
| `correspondent_abuse` | Correspondent Abuse | P8 Proliferation Financing | jurisdiction, counterparty, channel, amount |

---

## Installation

### Core (no LLM, no Spark)

```bash
pip install .
```

### With LLM backends (OpenAI / Anthropic)

```bash
pip install ".[llm]"
```

### With Spark + Great Expectations + Pandera

```bash
pip install ".[spark]"
```

### Full development environment

```bash
pip install ".[llm,spark,ml,gnn,dev]"
# or
pip install -r requirements.txt
```

**Requirements:** Python ≥ 3.10

---

## Quick Start

### 1 — Generate demo transaction data

```bash
tycat gen-demo --out-dir data/ --seed 42
```

Writes two CSV files to `data/`:
- `transactions.csv` — 50,000 transactions (≈ 0.2 % labelled illicit across 8 typologies)
- `accounts.csv` — 5,000 accounts with KYC and PEP flags

### 2 — Generate a typology test suite

```bash
tycat gen-suite --out experiments/generated_suite.json --seed 42
```

Produces a JSON array of test specifications, one per typology. Each entry contains:

```json
{
  "typology": "bulk_cash_structuring",
  "fixture_rows": [...],
  "oracle": {
    "expected_alert": true,
    "assertions": [
      { "kind": "row_count_gte", "column": null, "value": 3, "detail": "Need repeated deposits" },
      { "kind": "sum_gte", "column": "amount", "value": 10000, "detail": "14-day rolling sum should exceed CTR threshold" }
    ]
  },
  "coverage_tags": ["P6_drug_trafficking", "cash", "structuring"],
  "narrative": "..."
}
```

### 3 — Inspect package and compliance alignment

```bash
tycat info
```

---

## CLI Reference

| Command | Options | Description |
|---|---|---|
| `tycat gen-demo` | `--out-dir PATH` · `--seed INT` | Generate demo transaction and account CSV files |
| `tycat gen-suite` | `--out PATH` · `--seed INT` | Generate full typology test suite JSON |
| `tycat info` | — | Print version, typology counts, and regulatory anchors |

---

## Python API

### Generate fixtures programmatically

```python
from tycat.llm_generator import MockBackend, generate_test_spec
from tycat.typology_mapper import TYPOLOGY_CATALOG

backend = MockBackend(seed=42)

spec = generate_test_spec("bulk_cash_structuring", backend)
print(spec.typology)        # "bulk_cash_structuring"
print(spec.fixture_rows)    # list of transaction dicts
print(spec.oracle)          # Oracle with assertions
print(spec.coverage_tags)   # ["P6_drug_trafficking", "cash", "structuring"]
```

### Use an LLM backend (requires `.[llm]`)

```python
from tycat.llm_generator import OpenAIBackend, generate_test_spec  # or AnthropicBackend

backend = OpenAIBackend(model="gpt-4o", api_key="sk-...")
spec = generate_test_spec("hawala_proxy", backend)
print(spec.narrative)
```

> LLM outputs are validated against a strict JSON schema (`LLM_OUTPUT_SCHEMA`) before a `TestSpec` is constructed — malformed responses raise `jsonschema.ValidationError`.

### Run the rule-based detector

```python
import pandas as pd
from tycat.aml_detectors.rule_based import RuleBasedDetector

detector = RuleBasedDetector(amount_threshold=1_000_000.0)
df = pd.DataFrame(spec.fixture_rows)
alerts = detector(df)
# [{"tx_id": "S1", "rule": "structuring", "reason": "..."}, ...]
```

### Evaluate an oracle

```python
passed = spec.oracle.evaluate(df, alerts)
```

### Compute test suite metrics

```python
from tycat.metrics import typology_coverage, priority_coverage, mutation_score

specs = [generate_test_spec(t, backend) for t in TYPOLOGY_CATALOG]

print(typology_coverage(specs))   # fraction of 24 typologies covered
print(priority_coverage(specs))   # fraction of 8 priorities fully covered
```

### Export to Great Expectations / Pandera

```python
from tycat.validators import to_ge_suite, to_pandera_schema

ge_suite = to_ge_suite(spec.oracle)   # portable GE expectation suite dict
schema   = to_pandera_schema(("tx_id", "amount", "src_account"))
schema.validate(df)
```

---

## Project Structure

```
.
├── src/tycat/
│   ├── cli.py               # Click CLI entry-point (tycat)
│   ├── llm_generator.py     # LLMBackend ABC, MockBackend, OpenAIBackend, TestSpec
│   ├── typology_mapper.py   # FINCEN_PRIORITIES, TYPOLOGY_CATALOG, TypologyDef
│   ├── oracles.py           # OracleAssertion, Oracle, OracleTemplate
│   ├── synthetic_data.py    # generate_demo(), write_demo() — 50k transaction dataset
│   ├── metrics.py           # typology_coverage, priority_coverage, mutation_score
│   ├── validators.py        # to_ge_suite(), to_pandera_schema()
│   ├── prompts/             # System/user prompt templates for LLM backends
│   └── aml_detectors/
│       └── rule_based.py    # RuleBasedDetector (7 rules, mutation-test friendly)
├── data/                    # Generated CSV outputs (git-ignored)
├── experiments/             # Generated test suite JSON and experiment artefacts
├── notebooks/               # Jupyter notebooks for exploration
├── tests/                   # pytest test suite
├── docs/figures/            # Architecture and result figures
├── pyproject.toml           # Build config, dependencies, tool settings
├── requirements.txt         # Pinned core requirements for CI
└── CITATION.cff             # Software citation metadata
```

---

## How It Works

1. **Typology mapping** — `TYPOLOGY_CATALOG` maps each of the 24 typology codes to a `TypologyDef` containing a human-readable name, description, and the ETL dimensions it exercises (e.g., `graph`, `jurisdiction`, `amount`, `time`).

2. **Backend dispatch** — `generate_test_spec(typology, backend)` calls `backend.generate(system_prompt, user_prompt, schema)`. The `MockBackend` returns hand-crafted, deterministic fixtures; LLM backends receive a typology-conditioned system prompt and a JSON schema to constrain the response format.

3. **Schema validation** — Every backend response is validated against `LLM_OUTPUT_SCHEMA` using `jsonschema`. This prevents prompt-injection artefacts or hallucinated column names from propagating into test suites.

4. **Oracle construction** — `OracleAssertion` objects are built from the validated response. Supported assertion kinds:

   | Kind | Description |
   |---|---|
   | `row_count_gte` | DataFrame must have ≥ N rows |
   | `sum_gte` | Column sum ≥ threshold |
   | `distinct_count_gte` | Column cardinality ≥ N |
   | `column_unique` | Column values must be unique |
   | `column_in_set` | All values must belong to an allowed set |
   | `max_gap_lte` | Maximum time gap between events ≤ threshold (seconds) |
   | `alert_raised` | Detector must produce ≥ 1 alert |
   | `no_alert` | Detector must produce 0 alerts |

5. **Detector execution** — `RuleBasedDetector` implements 7 transparent rules intentionally designed to be mutation-testable. Rules are individually togglable via `rules_enabled`.

6. **Metrics** — `typology_coverage` and `priority_coverage` track breadth; `mutation_score` measures how many detector mutants (i.e., deliberately broken detectors) are caught ("killed") by the generated test suite.

---

## Extending TyCAT

### Add a new typology

```python
# src/tycat/typology_mapper.py
from tycat.typology_mapper import TYPOLOGY_CATALOG, TypologyDef

TYPOLOGY_CATALOG["new_typology"] = TypologyDef(
    code="new_typology",
    name="My New Typology",
    description="Description of the laundering pattern.",
    etl_dimensions=("counterparty", "amount", "time"),
)
```

Map it to a FinCEN priority in `PRIORITY_TYPOLOGY_MAP` in the same file and add a fixture branch in `MockBackend.generate()` for deterministic testing.

### Plug in a custom LLM backend

```python
from tycat.llm_generator import LLMBackend
from typing import Any

class MyBackend(LLMBackend):
    def generate(self, system: str, user: str, response_format: dict[str, Any]) -> dict[str, Any]:
        # Call your model and return a dict matching LLM_OUTPUT_SCHEMA
        ...
```

### Add a new oracle assertion kind

Extend `OracleAssertion.evaluate()` in `src/tycat/oracles.py` with a new `if self.kind == "..."` branch and update `LLM_OUTPUT_SCHEMA` if the kind requires new fields.

---

## Testing

```bash
# Install dev dependencies
pip install ".[dev]"

# Run the test suite
pytest

# With coverage report
pytest --cov=tycat --cov-report=term-missing
```

---

## Citation

If you use TyCAT in your research or compliance work, please cite:

```bibtex
@software{tycat2026,
  title  = {{TyCAT}: AI-Augmented ETL Test Case Generation for AML Transaction Monitoring},
  author = {{TyCAT Contributors}},
  year   = {2026},
  url    = {https://github.com/hkrishnan62/AI-Augmented-ETL-Test-Case-Generation-for-AML-Transaction},
  version = {1.0.0},
  license = {MIT}
}
```

---

## License

Released under the [MIT License](LICENSE).
