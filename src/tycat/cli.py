"""Command-line interface for TyCAT."""

from __future__ import annotations

import json
from pathlib import Path

import click

from .llm_generator import MockBackend, generate_test_spec
from .synthetic_data import write_demo
from .typology_mapper import FINCEN_PRIORITIES, TYPOLOGY_CATALOG


@click.group()
def main() -> None:
    """TyCAT CLI for demo data and suite generation."""


@main.command("gen-demo")
@click.option("--out-dir", default="data", show_default=True, type=click.Path())
@click.option("--seed", default=42, show_default=True, type=int)
def gen_demo(out_dir: str, seed: int) -> None:
    """Generate demo transaction/account CSV files."""

    tx_path, accounts_path = write_demo(out_dir=out_dir, seed=seed)
    click.echo(f"Wrote: {tx_path}")
    click.echo(f"Wrote: {accounts_path}")


@main.command("gen-suite")
@click.option("--out", default="experiments/generated_suite.json", show_default=True, type=click.Path())
@click.option("--seed", default=42, show_default=True, type=int)
def gen_suite(out: str, seed: int) -> None:
    """Generate typology test suite JSON using deterministic MockBackend."""

    backend = MockBackend(seed=seed)
    specs = [generate_test_spec(t, backend) for t in TYPOLOGY_CATALOG]
    payload = [
        {
            "typology": s.typology,
            "fixture_rows": s.fixture_rows,
            "oracle": s.oracle.to_dict(),
            "coverage_tags": s.coverage_tags,
            "narrative": s.narrative,
        }
        for s in specs
    ]

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    click.echo(f"Wrote suite with {len(payload)} tests to {out_path}")


@main.command("info")
def info() -> None:
    """Print package and compliance alignment details."""

    click.echo("TyCAT v1.0.0")
    click.echo(f"Priorities: {len(FINCEN_PRIORITIES)}")
    click.echo(f"Typologies: {len(TYPOLOGY_CATALOG)}")
    click.echo("Regulatory anchors:")
    click.echo("- FinCEN National AML/CFT Priorities (2021)")
    click.echo("- AMLA 2020 Section 6209 AML technology testing mandate")
    click.echo("- FinCEN NPRM 89 FR 55428 (2024) and 2026 successor docket")
    click.echo("- Interagency MRM guidance (OCC 2026-13 / SR 26-2 / FIL-15-2026)")
    click.echo("- NIST AI RMF 1.0 and NIST AI 600-1")


if __name__ == "__main__":
    main()
