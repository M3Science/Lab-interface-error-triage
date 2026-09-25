# Lab Interface Triage

![tests](https://github.com/M3Science/lab-interface-triage/actions/workflows/tests.yml/badge.svg)

A Python tool that checks HL7 v2 lab result messages (ORU^R01) for the
interface faults that cause real problems in hospital labs. It also writes a
plain-language triage report that tells support staff what went wrong, what to
do first, and who to escalate to.

I built it from the perspective of a Medical Laboratory Technician who works
every day with results moving between analyzers, the LIS and the EHR. Most
interface problems I see at the bench fall into a small set of patterns. This
project turns those patterns into automated checks and a written runbook.

> **All data in this repository is synthetic.** Patients use the `ZZTEST`
> last name, a common convention for test patients. Reference and critical
> ranges are illustrative only and are not clinical guidance.

## What it catches

| Severity | Fault | Example |
|---|---|---|
| high | `PATIENT_ID_MISMATCH` | MRN on the result differs from the MRN on the order |
| high | `ACCESSION_NOT_FOUND` | Result arrives for an accession with no order |
| high | `UNIT_MISMATCH` | Glucose sent in mmol/L when the LIS expects mg/dL |
| high | `MISSING_REQUIRED_FIELD` | Blank MRN, accession, test code, value or status |
| high | `MISSING_SEGMENT` | No PID segment |
| high | `MALFORMED_SEGMENT` | Free text line with no segment structure |
| high | `WRONG_MESSAGE_TYPE` | ADT message routed to the results feed |
| high | `CRITICAL_VALUE` | Potassium 6.8 mmol/L starts the critical-call workflow |
| medium | `DUPLICATE_MESSAGE` | Resend after an ACK timeout |
| medium | `DUPLICATE_RESULT` | Rerun sent as final (F) instead of corrected (C) |
| medium | `NON_NUMERIC_VALUE` | `HEMOLYZED` in a numeric value field |
| medium | `ABNORMAL_FLAG_MISMATCH` | Sodium 150 flagged as normal |
| medium | `UNKNOWN_TEST_CODE` | New assay not built in the LIS |
| medium | `INVALID_RESULT_STATUS` | Unmapped middleware status code |
| medium | `INVALID_DATETIME` | Collection time later than message time (clock drift) |

Each fault has a runbook entry covering its meaning, common causes, first steps
and escalation tier: **[docs/RUNBOOK.md](docs/RUNBOOK.md)**.

## Quick start

Requires Python 3.10 or newer. The tool has no dependencies; `pytest` is only needed to run the tests.

```bash
git clone https://github.com/M3Science/lab-interface-triage.git
cd lab-interface-triage
python -m hl7_triage data/messages --out reports
```

Output:

```
Checked 34 messages: 13 clean, 21 with findings.
Report written to reports/triage_report.md
```

The run produces two files:
- `reports/triage_report.md`: a summary table, counts by fault type, and per-message findings with next steps. See **[docs/sample_report.md](docs/sample_report.md)**.
- `reports/findings.csv`: one row per finding, for sorting or trending in Excel.

## Sample message

```
MSH|^~\&|ANALYZER_SIM|DEMO_LAB|LIS_SIM|DEMO_HOSP|20260115103000||ORU^R01|MSG0019|P|2.5.1
PID|1||TST10001^^^DEMO_HOSP^MR||ZZTEST^ALPHA||19800312|F
ORC|RE|ORD0019|A26000019
OBR|1|ORD0019|A26000019|CMP^Chemistry Panel^L|||20260115081500
OBX|1|NM|2823-3^Potassium^LN||6.8|mmol/L|3.5-5.1|HH|||F
```

The report entry for this message:

```
HIGH - CRITICAL_VALUE at OBX-1: Potassium 6.8 mmol/L is outside critical limits (2.8-6.2)
  Next step: Verify the result and specimen integrity, notify the responsible provider within
  the policy time limit, use read-back, and document who was called and when.
```

## How it works

```
data/messages/*.hl7 ──> parser ──> checks ──> report (Markdown + CSV)
                                     ^
          data/orders.csv ───────────┤  (accession -> patient MRN)
          data/test_catalog.csv ─────┘  (codes, units, reference and critical ranges)
```

- **`hl7_triage/parser.py`** splits messages into segments, fields and components. It handles HL7 `\r` endings as well as `\n` and `\r\n`, and MSH's offset field numbering.
- **`hl7_triage/rules.py`** holds the checks. A batch context tracks message IDs and final results so duplicates are caught across the whole batch.
- **`hl7_triage/faults.py`** is the fault catalog. The report's next steps and `docs/RUNBOOK.md` are both generated from it, so the tool and the documentation stay in sync.
- **`hl7_triage/report.py`** writes the Markdown report and CSV log.

## Testing

```bash
pip install -r requirements-dev.txt
pytest -v
```

- **47 tests** run on every push through GitHub Actions (Python 3.10 and 3.12).
- The dataset has an answer key (`data/expected_faults.csv`). The tests confirm every one of the 34 messages triggers *exactly* its labeled faults: nothing missed, nothing extra.
- A coverage test confirms every fault type in the catalog appears in at least one sample.
- Unit tests cover edge cases:
  - A corrected (C) result is not a duplicate.
  - `HH` is accepted for a high value.
  - Unit mismatches suppress flag and critical checks, since ranges are meaningless in the wrong units.
  - Status `X` with an empty value is valid.

To regenerate the data or the runbook:

```bash
python scripts/generate_samples.py
python scripts/build_runbook.py
```

## Design decisions

- **Hold rather than guess.** Identity and unit faults are high severity because filing the wrong value to the wrong patient is the worst outcome. The runbook never suggests fixing an identifier by guesswork.
- **Critical values are workflow, not errors.** They are flagged so the critical-call process starts, and the report counts them separately from interface faults.
- **One source of truth.** Fault meanings, causes and fixes live in one file, so updating a runbook step updates the report too.
- **No dependencies.** The parser is intentionally small so reviewers can read every step.

## Limitations

- One OBR per message; multi-order messages are not split.
- Reference ranges are not age- or sex-specific.
- It does not generate ACK messages or connect to a live interface engine; it analyzes saved messages.
- The checks cover common faults, not the full HL7 v2.5.1 specification.

## Skills demonstrated

HL7 v2 message structure · interface troubleshooting · data validation ·
root-cause analysis · escalation design · runbook and SOP writing ·
Python · automated testing · CI with GitHub Actions
