"""Render docs/RUNBOOK.md from hl7_triage/faults.py (run from the repo root)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hl7_triage.faults import FAULTS, SEVERITY_ORDER  # noqa: E402

HEADER = """# Troubleshooting Runbook: Lab Result Interface Faults

This runbook is written for the first person who sees an interface error:
bench staff, a support desk, or an LIS analyst on call. Each entry says what
the fault means, why it usually happens, what to do first, and who to
escalate to.

**Golden rule:** when a result's identity or meaning is in doubt, hold it.
A delayed result is recoverable; a wrong result on the wrong patient may not be.

## Escalation tiers

| Tier | Who | Handles |
|---|---|---|
| 1 | Bench / support desk | First look, hold the result, request a resend, fix at the source |
| 2 | LIS analyst | Test build, code mappings, reference ranges, status mappings |
| 3 | Interface team / vendor | Channel routing, message format, ACK and resend settings |

## Quick reference

| Severity | Code | Fault |
|---|---|---|
"""


def main() -> None:
    items = sorted(FAULTS.items(), key=lambda kv: (SEVERITY_ORDER[kv[1]["severity"]], kv[0]))
    out = [HEADER.rstrip("\n")]
    for code, f in items:
        out.append(f"| {f['severity']} | [`{code}`](#{code.lower()}) | {f['title']} |")
    out.append("")
    for code, f in items:
        out += [
            f"## {code}",
            "",
            f"**{f['title']}** (severity: {f['severity']})",
            "",
            f"- **What it means:** {f['meaning']}",
            f"- **Common causes:** {f['causes']}",
            f"- **First steps:** {f['fix']}",
            f"- **Escalate:** {f['escalate']}",
            "",
        ]
    (ROOT / "docs" / "RUNBOOK.md").write_text("\n".join(out), encoding="utf-8")
    print("Wrote docs/RUNBOOK.md")


if __name__ == "__main__":
    main()
