"""Turns findings into a plain-language Markdown report and a CSV log."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from .faults import FAULTS, SEVERITY_ORDER
from .rules import Finding


def write_csv(findings: list[Finding], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["message", "severity", "code", "location", "detail"])
        for x in findings:
            w.writerow([x.source, x.severity, x.code, x.location, x.detail])


def build_markdown(sources: list[str], findings: list[Finding]) -> str:
    by_source: dict[str, list[Finding]] = {s: [] for s in sources}
    for f in findings:
        by_source[f.source].append(f)

    flagged = [s for s, fs in by_source.items() if fs]
    held = [s for s, fs in by_source.items()
            if any(f.severity == "high" and f.code != "CRITICAL_VALUE" for f in fs)]
    critical = [s for s, fs in by_source.items() if any(f.code == "CRITICAL_VALUE" for f in fs)]
    counts = Counter(f.code for f in findings)

    lines = [
        "# Lab Interface Triage Report",
        "",
        "## Summary",
        "",
        "| Measure | Count |",
        "|---|---|",
        f"| Messages checked | {len(sources)} |",
        f"| Clean (no findings) | {len(sources) - len(flagged)} |",
        f"| With findings | {len(flagged)} |",
        f"| Hold - high-severity interface fault | {len(held)} |",
        f"| Critical values needing a call | {len(critical)} |",
        "",
        "## Findings by type",
        "",
        "| Severity | Code | What it means | Count |",
        "|---|---|---|---|",
    ]
    for code, n in sorted(counts.items(), key=lambda kv: (SEVERITY_ORDER[FAULTS[kv[0]]["severity"]], -kv[1])):
        lines.append(f"| {FAULTS[code]['severity']} | `{code}` | {FAULTS[code]['title']} | {n} |")

    lines += ["", "## Message detail", ""]
    for source in flagged:
        fs = sorted(by_source[source], key=lambda f: SEVERITY_ORDER[f.severity])
        lines.append(f"### {source}")
        lines.append("")
        for f in fs:
            lines.append(f"- **{f.severity.upper()} - `{f.code}`** at {f.location}: {f.detail}")
            lines.append(f"  - Next step: {FAULTS[f.code]['fix']}")
        lines.append("")

    lines.append("See docs/RUNBOOK.md for causes and escalation paths for each finding.")
    return "\n".join(lines) + "\n"
