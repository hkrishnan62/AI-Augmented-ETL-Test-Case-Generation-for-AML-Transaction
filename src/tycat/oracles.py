"""Oracle primitives for evaluating generated AML ETL fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd


@dataclass
class OracleAssertion:
    """Single assertion used by an Oracle."""

    kind: str
    column: str | None = None
    value: Any = None
    detail: str = ""

    def evaluate(self, df: pd.DataFrame, alerts: list[dict[str, Any]]) -> bool:
        """Evaluate assertion against fixture dataframe and detector alerts."""

        if self.kind == "row_count_gte":
            return len(df) >= int(self.value)

        if self.kind == "sum_gte":
            if self.column is None or self.column not in df.columns:
                return False
            return float(df[self.column].sum()) >= float(self.value)

        if self.kind == "distinct_count_gte":
            if self.column is None or self.column not in df.columns:
                return False
            return int(df[self.column].nunique()) >= int(self.value)

        if self.kind == "column_unique":
            if self.column is None or self.column not in df.columns:
                return False
            return bool(df[self.column].is_unique)

        if self.kind == "column_in_set":
            if self.column is None or self.column not in df.columns:
                return False
            allowed = set(self.value)
            return bool(df[self.column].isin(allowed).all())

        if self.kind == "max_gap_lte":
            if self.column is None or self.column not in df.columns:
                return False
            series = pd.to_datetime(df[self.column]).sort_values()
            if len(series) < 2:
                return True
            max_gap_seconds = (series.diff().dt.total_seconds().fillna(0.0)).max()
            return float(max_gap_seconds) <= float(self.value)

        if self.kind == "alert_raised":
            return len(alerts) > 0

        if self.kind == "no_alert":
            return len(alerts) == 0

        raise ValueError(f"Unsupported assertion kind: {self.kind}")


@dataclass
class Oracle:
    """Oracle containing one or more assertions and expected outcome metadata."""

    assertions: list[OracleAssertion]
    expected_alert: bool
    description: str = ""

    def evaluate(self, df: pd.DataFrame, alerts: list[dict[str, Any]]) -> bool:
        """Evaluate all assertions and expected alert polarity."""

        assertion_ok = all(assertion.evaluate(df, alerts) for assertion in self.assertions)
        alert_flag = len(alerts) > 0
        return assertion_ok and (alert_flag == self.expected_alert)

    def to_dict(self) -> dict[str, Any]:
        """Serialize oracle configuration."""

        return {
            "expected_alert": self.expected_alert,
            "description": self.description,
            "assertions": [
                {
                    "kind": assertion.kind,
                    "column": assertion.column,
                    "value": assertion.value,
                    "detail": assertion.detail,
                }
                for assertion in self.assertions
            ],
        }


@dataclass(frozen=True)
class OracleTemplate:
    """Template builder for reusable typology-specific oracle patterns."""

    typology_code: str
    build: Callable[..., Oracle]

    def make(self, **params: Any) -> Oracle:
        """Instantiate an oracle from template parameters."""

        return self.build(**params)


def _bulk_cash_structuring_template(window_days: int = 14) -> Oracle:
    return Oracle(
        assertions=[
            OracleAssertion("row_count_gte", value=3, detail="Repeated cash placements"),
            OracleAssertion("sum_gte", column="amount", value=10000, detail="CTR threshold exceeded"),
        ],
        expected_alert=True,
        description=f"Structuring pattern within {window_days}-day window.",
    )


def _small_value_funnel_template(min_sources: int = 6) -> Oracle:
    return Oracle(
        assertions=[
            OracleAssertion("distinct_count_gte", column="src_account", value=min_sources),
            OracleAssertion("alert_raised"),
        ],
        expected_alert=True,
        description="Many small senders converge into one destination.",
    )


def _funnel_account_template(min_sources: int = 5) -> Oracle:
    return Oracle(
        assertions=[
            OracleAssertion("distinct_count_gte", column="src_account", value=min_sources),
            OracleAssertion("alert_raised"),
        ],
        expected_alert=True,
        description="Funnel account receives from many distinct sources.",
    )


def _mule_account_template(min_destinations: int = 8) -> Oracle:
    return Oracle(
        assertions=[
            OracleAssertion("distinct_count_gte", column="dst_account", value=min_destinations),
            OracleAssertion("alert_raised"),
        ],
        expected_alert=True,
        description="Mule account fan-out to many beneficiaries.",
    )


def _sanctioned_jurisdiction_template() -> Oracle:
    return Oracle(
        assertions=[
            OracleAssertion(
                "column_in_set",
                column="dst_country",
                value=["KP", "IR", "SY", "CU"],
                detail="FinCEN/high-risk sanctions jurisdictions",
            ),
            OracleAssertion("sum_gte", column="amount", value=20000),
            OracleAssertion("alert_raised"),
        ],
        expected_alert=True,
        description="Outbound wire to sanctioned jurisdiction with material value.",
    )


_TEMPLATE_REGISTRY: dict[str, OracleTemplate] = {
    "bulk_cash_structuring": OracleTemplate("bulk_cash_structuring", _bulk_cash_structuring_template),
    "small_value_funnel": OracleTemplate("small_value_funnel", _small_value_funnel_template),
    "funnel_account": OracleTemplate("funnel_account", _funnel_account_template),
    "mule_account": OracleTemplate("mule_account", _mule_account_template),
    "sanctioned_jurisdiction": OracleTemplate("sanctioned_jurisdiction", _sanctioned_jurisdiction_template),
}


def get_oracle_template(typology_code: str) -> OracleTemplate:
    """Return registered template for typology, or raise KeyError."""

    if typology_code not in _TEMPLATE_REGISTRY:
        raise KeyError(f"No oracle template for typology: {typology_code}")
    return _TEMPLATE_REGISTRY[typology_code]
