"""Evaluation metrics for TyCAT experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

import pandas as pd

from .llm_generator import TestSpec
from .typology_mapper import FINCEN_PRIORITIES, map_priority_to_typologies


@dataclass(frozen=True)
class Mutant:
    """Detector mutant used for mutation testing."""

    mutant_id: str
    description: str
    apply: Callable[[pd.DataFrame], list[dict[str, Any]]]


def typology_coverage(specs: Iterable[TestSpec]) -> float:
    """Compute typology coverage ratio over the fixed catalog size (24)."""

    covered = {spec.typology for spec in specs}
    return len(covered) / 24.0


def priority_coverage(specs: Iterable[TestSpec]) -> float:
    """Compute ratio of priorities for which all mapped typologies are covered."""

    covered = {spec.typology for spec in specs}
    full = 0
    for priority in FINCEN_PRIORITIES:
        required = {t.code for t in map_priority_to_typologies(priority)}
        if required.issubset(covered):
            full += 1
    return full / 8.0


def mutation_score(
    test_dfs: Iterable[pd.DataFrame],
    expected_alerts: Iterable[set[str]],
    original_detector: Callable[[pd.DataFrame], list[dict[str, Any]]],
    mutants: Iterable[Mutant],
) -> float:
    """Compute mutation score.

    A mutant is killed if any test dataset produces a different alert tx_id set
    compared with the reference outcome (expected_alerts when provided, else
    original detector outputs).
    """

    tests = list(test_dfs)
    expected_list = list(expected_alerts)

    if expected_list and len(expected_list) != len(tests):
        raise ValueError("expected_alerts length must match number of test datasets")

    if not expected_list:
        expected_list = [{a["tx_id"] for a in original_detector(df)} for df in tests]

    mutants_list = list(mutants)
    if not mutants_list:
        return 0.0

    killed = 0
    for mutant in mutants_list:
        is_killed = False
        for df, expected in zip(tests, expected_list):
            got = {a["tx_id"] for a in mutant.apply(df)}
            if got != expected:
                is_killed = True
                break
        if is_killed:
            killed += 1

    return killed / len(mutants_list)


def fp_reduction_estimate(
    baseline_alerts: set[str],
    augmented_alerts: set[str],
    ground_truth: set[str],
) -> dict[str, float]:
    """Estimate FP-rate reduction and recall delta for augmented pipeline."""

    def _fp_rate(alerts: set[str]) -> float:
        if not alerts:
            return 0.0
        fp = len(alerts - ground_truth)
        return fp / len(alerts)

    def _recall(alerts: set[str]) -> float:
        if not ground_truth:
            return 1.0
        tp = len(alerts & ground_truth)
        return tp / len(ground_truth)

    baseline_fp = _fp_rate(baseline_alerts)
    augmented_fp = _fp_rate(augmented_alerts)
    baseline_recall = _recall(baseline_alerts)
    augmented_recall = _recall(augmented_alerts)

    relative_reduction = 0.0
    if baseline_fp > 0:
        relative_reduction = (baseline_fp - augmented_fp) / baseline_fp

    return {
        "baseline_fp_rate": baseline_fp,
        "augmented_fp_rate": augmented_fp,
        "relative_reduction": relative_reduction,
        "recall_delta_pp": (augmented_recall - baseline_recall) * 100.0,
    }
