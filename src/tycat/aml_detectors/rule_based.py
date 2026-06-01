"""Reference 7-rule AML detector for TyCAT experiments.

This simple baseline is intentionally transparent for testability and mutation
analysis under AMLA 2020 Section 6209-style model/technology validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


SANCTIONED_COUNTRIES = {"KP", "IR", "SY", "CU"}


@dataclass
class RuleBasedDetector:
    """Rule-based transaction detector used for reproducible experiments."""

    amount_threshold: float = 1_000_000.0
    fan_out_min: int = 5
    velocity_min: int = 10
    structuring_threshold: float = 10_000.0
    rules_enabled: list[str] = field(
        default_factory=lambda: [
            "amount",
            "fan_out",
            "velocity",
            "round_number",
            "cross_border",
            "structuring",
            "dormant_active",
        ]
    )

    def __call__(self, transactions_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Run all enabled rules and return alert records."""

        if transactions_df.empty:
            return []

        df = transactions_df.copy()
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        alerts: list[dict[str, Any]] = []

        def add_alert(tx_id: Any, rule: str, reason: str) -> None:
            alerts.append({"tx_id": str(tx_id), "rule": rule, "reason": reason})

        if "amount" in self.rules_enabled and "amount" in df.columns:
            for _, row in df[df["amount"] >= self.amount_threshold].iterrows():
                add_alert(row.get("tx_id", ""), "amount", "Amount exceeds high-value threshold")

        if "fan_out" in self.rules_enabled and {"src_account", "dst_account"}.issubset(df.columns):
            fanout = df.groupby("src_account")["dst_account"].nunique()
            suspicious_src = set(fanout[fanout >= self.fan_out_min].index)
            for _, row in df[df["src_account"].isin(suspicious_src)].iterrows():
                add_alert(row.get("tx_id", ""), "fan_out", "Source fans out to many destinations")

        if "velocity" in self.rules_enabled and {"src_account", "timestamp"}.issubset(df.columns):
            valid = df.dropna(subset=["timestamp"]).sort_values(["src_account", "timestamp"])
            for src, grp in valid.groupby("src_account"):
                rolling = grp.set_index("timestamp").rolling("1h")["tx_id"].count()
                if (rolling >= self.velocity_min).any():
                    for tx_id in grp["tx_id"]:
                        add_alert(tx_id, "velocity", f"High velocity burst for source {src}")

        if "round_number" in self.rules_enabled and "amount" in df.columns:
            mask = (df["amount"] >= 10_000) & ((df["amount"] % 1000).abs() < 1e-9)
            for _, row in df[mask].iterrows():
                add_alert(row.get("tx_id", ""), "round_number", "Large round-number transaction")

        if "cross_border" in self.rules_enabled and {"src_country", "dst_country"}.issubset(df.columns):
            mask = (df["src_country"] != df["dst_country"]) & (df.get("amount", 0) >= 20_000)
            for _, row in df[mask].iterrows():
                add_alert(row.get("tx_id", ""), "cross_border", "Material cross-border transfer")

        if "structuring" in self.rules_enabled and {"src_account", "timestamp", "amount"}.issubset(df.columns):
            valid = df.dropna(subset=["timestamp"]).sort_values(["src_account", "timestamp"])
            for src, grp in valid.groupby("src_account"):
                no_single_over = grp["amount"] < self.structuring_threshold
                if not no_single_over.all():
                    continue
                rolling_sum = grp.set_index("timestamp").rolling("14D")["amount"].sum()
                if (rolling_sum > self.structuring_threshold).any():
                    for tx_id in grp["tx_id"]:
                        add_alert(tx_id, "structuring", f"14-day sum exceeds {self.structuring_threshold}")

        if "dormant_active" in self.rules_enabled and {"src_account", "timestamp"}.issubset(df.columns):
            valid = df.dropna(subset=["timestamp"]).sort_values(["src_account", "timestamp"])
            for src, grp in valid.groupby("src_account"):
                gaps = grp["timestamp"].diff().dt.total_seconds().fillna(0)
                dormant_idx = gaps[gaps > 30 * 24 * 3600].index
                if len(dormant_idx) == 0:
                    continue
                reactivation_time = grp.loc[dormant_idx[0], "timestamp"]
                window_end = reactivation_time + pd.Timedelta(days=1)
                reactivated = grp[(grp["timestamp"] >= reactivation_time) & (grp["timestamp"] <= window_end)]
                if len(reactivated) >= 3:
                    for tx_id in reactivated["tx_id"]:
                        add_alert(tx_id, "dormant_active", f"Dormant-to-active burst for source {src}")

        if {"dst_country"}.issubset(df.columns):
            sanctioned = df[df["dst_country"].isin(SANCTIONED_COUNTRIES)]
            for _, row in sanctioned.iterrows():
                add_alert(row.get("tx_id", ""), "sanctioned_country", "Destination in sanctioned list")

        # Deduplicate same (tx_id, rule) combinations while preserving order.
        seen: set[tuple[str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for alert in alerts:
            key = (alert["tx_id"], alert["rule"])
            if key not in seen:
                seen.add(key)
                deduped.append(alert)

        return deduped
