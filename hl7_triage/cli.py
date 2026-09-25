"""Command-line entry point.

Usage:
    python -m hl7_triage data/messages --orders data/orders.csv \
        --catalog data/test_catalog.csv --out reports
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .parser import parse_message
from .reference import load_catalog, load_orders
from .report import build_markdown, write_csv
from .rules import BatchContext, Finding, check_message


def triage_folder(folder: Path, orders: Path, catalog: Path) -> tuple[list[str], list[Finding]]:
    ctx = BatchContext(catalog=load_catalog(catalog), orders=load_orders(orders))
    sources, findings = [], []
    # Sorted so messages are processed in arrival order (file names start with a sequence number)
    for path in sorted(folder.glob("*.hl7")):
        msg = parse_message(path.read_text(encoding="utf-8"), source=path.name)
        sources.append(path.name)
        findings.extend(check_message(msg, ctx))
    return sources, findings


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Triage HL7 v2 lab result messages.")
    p.add_argument("folder", type=Path, help="Folder of .hl7 files")
    p.add_argument("--orders", type=Path, default=Path("data/orders.csv"))
    p.add_argument("--catalog", type=Path, default=Path("data/test_catalog.csv"))
    p.add_argument("--out", type=Path, default=Path("reports"))
    args = p.parse_args(argv)

    sources, findings = triage_folder(args.folder, args.orders, args.catalog)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "triage_report.md").write_text(build_markdown(sources, findings), encoding="utf-8")
    write_csv(findings, args.out / "findings.csv")

    flagged = len({f.source for f in findings})
    print(f"Checked {len(sources)} messages: {len(sources) - flagged} clean, {flagged} with findings.")
    print(f"Report written to {args.out / 'triage_report.md'}")
    return 0
