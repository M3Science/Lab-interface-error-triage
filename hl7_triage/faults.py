"""Fault catalog: the single source of truth for every fault the tool reports.

Each entry doubles as a runbook entry (docs/RUNBOOK.md is generated from
this file by scripts/build_runbook.py), so the tool and the documentation
cannot drift apart.

Escalation tiers used throughout:
  Tier 1 - Bench / support desk (first look, hold result, request resend)
  Tier 2 - LIS analyst (test build, mappings, reference ranges)
  Tier 3 - Interface / integration team or instrument vendor
"""

FAULTS: dict[str, dict[str, str]] = {
    "MALFORMED_SEGMENT": {
        "severity": "high",
        "title": "Line is not a valid HL7 segment",
        "meaning": "A line does not start with a 3-character segment ID followed by '|'.",
        "causes": "Free text or instrument comments inserted without an NTE segment; broken "
                  "line wrapping or segment terminators in the interface engine; truncated transmission.",
        "fix": "Open the raw message in the interface engine. Check segment terminator settings. "
               "Request a resend from the sending system.",
        "escalate": "Tier 3 if it repeats for the same instrument or channel.",
    },
    "MISSING_SEGMENT": {
        "severity": "high",
        "title": "Required segment missing",
        "meaning": "A result message must contain MSH, PID, OBR and at least one OBX segment.",
        "causes": "Sending system mapping error; message split across transmissions; filter "
                  "in the interface engine dropping segments.",
        "fix": "Hold the message. Compare against a known-good message from the same source. "
               "Request a resend.",
        "escalate": "Tier 3 (interface team).",
    },
    "WRONG_MESSAGE_TYPE": {
        "severity": "high",
        "title": "Not a lab result message",
        "meaning": "MSH-9 is not ORU^R01, so this message was routed to the results channel by mistake.",
        "causes": "Routing rule in the interface engine sends ADT/ORM traffic to the result feed.",
        "fix": "Do not process as a result. Confirm the channel routing rules.",
        "escalate": "Tier 3 (interface team) to correct routing.",
    },
    "MISSING_REQUIRED_FIELD": {
        "severity": "high",
        "title": "Required field is empty",
        "meaning": "A field needed to file the result safely is blank (message control ID, "
                   "patient MRN, accession number, test code, result value or result status).",
        "causes": "Manual entry skipped on the instrument; incomplete barcode read; mapping gap.",
        "fix": "Hold the result. Look up the specimen by label or order and correct at the source. "
               "Never guess an identifier.",
        "escalate": "Tier 2 if the same field is blank across many messages (mapping issue).",
    },
    "INVALID_DATETIME": {
        "severity": "medium",
        "title": "Invalid or impossible date/time",
        "meaning": "A timestamp is not in HL7 format (YYYYMMDDHHMM[SS]) or the collection time "
                   "is later than the message time.",
        "causes": "Instrument clock drift; time zone or daylight-saving misconfiguration; "
                  "wrong date format in the sending system.",
        "fix": "Check the instrument and interface server clocks. Correct the collection time "
               "from the specimen record before release.",
        "escalate": "Tier 2 for clock sync; Tier 3 if the format is wrong at the source.",
    },
    "ACCESSION_NOT_FOUND": {
        "severity": "high",
        "title": "Accession number has no matching order",
        "meaning": "OBR-3 does not match any open order in the LIS.",
        "causes": "Specimen run before the order was received; accession typed manually with a "
                  "typo; order cancelled after the specimen was loaded.",
        "fix": "Hold the result. Verify the order exists and is active, then relink the result "
               "to the correct accession.",
        "escalate": "Tier 2 if orders are consistently missing (order interface delay).",
    },
    "PATIENT_ID_MISMATCH": {
        "severity": "high",
        "title": "Patient ID does not match the order",
        "meaning": "The MRN in PID-3 differs from the MRN on the order for this accession.",
        "causes": "Mislabeled specimen; wrong patient selected at collection; merged or "
                  "duplicate patient records.",
        "fix": "Do NOT release. Treat as a potential misidentification event: follow the "
               "specimen identification policy, notify the supervisor, and recollect if required.",
        "escalate": "Supervisor immediately; Tier 2 if caused by a patient merge.",
    },
    "DUPLICATE_MESSAGE": {
        "severity": "medium",
        "title": "Same message received twice",
        "meaning": "The message control ID (MSH-10) was already seen in this batch.",
        "causes": "Sending system resent after an acknowledgment (ACK) timeout.",
        "fix": "Suppress the duplicate. Check ACK timeout and retry settings on the channel.",
        "escalate": "Tier 3 if resends are frequent.",
    },
    "DUPLICATE_RESULT": {
        "severity": "medium",
        "title": "Second final result for the same test",
        "meaning": "A final (F) result for this accession and test was already filed. "
                   "Changes to a final result should arrive as corrected (C).",
        "causes": "Specimen rerun and resent as final; duplicate transmission.",
        "fix": "Confirm which value is correct. If the value changed, file it as a corrected "
               "result so the change is documented and the provider is notified.",
        "escalate": "Tier 2 if the instrument sends reruns as F instead of C.",
    },
    "NON_NUMERIC_VALUE": {
        "severity": "medium",
        "title": "Numeric test has a non-numeric value",
        "meaning": "OBX-2 says the value is numeric (NM) but OBX-5 contains text.",
        "causes": "Instrument error code or specimen comment (e.g. HEMOLYZED) placed in the "
                  "value field instead of an NTE comment segment.",
        "fix": "Hold the result. Check the specimen and instrument flags, then rerun or "
               "result with a proper comment.",
        "escalate": "Tier 2 to map instrument comments to NTE segments.",
    },
    "UNIT_MISMATCH": {
        "severity": "high",
        "title": "Result units differ from the test build",
        "meaning": "OBX-6 units do not match the units defined for the test in the LIS.",
        "causes": "Instrument set to SI units while the LIS expects conventional units (or the "
                  "reverse); test build changed without updating the instrument.",
        "fix": "Hold all results for this test. Verify the instrument unit setting against the "
               "LIS test build. Never convert values by hand without a validated conversion.",
        "escalate": "Tier 2 immediately.",
    },
    "UNKNOWN_TEST_CODE": {
        "severity": "medium",
        "title": "Test code not in the test catalog",
        "meaning": "The OBX-3 code has no matching test build in the LIS.",
        "causes": "New assay on the instrument not built yet in the LIS; typo in the code "
                  "mapping table.",
        "fix": "Hold the result. Check the instrument-to-LIS test mapping table.",
        "escalate": "Tier 2 (test build / mapping).",
    },
    "INVALID_RESULT_STATUS": {
        "severity": "medium",
        "title": "Unrecognized result status",
        "meaning": "OBX-11 is not a valid HL7 result status (F, P, C, X, R, I, S, D, W).",
        "causes": "Custom status code from the instrument middleware not mapped to HL7.",
        "fix": "Hold the result and confirm its intended status with the bench.",
        "escalate": "Tier 2 (status mapping).",
    },
    "ABNORMAL_FLAG_MISMATCH": {
        "severity": "medium",
        "title": "Abnormal flag does not match the value",
        "meaning": "OBX-8 (H/L/N) does not agree with the value and the LIS reference range.",
        "causes": "Reference range updated in the LIS but not on the instrument (or the "
                  "reverse); age/sex-specific ranges not applied.",
        "fix": "Compare reference ranges in the LIS test build and on the instrument.",
        "escalate": "Tier 2 (reference range build).",
    },
    "CRITICAL_VALUE": {
        "severity": "high",
        "title": "Critical value - notification required",
        "meaning": "The result is outside critical limits. This is not an interface fault; it is "
                   "a workflow alert that starts the critical-call process.",
        "causes": "True patient result (most common); specimen issue such as hemolysis or "
                  "contamination.",
        "fix": "Verify the result and specimen integrity, notify the responsible provider within "
               "the policy time limit, use read-back, and document who was called and when.",
        "escalate": "Supervisor if the provider cannot be reached within policy time.",
    },
}

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
