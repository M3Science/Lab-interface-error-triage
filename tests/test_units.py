"""Focused tests for the parser and individual checks."""

from hl7_triage.parser import parse_message
from hl7_triage.reference import TestDef
from hl7_triage.rules import BatchContext, check_message, parse_hl7_ts

GLUCOSE = TestDef("2345-7", "Glucose", "mg/dL", 70, 99, 40, 450)


def ctx():
    return BatchContext(catalog={"2345-7": GLUCOSE}, orders={"A1": "M1"})


def build(obx="OBX|1|NM|2345-7^Glucose^LN||92|mg/dL|70-99|N|||F", mrn="M1", acc="A1", ctrl="C1"):
    return "\r".join([
        f"MSH|^~\\&|APP|FAC|LIS|HOSP|20260115103000||ORU^R01|{ctrl}|P|2.5.1",
        f"PID|1||{mrn}^^^HOSP^MR||ZZTEST^A||19800101|F",
        f"OBR|1|O1|{acc}|CMP^Panel^L|||20260115080000",
        obx,
    ])


def codes(text, c=None):
    return {f.code for f in check_message(parse_message(text, "t.hl7"), c or ctx())}


def test_msh_field_numbering_is_offset():
    msh = parse_message(build()).first("MSH")
    assert msh.field(1) == "|"
    assert msh.field(2) == "^~\\&"
    assert msh.field(9) == "ORU^R01"
    assert msh.field(10) == "C1"


def test_component_access():
    pid = parse_message(build()).first("PID")
    assert pid.component(3, 1) == "M1"
    assert pid.component(3, 4) == "HOSP"


def test_all_line_endings_parse_the_same():
    text = build()
    for sep in ("\r", "\n", "\r\n"):
        assert len(parse_message(text.replace("\r", sep)).segments) == 4


def test_clean_message_has_no_findings():
    assert codes(build()) == set()


def test_timestamp_validation():
    assert parse_hl7_ts("20260115") is not None
    assert parse_hl7_ts("202601151030-0600") is not None
    assert parse_hl7_ts("20261345") is None      # month 13
    assert parse_hl7_ts("2026-01-15") is None


def test_hh_flag_accepted_for_high_value():
    obx = "OBX|1|NM|2345-7^Glucose^LN||500|mg/dL|70-99|HH|||F"
    assert codes(build(obx)) == {"CRITICAL_VALUE"}


def test_empty_flag_on_abnormal_value_is_mismatch():
    obx = "OBX|1|NM|2345-7^Glucose^LN||150|mg/dL|70-99||||F"
    assert codes(build(obx)) == {"ABNORMAL_FLAG_MISMATCH"}


def test_unit_mismatch_skips_flag_and_critical_checks():
    obx = "OBX|1|NM|2345-7^Glucose^LN||2.0|mmol/L|70-99|N|||F"
    assert codes(build(obx)) == {"UNIT_MISMATCH"}


def test_corrected_result_is_not_duplicate():
    c = ctx()
    codes(build(), c)
    corrected = "OBX|1|NM|2345-7^Glucose^LN||95|mg/dL|70-99|N|||C"
    assert codes(build(corrected, ctrl="C2"), c) == set()


def test_second_final_is_duplicate():
    c = ctx()
    codes(build(), c)
    assert codes(build(ctrl="C2"), c) == {"DUPLICATE_RESULT"}
