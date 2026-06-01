"""LLM and deterministic backends for TyCAT fixture generation.

Regulatory context reflected in prompt scaffolding and schema constraints:
- FinCEN National AML/CFT Priorities (2021)
- AMLA 2020 Section 6209 testing standard mandate
- NIST AI RMF 1.0 and NIST AI 600-1 for trustworthy GenAI controls
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import random
from typing import Any

from .oracles import Oracle, OracleAssertion, get_oracle_template
from .typology_mapper import TYPOLOGY_CATALOG

try:
    import jsonschema
except Exception:  # pragma: no cover - optional dependency fallback
    jsonschema = None


LLM_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "typology": {"type": "string"},
        "fixture_rows": {
            "type": "array",
            "items": {"type": "object"},
            "minItems": 1,
        },
        "oracle_assertions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "column": {"type": ["string", "null"]},
                    "value": {},
                    "detail": {"type": "string"},
                },
                "required": ["kind", "column", "value", "detail"],
            },
            "minItems": 1,
        },
        "coverage_tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "expected_alert": {"type": "boolean"},
        "narrative": {"type": "string"},
    },
    "required": [
        "typology",
        "fixture_rows",
        "oracle_assertions",
        "coverage_tags",
        "expected_alert",
    ],
}


@dataclass(frozen=True)
class TestSpec:
    """Generated ETL test specification."""

    typology: str
    fixture_rows: list[dict[str, Any]]
    oracle: Oracle
    coverage_tags: list[str]
    narrative: str = ""


class LLMBackend(ABC):
    """Abstract interface for pluggable text-generation backends."""

    @abstractmethod
    def generate(self, system: str, user: str, response_format: dict[str, Any]) -> dict[str, Any]:
        """Generate a JSON-like dictionary response."""


class MockBackend(LLMBackend):
    """Deterministic, seed-controlled backend with no API calls."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def _rng(self, typology: str) -> random.Random:
        digest = hashlib.sha256(f"{self.seed}:{typology}".encode("utf-8")).hexdigest()
        return random.Random(int(digest[:16], 16))

    def generate(self, system: str, user: str, response_format: dict[str, Any]) -> dict[str, Any]:
        typology = user.strip().splitlines()[-1].replace("typology=", "").strip()
        rng = self._rng(typology)

        if typology == "bulk_cash_structuring":
            fixture_rows = [
                {"tx_id": "S1", "src_account": "A100", "amount": 9300.0, "payment_type": "cash_deposit"},
                {"tx_id": "S2", "src_account": "A100", "amount": 9450.0, "payment_type": "cash_deposit"},
                {"tx_id": "S3", "src_account": "A100", "amount": 9800.0, "payment_type": "cash_deposit"},
            ]
            assertions = [
                {"kind": "row_count_gte", "column": None, "value": 3, "detail": "Need repeated deposits"},
                {
                    "kind": "sum_gte",
                    "column": "amount",
                    "value": 10000,
                    "detail": "14-day rolling sum should exceed CTR threshold",
                },
            ]
            tags = ["P6_drug_trafficking", "cash", "structuring"]
        elif typology == "funnel_account":
            fixture_rows = [
                {"tx_id": f"F{i}", "src_account": f"SRC{i}", "dst_account": "DST1", "amount": 1400 + i}
                for i in range(1, 7)
            ]
            assertions = [
                {
                    "kind": "distinct_count_gte",
                    "column": "src_account",
                    "value": 5,
                    "detail": "At least five unique senders into one account",
                }
            ]
            tags = ["P6_drug_trafficking", "funnel", "graph"]
        elif typology == "mule_account":
            fixture_rows = [
                {"tx_id": f"M{i}", "src_account": "MULE_SRC", "dst_account": f"DST{i}", "amount": 620.0}
                for i in range(1, 10)
            ]
            assertions = [
                {
                    "kind": "distinct_count_gte",
                    "column": "dst_account",
                    "value": 8,
                    "detail": "Mule fan-out target",
                }
            ]
            tags = ["P2_cybercrime_virtual_currency", "mule", "fan_out"]
        elif typology == "sanctioned_jurisdiction":
            fixture_rows = [
                {
                    "tx_id": "J1",
                    "src_account": "SRC9",
                    "dst_account": "DST9",
                    "amount": 30000.0,
                    "payment_type": "wire",
                    "dst_country": "IR",
                }
            ]
            assertions = [
                {
                    "kind": "column_in_set",
                    "column": "dst_country",
                    "value": ["KP", "IR", "SY", "CU"],
                    "detail": "Destination should be sanctioned",
                },
                {
                    "kind": "sum_gte",
                    "column": "amount",
                    "value": 20000,
                    "detail": "Material value transfer",
                },
            ]
            tags = ["P8_proliferation", "sanctions", "wire"]
        else:
            base_amount = round(rng.uniform(450.0, 125000.0), 2)
            fixture_rows = [
                {
                    "tx_id": f"{typology[:4].upper()}_{i}",
                    "src_account": f"SRC_{rng.randint(1, 999)}",
                    "dst_account": f"DST_{rng.randint(1, 999)}",
                    "amount": round(base_amount * (0.8 + (i * 0.1)), 2),
                    "payment_type": rng.choice(["wire", "card", "p2p"]),
                    "dst_country": rng.choice(["US", "GB", "AE", "SG"]),
                }
                for i in range(1, 4)
            ]
            assertions = [
                {
                    "kind": "row_count_gte",
                    "column": None,
                    "value": 3,
                    "detail": "Minimum fixture size",
                },
                {
                    "kind": "sum_gte",
                    "column": "amount",
                    "value": round(base_amount * 2.0, 2),
                    "detail": "Aggregate movement should be meaningful",
                },
            ]
            tags = ["mock", typology, "deterministic"]

        return {
            "typology": typology,
            "fixture_rows": fixture_rows,
            "oracle_assertions": assertions,
            "coverage_tags": tags,
            "expected_alert": True,
            "narrative": f"Deterministic mock fixture for {typology}.",
        }


