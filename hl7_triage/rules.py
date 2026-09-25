"""Validation checks for lab result messages.

Each check looks at one parsed message and returns Findings. A shared
BatchContext lets checks spot duplicates across a whole batch of messages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from .faults import FAULTS
from .parser import Message
from .reference import TestDef

VALID_RESULT_STATUS = {"F", "P", "C", "X", "R", "I", "S", "D", "W"}
HL7_TS = re.compile(r"^(\d{8})(\d{4})?(\d{2})?([+-]\d{4})?$")


@dataclass
class Finding:
    source: str
    code: str
    location: str
    detail: str

    @property
    def severity(self) -> str:
        return FAULTS[self.code]["severity"]


@dataclass
class BatchContext:
    catalog: dict[str, TestDef]
    orders: dict[str, str]
    seen_control_ids: set[str] = field(default_factory=set)
    seen_final_results: set[tuple[str, str]] = field(default_factory=set)


def parse_hl7_ts(value: str) -> datetime | None:
    """Parse an HL7 timestamp (YYYYMMDD[HHMM[SS]][+/-ZZZZ]). None if invalid."""
    m = HL7_TS.match(value)
    if not m:
        return None
    date, hm, sec = m.group(1), m.group(2) or "0000", m.group(3) or "00"
    try:
        return datetime.strptime(date + hm + sec, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def parse_number(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def expected_flag(value: float, test: TestDef) -> str:
    if test.ref_low is not None and value < test.ref_low:
        return "L"
    if test.ref_high is not None and value > test.ref_high:
        return "H"
    return "N"


def check_message(msg: Message, ctx: BatchContext) -> list[Finding]:
    out: list[Finding] = []

    def add(code: str, location: str, detail: str) -> None:
        out.append(Finding(msg.source, code, location, detail))

    # --- Structure -------------------------------------------------------
    for line_no, raw in msg.malformed:
        add("MALFORMED_SEGMENT", f"line {line_no}", f"'{raw[:40]}'")

    msh = msg.first("MSH")
    if msh is None or msg.segments[0].name != "MSH":
        add("MISSING_SEGMENT", "MSH", "Message must start with an MSH segment")
        return out

    msg_type = f"{msh.component(9, 1)}^{msh.component(9, 2)}"
    if msg_type != "ORU^R01":
        add("WRONG_MESSAGE_TYPE", "MSH-9", f"Got {msg_type}, expected ORU^R01")
        return out

    for seg in ("PID", "OBR", "OBX"):
        if msg.first(seg) is None:
            add("MISSING_SEGMENT", seg, f"No {seg} segment")

    # --- Header ------------------------------------------------------------
    control_id = msh.field(10)
    if not control_id:
        add("MISSING_REQUIRED_FIELD", "MSH-10", "Message control ID is empty")
    elif control_id in ctx.seen_control_ids:
        add("DUPLICATE_MESSAGE", "MSH-10", f"Control ID {control_id} already received")
    else:
        ctx.seen_control_ids.add(control_id)

    msg_time = parse_hl7_ts(msh.field(7))
    if msg_time is None:
        add("INVALID_DATETIME", "MSH-7", f"'{msh.field(7)}' is not a valid HL7 timestamp")

    # --- Patient and order -------------------------------------------------
    pid, obr = msg.first("PID"), msg.first("OBR")
    mrn = pid.component(3, 1) if pid else ""
    accession = obr.component(3, 1) if obr else ""

    if pid and not mrn:
        add("MISSING_REQUIRED_FIELD", "PID-3", "Patient MRN is empty")
    if obr and not accession:
        add("MISSING_REQUIRED_FIELD", "OBR-3", "Accession number is empty")

    if accession:
        if accession not in ctx.orders:
            add("ACCESSION_NOT_FOUND", "OBR-3", f"No order for accession {accession}")
        elif mrn and ctx.orders[accession] != mrn:
            add("PATIENT_ID_MISMATCH", "PID-3",
                f"Message MRN {mrn} but order {accession} belongs to {ctx.orders[accession]}")

    if obr:
        raw_collected = obr.field(7)
        collected = parse_hl7_ts(raw_collected)
        if collected is None:
            add("INVALID_DATETIME", "OBR-7", f"'{raw_collected}' is not a valid HL7 timestamp")
        elif msg_time and collected > msg_time:
            add("INVALID_DATETIME", "OBR-7",
                f"Collection time {raw_collected} is after message time {msh.field(7)}")

    # --- Results -------------------------------------------------------------
    for obx in msg.all("OBX"):
        loc = f"OBX-{obx.field(1) or '?'}"
        code = obx.component(3, 1)
        value = obx.field(5)
        status = obx.field(11)

        if not code:
            add("MISSING_REQUIRED_FIELD", f"{loc} (OBX-3)", "Test code is empty")
            continue
        test = ctx.catalog.get(code)
        label = test.name if test else code

        if not status:
            add("MISSING_REQUIRED_FIELD", f"{loc} (OBX-11)", f"{label}: result status is empty")
        elif status not in VALID_RESULT_STATUS:
            add("INVALID_RESULT_STATUS", f"{loc} (OBX-11)", f"{label}: status '{status}' is not valid")

        if status == "F" and accession:
            key = (accession, code)
            if key in ctx.seen_final_results:
                add("DUPLICATE_RESULT", loc, f"{label}: final result already filed for {accession}")
            ctx.seen_final_results.add(key)

        if test is None:
            add("UNKNOWN_TEST_CODE", f"{loc} (OBX-3)", f"Code {code} is not in the test catalog")
            continue

        if not value:
            if status != "X":  # X = result cannot be obtained, so empty is expected
                add("MISSING_REQUIRED_FIELD", f"{loc} (OBX-5)", f"{label}: result value is empty")
            continue

        number = parse_number(value) if obx.field(2) == "NM" else None
        if obx.field(2) == "NM" and number is None:
            add("NON_NUMERIC_VALUE", f"{loc} (OBX-5)", f"{label}: '{value}' is not a number")
            continue

        unit = obx.component(6, 1)
        if unit != test.unit:
            add("UNIT_MISMATCH", f"{loc} (OBX-6)",
                f"{label}: units '{unit}' but test build expects '{test.unit}'")
            continue  # flags and critical limits are meaningless in the wrong units

        if number is None:
            continue

        if (test.crit_low is not None and number < test.crit_low) or \
           (test.crit_high is not None and number > test.crit_high):
            add("CRITICAL_VALUE", loc, f"{label} {value} {unit} is outside critical limits "
                f"({test.crit_low}-{test.crit_high})")

        want = expected_flag(number, test)
        got = obx.field(8) or "N"
        if got[0] != want:  # HH/LL count as H/L
            add("ABNORMAL_FLAG_MISMATCH", f"{loc} (OBX-8)",
                f"{label} {value}: flag '{got}' but reference range "
                f"{test.ref_low}-{test.ref_high} gives '{want}'")

    return out
