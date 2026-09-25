"""End-to-end test: every synthetic message must trigger exactly its labeled faults."""

import csv
from pathlib import Path

import pytest

from hl7_triage.cli import triage_folder
from hl7_triage.faults import FAULTS

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def results():
    sources, findings = triage_folder(DATA / "messages", DATA / "orders.csv", DATA / "test_catalog.csv")
    got = {s: set() for s in sources}
    for f in findings:
        got[f.source].add(f.code)
    return got, findings


def load_expected():
    with open(DATA / "expected_faults.csv", newline="", encoding="utf-8") as f:
        return [(r["message"], set(filter(None, r["expected_faults"].split(";")))) for r in csv.DictReader(f)]


@pytest.mark.parametrize("message,expected", load_expected())
def test_message_matches_answer_key(results, message, expected):
    got, _ = results
    assert got[message] == expected


def test_dataset_is_large_enough():
    assert len(load_expected()) >= 30


def test_every_fault_type_is_covered_by_samples():
    covered = set().union(*(e for _, e in load_expected()))
    assert covered == set(FAULTS)


def test_every_finding_has_runbook_entry(results):
    _, findings = results
    assert all(f.code in FAULTS for f in findings)
