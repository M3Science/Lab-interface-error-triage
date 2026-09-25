"""Generate the synthetic dataset in data/.

Everything here is invented. Patients use the ZZTEST last name, the same
convention labs use to mark test patients so they are never confused with
real ones. Reference and critical ranges are illustrative only and are not
clinical guidance.

Run from the repo root:  python scripts/generate_samples.py
Outputs:
  data/test_catalog.csv    test build (codes, units, ranges)
  data/orders.csv          open orders: accession -> patient MRN
  data/messages/*.hl7      one ORU^R01 message per file
  data/expected_faults.csv the faults each message SHOULD trigger (answer key)
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MSG_DIR = DATA / "messages"

# code, name, unit, ref_low, ref_high, crit_low, crit_high  (LOINC codes; illustrative ranges)
CATALOG = [
    ("2345-7", "Glucose", "mg/dL", 70, 99, 40, 450),
    ("2823-3", "Potassium", "mmol/L", 3.5, 5.1, 2.8, 6.2),
    ("2951-2", "Sodium", "mmol/L", 136, 145, 120, 160),
    ("2160-0", "Creatinine", "mg/dL", 0.6, 1.3, "", ""),
    ("718-7", "Hemoglobin", "g/dL", 12.0, 17.5, 7.0, 20.0),
    ("6690-2", "WBC", "10*3/uL", 4.5, 11.0, 2.0, 30.0),
    ("777-3", "Platelets", "10*3/uL", 150, 400, 20, 1000),
]
TESTS = {c[0]: c for c in CATALOG}

PATIENTS = [  # mrn, name, dob, sex
    ("TST10001", "ZZTEST^ALPHA", "19800312", "F"),
    ("TST10002", "ZZTEST^BRAVO", "19751120", "M"),
    ("TST10003", "ZZTEST^CHARLIE", "19920604", "F"),
    ("TST10004", "ZZTEST^DELTA", "19680829", "M"),
    ("TST10005", "ZZTEST^ECHO", "20010115", "F"),
    ("TST10006", "ZZTEST^FOXTROT", "19590407", "M"),
]


def flag_for(code: str, value: float) -> str:
    _, _, _, lo, hi, clo, chi = TESTS[code]
    if clo != "" and value < clo:
        return "LL"
    if chi != "" and value > chi:
        return "HH"
    if value < lo:
        return "L"
    if value > hi:
        return "H"
    return "N"


def obx(i, code, value, unit=None, flag=None, status="F", vtype="NM"):
    name = TESTS[code][1] if code in TESTS else "UNKNOWN"
    unit = TESTS[code][2] if unit is None and code in TESTS else (unit or "")
    if flag is None:
        try:
            flag = flag_for(code, float(value))
        except (ValueError, KeyError):
            flag = ""
    rng = f"{TESTS[code][3]}-{TESTS[code][4]}" if code in TESTS else ""
    return f"OBX|{i}|{vtype}|{code}^{name}^LN||{value}|{unit}|{rng}|{flag}|||{status}"


def message(ctrl, accession, patient, results, msg_time="20260115103000",
            collected="20260115081500", msg_type="ORU^R01", mrn_override=None, extra=None):
    mrn, name, dob, sex = patient
    mrn = mrn if mrn_override is None else mrn_override
    segs = [
        f"MSH|^~\\&|ANALYZER_SIM|DEMO_LAB|LIS_SIM|DEMO_HOSP|{msg_time}||{msg_type}|{ctrl}|P|2.5.1",
        f"PID|1||{mrn}^^^DEMO_HOSP^MR||{name}||{dob}|{sex}",
        f"ORC|RE|ORD{accession[-4:]}|{accession}",
        f"OBR|1|ORD{accession[-4:]}|{accession}|CMP^Chemistry Panel^L|||{collected}",
    ]
    segs += [obx(i, *r) if isinstance(r, tuple) else r for i, r in enumerate(results, start=1)]
    if extra:
        segs.insert(extra[0], extra[1])
    return "\n".join(segs) + "\n"


def bmp(k="4.1", na="140", glu="92"):
    return [("2823-3", k), ("2951-2", na), ("2345-7", glu)]


def cbc(wbc="7.2", hgb="13.8", plt="245"):
    return [("6690-2", wbc), ("718-7", hgb), ("777-3", plt)]


P = PATIENTS
# (file stem, accession, patient, msg kwargs, expected fault codes, description)
CASES = [
    ("001_clean_bmp", "A26000001", P[0], dict(ctrl="MSG0001", results=bmp()), [], "Normal chemistry"),
    ("002_clean_cbc", "A26000002", P[1], dict(ctrl="MSG0002", results=cbc()), [], "Normal CBC"),
    ("003_clean_high_glucose", "A26000003", P[2], dict(ctrl="MSG0003", results=bmp(glu="182")), [],
     "High glucose, correctly flagged H"),
    ("004_clean_low_hgb", "A26000004", P[3], dict(ctrl="MSG0004", results=cbc(hgb="10.9")), [],
     "Low hemoglobin, correctly flagged L"),
    ("005_clean_creatinine", "A26000005", P[4], dict(ctrl="MSG0005", results=[("2160-0", "0.9")]), [],
     "Single test"),
    ("006_clean_bmp", "A26000006", P[5], dict(ctrl="MSG0006", results=bmp("3.9", "138", "88")), [], "Normal chemistry"),
    ("007_clean_cbc_high_wbc", "A26000007", P[0], dict(ctrl="MSG0007", results=cbc(wbc="14.6")), [],
     "High WBC, correctly flagged H"),
    ("008_clean_preliminary", "A26000008", P[1], dict(ctrl="MSG0008", results=[("2345-7", "101", None, None, "P")]), [],
     "Preliminary (P) result"),
    ("009_clean_cannot_obtain", "A26000009", P[2], dict(ctrl="MSG0009", results=[("2823-3", "", None, "", "X")]), [],
     "Status X with empty value is valid"),
    ("010_clean_bmp", "A26000010", P[3], dict(ctrl="MSG0010", results=bmp("4.8", "143", "97")), [], "Normal chemistry"),
    ("011_clean_cbc", "A26000011", P[4], dict(ctrl="MSG0011", results=cbc("5.1", "12.4", "160")), [], "Normal CBC"),
    ("012_clean_crlf", "A26000012", P[5], dict(ctrl="MSG0012", results=bmp()), [],
     "Saved with CRLF/CR line endings"),
    ("013_missing_mrn", "A26000013", P[0], dict(ctrl="MSG0013", results=bmp(), mrn_override=""),
     ["MISSING_REQUIRED_FIELD"], "PID-3 empty"),
    ("014_missing_accession", "", P[1], dict(ctrl="MSG0014", results=bmp()),
     ["MISSING_REQUIRED_FIELD"], "OBR-3 empty"),
    ("015_accession_not_found", "A26009999", P[2], dict(ctrl="MSG0015", results=bmp()),
     ["ACCESSION_NOT_FOUND"], "No order for this accession"),
    ("016_patient_mismatch", "A26000016", P[3], dict(ctrl="MSG0016", results=bmp(), mrn_override="TST10005"),
     ["PATIENT_ID_MISMATCH"], "MRN differs from the order"),
    ("017_non_numeric", "A26000017", P[4], dict(ctrl="MSG0017", results=[("2823-3", "HEMOLYZED", None, "")]),
     ["NON_NUMERIC_VALUE"], "Specimen comment in the value field"),
    ("018_unit_mismatch", "A26000018", P[5], dict(ctrl="MSG0018", results=[("2345-7", "5.4", "mmol/L", "N")]),
     ["UNIT_MISMATCH"], "Glucose in SI units, LIS expects mg/dL"),
    ("019_critical_high_k", "A26000019", P[0], dict(ctrl="MSG0019", results=bmp(k="6.8")),
     ["CRITICAL_VALUE"], "Critical potassium"),
    ("020_flag_mismatch", "A26000020", P[1], dict(ctrl="MSG0020", results=[("2951-2", "150", None, "N")]),
     ["ABNORMAL_FLAG_MISMATCH"], "Sodium 150 flagged normal"),
    ("021_unknown_test", "A26000021", P[2], dict(ctrl="MSG0021", results=[("99999-9", "12.0", "U/L", "")]),
     ["UNKNOWN_TEST_CODE"], "Assay not built in the LIS"),
    ("022_invalid_status", "A26000022", P[3], dict(ctrl="MSG0022", results=[("2345-7", "90", None, None, "Z")]),
     ["INVALID_RESULT_STATUS"], "Status Z from middleware"),
    ("023_missing_value", "A26000023", P[4], dict(ctrl="MSG0023", results=[("2345-7", "", None, "", "F")]),
     ["MISSING_REQUIRED_FIELD"], "Final result with no value"),
    ("024_malformed_line", "A26000024", P[5],
     dict(ctrl="MSG0024", results=bmp(), extra=(4, "NTE results verified by tech")),
     ["MALFORMED_SEGMENT"], "Free text line without segment structure"),
    ("025_missing_pid", "A26000025", P[0], dict(ctrl="MSG0025", results=bmp()),
     ["MISSING_SEGMENT"], "No PID segment"),
    ("026_wrong_type", "A26000026", P[1], dict(ctrl="MSG0026", results=bmp(), msg_type="ADT^A01"),
     ["WRONG_MESSAGE_TYPE"], "ADT message on the results feed"),
    ("027_bad_timestamp", "A26000027", P[2], dict(ctrl="MSG0027", results=bmp(), msg_time="2026-01-15 10:30"),
     ["INVALID_DATETIME"], "MSH-7 in the wrong format"),
    ("028_future_collection", "A26000028", P[3],
     dict(ctrl="MSG0028", results=bmp(), collected="20260115143000"),
     ["INVALID_DATETIME"], "Collected after the message was sent (clock drift)"),
    ("029_duplicate_message", "A26000001", P[0], dict(ctrl="MSG0001", results=bmp()),
     ["DUPLICATE_MESSAGE", "DUPLICATE_RESULT"], "Resend of message 001 after ACK timeout"),
    ("030_duplicate_final", "A26000002", P[1], dict(ctrl="MSG0030", results=[("718-7", "13.1")]),
     ["DUPLICATE_RESULT"], "Rerun sent as F instead of C"),
    ("031_clean_corrected", "A26000003", P[2],
     dict(ctrl="MSG0031", results=[("2345-7", "176", None, None, "C")]), [],
     "Correction sent properly as C"),
    ("032_missing_control_id", "A26000032", P[3], dict(ctrl="", results=bmp()),
     ["MISSING_REQUIRED_FIELD"], "MSH-10 empty"),
    ("033_critical_low_glucose", "A26000033", P[4], dict(ctrl="MSG0033", results=bmp(glu="32")),
     ["CRITICAL_VALUE"], "Critical glucose"),
    ("034_multi_fault", "A26000034", P[5],
     dict(ctrl="MSG0034", results=[("6690-2", "CLOTTED", None, "")], mrn_override=""),
     ["MISSING_REQUIRED_FIELD", "NON_NUMERIC_VALUE"], "Missing MRN and clotted specimen comment"),
]

# Accessions that should NOT have an order (to test ACCESSION_NOT_FOUND)
NO_ORDER = {"A26009999", ""}
# Order belongs to a different patient than the message claims
ORDER_PATIENT_OVERRIDE = {"A26000016": "TST10004"}


def main() -> None:
    MSG_DIR.mkdir(parents=True, exist_ok=True)
    for old in MSG_DIR.glob("*.hl7"):
        old.unlink()

    with open(DATA / "test_catalog.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "unit", "ref_low", "ref_high", "crit_low", "crit_high"])
        w.writerows(CATALOG)

    orders = {}
    for stem, acc, patient, kw, _, _ in CASES:
        if acc not in NO_ORDER:
            orders.setdefault(acc, ORDER_PATIENT_OVERRIDE.get(acc, patient[0]))
    with open(DATA / "orders.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["accession", "mrn"])
        w.writerows(sorted(orders.items()))

    with open(DATA / "expected_faults.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["message", "expected_faults", "scenario"])
        for stem, acc, patient, kw, expected, desc in CASES:
            text = message(accession=acc, patient=patient, **kw)
            if stem == "025_missing_pid":
                text = "\n".join(l for l in text.splitlines() if not l.startswith("PID")) + "\n"
            if stem == "012_clean_crlf":
                text = text.replace("\n", "\r\n")
            with open(MSG_DIR / f"{stem}.hl7", "w", encoding="utf-8", newline="") as out:
                out.write(text)
            w.writerow([f"{stem}.hl7", ";".join(sorted(expected)), desc])

    print(f"Wrote {len(CASES)} messages, {len(orders)} orders, {len(CATALOG)} tests to {DATA}")


if __name__ == "__main__":
    main()