class OpenAIBackend(LLMBackend):
    """OpenAI Chat Completions backend."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, system: str, user: str, response_format: dict[str, Any]) -> dict[str, Any]:
        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("openai package is required for OpenAIBackend") from exc

        client = OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return json.loads(resp.choices[0].message.content or "{}")


class AnthropicBackend(LLMBackend):
    """Anthropic Messages API backend."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-haiku-latest") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, system: str, user: str, response_format: dict[str, Any]) -> dict[str, Any]:
        try:
            from anthropic import Anthropic
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("anthropic package is required for AnthropicBackend") from exc

        client = Anthropic(api_key=self.api_key)
        resp = client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.2,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        payload = "".join(
            block.text for block in resp.content if hasattr(block, "text") and block.text
        )
        return json.loads(payload)


class _ResponseCache:
    """SHA-256 keyed JSON disk cache for backend outputs."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path_for(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, key: str, value: dict[str, Any]) -> None:
        path = self._path_for(key)
        path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def _validate_payload(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    required = schema.get("required", [])
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing required keys: {missing}")

    if jsonschema is not None:
        jsonschema.validate(instance=payload, schema=schema)


def _build_oracle_from_payload(payload: dict[str, Any]) -> Oracle:
    assertions = [
        OracleAssertion(
            kind=assertion["kind"],
            column=assertion.get("column"),
            value=assertion.get("value"),
            detail=assertion.get("detail", ""),
        )
        for assertion in payload["oracle_assertions"]
    ]
    return Oracle(assertions=assertions, expected_alert=bool(payload["expected_alert"]))


def _load_prompt_for_typology(typology: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / f"{typology}.txt"
    if not prompt_path.exists():
        return f"Generate a realistic AML ETL test for typology={typology}."
    return prompt_path.read_text(encoding="utf-8")


def generate_test_spec(
    typology: str,
    backend: LLMBackend,
    schema: dict[str, Any] | None = None,
    cache_dir: str | Path = "experiments/cache",
) -> TestSpec:
    """Generate a single typology-specific test specification.

    Raises:
        KeyError: If typology is unknown.
        ValueError: If output does not satisfy required schema constraints.
    """

    if typology not in TYPOLOGY_CATALOG:
        raise KeyError(f"Unknown typology: {typology}")

    schema_to_use = schema or LLM_OUTPUT_SCHEMA
    system_prompt = (
        "You are TyCAT. Return strict JSON only. Respect regulatory alignment "
        "for FinCEN priorities and AMLA Section 6209 testability needs."
    )
    user_prompt = f"{_load_prompt_for_typology(typology)}\ntypology={typology}"

    cache = _ResponseCache(Path(cache_dir))
    cache_key = json.dumps(
        {
            "typology": typology,
            "backend": backend.__class__.__name__,
            "system": system_prompt,
            "user": user_prompt,
            "schema": schema_to_use,
        },
        sort_keys=True,
    )
    payload = cache.get(cache_key)
    if payload is None:
        payload = backend.generate(system_prompt, user_prompt, schema_to_use)
        cache.set(cache_key, payload)

    _validate_payload(payload, schema_to_use)

    # Prefer reusable template where available; fallback to generated assertions.
    try:
        oracle = get_oracle_template(typology).make()
        oracle.expected_alert = bool(payload["expected_alert"])
    except KeyError:
        oracle = _build_oracle_from_payload(payload)

    return TestSpec(
        typology=typology,
        fixture_rows=list(payload["fixture_rows"]),
        oracle=oracle,
        coverage_tags=list(payload["coverage_tags"]),
        narrative=str(payload.get("narrative", "")),
    )
