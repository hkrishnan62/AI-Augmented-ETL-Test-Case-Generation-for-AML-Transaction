"""Validation adapters for Great Expectations and Pandera.

The adapters degrade gracefully when optional dependencies are unavailable,
allowing TyCAT test workflows to run in lightweight CI environments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .oracles import Oracle


def to_ge_suite(oracle: Oracle) -> dict[str, Any]:
    """Convert an Oracle into a portable GE-like expectation suite dictionary."""

    expectations: list[dict[str, Any]] = []
    for assertion in oracle.assertions:
        if assertion.kind == "sum_gte":
            expectations.append(
                {
                    "expectation_type": "expect_column_sum_to_be_between",
                    "kwargs": {
                        "column": assertion.column,
                        "min_value": assertion.value,
                    },
                }
            )
        elif assertion.kind == "row_count_gte":
            expectations.append(
                {
                    "expectation_type": "expect_table_row_count_to_be_between",
                    "kwargs": {"min_value": assertion.value},
                }
            )
        elif assertion.kind == "column_unique":
            expectations.append(
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": assertion.column},
                }
            )

    return {
        "expectation_suite_name": "tycat_oracle_suite",
        "expectations": expectations,
        "meta": {
            "expected_alert": oracle.expected_alert,
            "description": oracle.description,
        },
    }


@dataclass
class _FallbackPanderaSchema:
    """Minimal fallback schema with a pandera-like validate method."""

    required_columns: tuple[str, ...]

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in self.required_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return df


def to_pandera_schema(required_columns: tuple[str, ...] = ("tx_id", "amount")) -> Any:
    """Build a Pandera schema if installed, else return fallback validator."""

    try:
        import pandera as pa
    except Exception:
        return _FallbackPanderaSchema(required_columns=required_columns)

    fields = {col: pa.Column(object, nullable=False) for col in required_columns}
    return pa.DataFrameSchema(fields, coerce=True)
