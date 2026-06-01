"""Synthetic AML transaction/account data generation for TyCAT demos.

This module creates a deterministic demo dataset used in experiments. Illicit
patterns are injected for all 8 FinCEN AML/CFT priorities (June 30, 2021),
which supports AMLA 2020 Section 6209 style technology testing workflows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


_SANCTIONED = ["KP", "IR", "SY", "CU"]


def _random_account_ids(rng: np.random.Generator, n: int, prefix: str = "ACC") -> list[str]:
    return [f"{prefix}{i:05d}" for i in rng.choice(200000, size=n, replace=False)]


def generate_demo(
    n: int = 50_000,
    n_accounts: int = 5_000,
    illicit_fraction: float = 0.002,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate demo transactions and accounts for experimentation."""

    rng = np.random.default_rng(seed)

    account_ids = [f"ACC{i:05d}" for i in range(n_accounts)]
    countries = np.array(["US", "GB", "AE", "SG", "DE", "IN", "CA"])

    accounts_df = pd.DataFrame(
        {
            "account_id": account_ids,
            "account_type": rng.choice(["retail", "business", "ngo"], size=n_accounts, p=[0.72, 0.25, 0.03]),
            "country": rng.choice(countries, size=n_accounts),
            "kyc_complete": rng.choice([True, False], size=n_accounts, p=[0.93, 0.07]),
            "is_pep": rng.choice([True, False], size=n_accounts, p=[0.02, 0.98]),
            "age": rng.integers(18, 85, size=n_accounts),
        }
    )

    illicit_total = max(8, int(n * illicit_fraction))
    legit_total = max(0, n - illicit_total)

    base_ts = pd.Timestamp("2026-01-01")

    legit_df = pd.DataFrame(
        {
            "tx_id": [f"TX{i:08d}" for i in range(legit_total)],
            "src_account": rng.choice(account_ids, size=legit_total),
            "dst_account": rng.choice(account_ids, size=legit_total),
            "amount": np.round(rng.gamma(shape=2.0, scale=1200.0, size=legit_total), 2),
            "currency": rng.choice(["USD", "EUR", "GBP"], size=legit_total, p=[0.86, 0.08, 0.06]),
            "payment_type": rng.choice(["wire", "card", "ach", "p2p"], size=legit_total, p=[0.2, 0.35, 0.3, 0.15]),
            "timestamp": [base_ts + pd.Timedelta(minutes=int(x)) for x in rng.integers(0, 60 * 24 * 120, size=legit_total)],
            "src_country": rng.choice(countries, size=legit_total),
            "dst_country": rng.choice(countries, size=legit_total),
            "is_laundering": np.zeros(legit_total, dtype=int),
            "typology": np.array(["legit"] * legit_total),
        }
    )

    typologies = [
        "shell_company",               # P1
        "crypto_layering",             # P2
        "small_value_funnel",          # P3
        "account_takeover",            # P4
        "trade_based_ml",              # P5
        "bulk_cash_structuring",       # P6
        "hotel_transport_pattern",     # P7
        "sanctioned_jurisdiction",     # P8
    ]

    base_alloc = illicit_total // 8
    remainder = illicit_total % 8
    alloc = [base_alloc + (1 if i < remainder else 0) for i in range(8)]

    rows: list[dict[str, Any]] = []
    tx_counter = legit_total

    def new_tx_id() -> str:
        nonlocal tx_counter
        tx_counter += 1
        return f"TX{tx_counter:08d}"

    for code, count in zip(typologies, alloc):
        if count == 0:
            continue

        if code == "shell_company":
            # P1 corruption: 4-hop circular wire chain with large values.
            for _ in range(count):
                chain = _random_account_ids(rng, 4, prefix="SH")
                src = chain[_ % 4]
                dst = chain[(_ + 1) % 4]
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": src,
                        "dst_account": dst,
                        "amount": float(np.round(rng.uniform(80_000, 250_000), 2)),
                        "currency": "USD",
                        "payment_type": "wire",
                        "timestamp": base_ts + pd.Timedelta(minutes=int(rng.integers(0, 60 * 24 * 90))),
                        "src_country": "US",
                        "dst_country": rng.choice(["AE", "SG", "GB"]),
                        "is_laundering": 1,
                        "typology": code,
                    }
                )
        elif code == "crypto_layering":
            # P2 cybercrime: burst transfers to CRYPTO_MIX endpoints within <1h.
            src = _random_account_ids(rng, 1, prefix="CY")[0]
            base = base_ts + pd.Timedelta(days=5)
            for i in range(count):
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": src,
                        "dst_account": f"CRYPTO_MIX_{i % 5}",
                        "amount": float(np.round(rng.uniform(4_000, 40_000), 2)),
                        "currency": "USD",
                        "payment_type": "wire",
                        "timestamp": base + pd.Timedelta(minutes=int(i % 50)),
                        "src_country": "US",
                        "dst_country": rng.choice(["US", "SG"]),
                        "is_laundering": 1,
                        "typology": code,
                    }
                )
        elif code == "small_value_funnel":
            # P3 terrorist financing: 6+ sources to one destination at sub-$950 values.
            dst = _random_account_ids(rng, 1, prefix="TF")[0]
            srcs = _random_account_ids(rng, max(6, count), prefix="SRC")
            for i in range(count):
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": srcs[i % len(srcs)],
                        "dst_account": dst,
                        "amount": float(np.round(rng.uniform(150, 949), 2)),
                        "currency": "USD",
                        "payment_type": "p2p",
                        "timestamp": base_ts + pd.Timedelta(days=8, minutes=int(i * 8)),
                        "src_country": "US",
                        "dst_country": "US",
                        "is_laundering": 1,
                        "typology": code,
                    }
                )
        elif code == "account_takeover":
            # P4 fraud: rapid card burst (>=4 tx within 30 min) on victim account.
            victim = _random_account_ids(rng, 1, prefix="VIC")[0]
            for i in range(count):
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": victim,
                        "dst_account": _random_account_ids(rng, 1, prefix="MER")[0],
                        "amount": float(np.round(rng.uniform(250, 1200), 2)),
                        "currency": "USD",
                        "payment_type": "card",
                        "timestamp": base_ts + pd.Timedelta(days=12, minutes=int(i % 28)),
                        "src_country": "US",
                        "dst_country": "US",
                        "is_laundering": 1,
                        "typology": code,
                    }
                )
        elif code == "trade_based_ml":
            # P5 TCO: over-invoiced wires above $150k.
            for _ in range(count):
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": _random_account_ids(rng, 1, prefix="IMP")[0],
                        "dst_account": _random_account_ids(rng, 1, prefix="EXP")[0],
                        "amount": float(np.round(rng.uniform(150_001, 480_000), 2)),
                        "currency": "USD",
                        "payment_type": "wire",
                        "timestamp": base_ts + pd.Timedelta(days=20, minutes=int(rng.integers(0, 1200))),
                        "src_country": "US",
                        "dst_country": rng.choice(["AE", "HK", "SG"]),
                        "is_laundering": 1,
                        "typology": code,
                    }
                )
        elif code == "bulk_cash_structuring":
            # P6 DTO: repeated cash deposits in $9,100-$9,950 band.
            src = _random_account_ids(rng, 1, prefix="BC")[0]
            for i in range(count):
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": src,
                        "dst_account": src,
                        "amount": float(np.round(rng.uniform(9_100, 9_950), 2)),
                        "currency": "USD",
                        "payment_type": "cash_deposit",
                        "timestamp": base_ts + pd.Timedelta(days=30 + int(i % 14), minutes=int(i * 5)),
                        "src_country": "US",
                        "dst_country": "US",
                        "is_laundering": 1,
                        "typology": code,
                    }
                )
        elif code == "hotel_transport_pattern":
            # P7 trafficking/smuggling indicator: recurring hotel + transport spend.
            merchants = ["HOTEL_CHAIN", "TRANSPORT_SERVICE"]
            src = _random_account_ids(rng, 1, prefix="HT")[0]
            for i in range(count):
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": src,
                        "dst_account": merchants[i % 2],
                        "amount": float(np.round(rng.uniform(120, 2200), 2)),
                        "currency": "USD",
                        "payment_type": "card",
                        "timestamp": base_ts + pd.Timedelta(days=40 + (i % 21), hours=int(i % 6)),
                        "src_country": "US",
                        "dst_country": "US",
                        "is_laundering": 1,
                        "typology": code,
                    }
                )
        elif code == "sanctioned_jurisdiction":
            # P8 proliferation financing: wires to KP/IR/SY/CU.
            for i in range(count):
                rows.append(
                    {
                        "tx_id": new_tx_id(),
                        "src_account": _random_account_ids(rng, 1, prefix="SX")[0],
                        "dst_account": _random_account_ids(rng, 1, prefix="DX")[0],
                        "amount": float(np.round(rng.uniform(20_001, 300_000), 2)),
                        "currency": "USD",
                        "payment_type": "wire",
                        "timestamp": base_ts + pd.Timedelta(days=50, minutes=int(i * 19)),
                        "src_country": "US",
                        "dst_country": _SANCTIONED[i % len(_SANCTIONED)],
                        "is_laundering": 1,
                        "typology": code,
                    }
                )

    illicit_df = pd.DataFrame(rows)
    tx_df = pd.concat([legit_df, illicit_df], ignore_index=True)
    tx_df["timestamp"] = pd.to_datetime(tx_df["timestamp"])

    # Keep deterministic order for reproducibility and test snapshots.
    tx_df = tx_df.sort_values("tx_id").reset_index(drop=True)

    return tx_df, accounts_df


def write_demo(out_dir: str | Path = "data", seed: int = 42) -> tuple[Path, Path]:
    """Generate and write demo CSV files."""

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    tx_df, accounts_df = generate_demo(seed=seed)
    tx_path = out_path / "demo_transactions.csv"
    accounts_path = out_path / "demo_accounts.csv"
    tx_df.to_csv(tx_path, index=False)
    accounts_df.to_csv(accounts_path, index=False)
    return tx_path, accounts_path
