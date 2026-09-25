"""Loads the reference files the checks compare against.

In a real lab these would come from the LIS test build and the order
database. Here they are small CSV files of synthetic data.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestDef:
    __test__ = False  # tell pytest this is not a test class

    code: str
    name: str
    unit: str
    ref_low: float | None
    ref_high: float | None
    crit_low: float | None
    crit_high: float | None


def _num(value: str) -> float | None:
    value = (value or "").strip()
    return float(value) if value else None


def load_catalog(path: str | Path) -> dict[str, TestDef]:
    catalog = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            catalog[row["code"]] = TestDef(
                code=row["code"],
                name=row["name"],
                unit=row["unit"],
                ref_low=_num(row["ref_low"]),
                ref_high=_num(row["ref_high"]),
                crit_low=_num(row["crit_low"]),
                crit_high=_num(row["crit_high"]),
            )
    return catalog


def load_orders(path: str | Path) -> dict[str, str]:
    """Return {accession: mrn}."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["accession"]: row["mrn"] for row in csv.DictReader(f)}
