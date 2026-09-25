# Lab Interface Triage Report

## Summary

| Measure | Count |
|---|---|
| Messages checked | 34 |
| Clean (no findings) | 13 |
| With findings | 21 |
| Hold - high-severity interface fault | 11 |
| Critical values needing a call | 2 |

## Findings by type

| Severity | Code | What it means | Count |
|---|---|---|---|
| high | `MISSING_REQUIRED_FIELD` | Required field is empty | 5 |
| high | `CRITICAL_VALUE` | Critical value - notification required | 2 |
| high | `ACCESSION_NOT_FOUND` | Accession number has no matching order | 1 |
| high | `PATIENT_ID_MISMATCH` | Patient ID does not match the order | 1 |
| high | `UNIT_MISMATCH` | Result units differ from the test build | 1 |
| high | `MALFORMED_SEGMENT` | Line is not a valid HL7 segment | 1 |
| high | `MISSING_SEGMENT` | Required segment missing | 1 |
| high | `WRONG_MESSAGE_TYPE` | Not a lab result message | 1 |
| medium | `DUPLICATE_RESULT` | Second final result for the same test | 4 |
| medium | `NON_NUMERIC_VALUE` | Numeric test has a non-numeric value | 2 |
| medium | `INVALID_DATETIME` | Invalid or impossible date/time | 2 |
| medium | `ABNORMAL_FLAG_MISMATCH` | Abnormal flag does not match the value | 1 |
| medium | `UNKNOWN_TEST_CODE` | Test code not in the test catalog | 1 |
| medium | `INVALID_RESULT_STATUS` | Unrecognized result status | 1 |
| medium | `DUPLICATE_MESSAGE` | Same message received twice | 1 |

## Message detail

### 013_missing_mrn.hl7

- **HIGH - `MISSING_REQUIRED_FIELD`** at PID-3: Patient MRN is empty
  - Next step: Hold the result. Look up the specimen by label or order and correct at the source. Never guess an identifier.

### 014_missing_accession.hl7

- **HIGH - `MISSING_REQUIRED_FIELD`** at OBR-3: Accession number is empty
  - Next step: Hold the result. Look up the specimen by label or order and correct at the source. Never guess an identifier.

### 015_accession_not_found.hl7

- **HIGH - `ACCESSION_NOT_FOUND`** at OBR-3: No order for accession A26009999
  - Next step: Hold the result. Verify the order exists and is active, then relink the result to the correct accession.

### 016_patient_mismatch.hl7

- **HIGH - `PATIENT_ID_MISMATCH`** at PID-3: Message MRN TST10005 but order A26000016 belongs to TST10004
  - Next step: Do NOT release. Treat as a potential misidentification event: follow the specimen identification policy, notify the supervisor, and recollect if required.

### 017_non_numeric.hl7

- **MEDIUM - `NON_NUMERIC_VALUE`** at OBX-1 (OBX-5): Potassium: 'HEMOLYZED' is not a number
  - Next step: Hold the result. Check the specimen and instrument flags, then rerun or result with a proper comment.

### 018_unit_mismatch.hl7

- **HIGH - `UNIT_MISMATCH`** at OBX-1 (OBX-6): Glucose: units 'mmol/L' but test build expects 'mg/dL'
  - Next step: Hold all results for this test. Verify the instrument unit setting against the LIS test build. Never convert values by hand without a validated conversion.

### 019_critical_high_k.hl7

- **HIGH - `CRITICAL_VALUE`** at OBX-1: Potassium 6.8 mmol/L is outside critical limits (2.8-6.2)
  - Next step: Verify the result and specimen integrity, notify the responsible provider within the policy time limit, use read-back, and document who was called and when.

### 020_flag_mismatch.hl7

- **MEDIUM - `ABNORMAL_FLAG_MISMATCH`** at OBX-1 (OBX-8): Sodium 150: flag 'N' but reference range 136.0-145.0 gives 'H'
  - Next step: Compare reference ranges in the LIS test build and on the instrument.

### 021_unknown_test.hl7

- **MEDIUM - `UNKNOWN_TEST_CODE`** at OBX-1 (OBX-3): Code 99999-9 is not in the test catalog
  - Next step: Hold the result. Check the instrument-to-LIS test mapping table.

### 022_invalid_status.hl7

- **MEDIUM - `INVALID_RESULT_STATUS`** at OBX-1 (OBX-11): Glucose: status 'Z' is not valid
  - Next step: Hold the result and confirm its intended status with the bench.

### 023_missing_value.hl7

- **HIGH - `MISSING_REQUIRED_FIELD`** at OBX-1 (OBX-5): Glucose: result value is empty
  - Next step: Hold the result. Look up the specimen by label or order and correct at the source. Never guess an identifier.

### 024_malformed_line.hl7

- **HIGH - `MALFORMED_SEGMENT`** at line 5: 'NTE results verified by tech'
  - Next step: Open the raw message in the interface engine. Check segment terminator settings. Request a resend from the sending system.

### 025_missing_pid.hl7

- **HIGH - `MISSING_SEGMENT`** at PID: No PID segment
  - Next step: Hold the message. Compare against a known-good message from the same source. Request a resend.

### 026_wrong_type.hl7

- **HIGH - `WRONG_MESSAGE_TYPE`** at MSH-9: Got ADT^A01, expected ORU^R01
  - Next step: Do not process as a result. Confirm the channel routing rules.

### 027_bad_timestamp.hl7

- **MEDIUM - `INVALID_DATETIME`** at MSH-7: '2026-01-15 10:30' is not a valid HL7 timestamp
  - Next step: Check the instrument and interface server clocks. Correct the collection time from the specimen record before release.

### 028_future_collection.hl7

- **MEDIUM - `INVALID_DATETIME`** at OBR-7: Collection time 20260115143000 is after message time 20260115103000
  - Next step: Check the instrument and interface server clocks. Correct the collection time from the specimen record before release.

### 029_duplicate_message.hl7

- **MEDIUM - `DUPLICATE_MESSAGE`** at MSH-10: Control ID MSG0001 already received
  - Next step: Suppress the duplicate. Check ACK timeout and retry settings on the channel.
- **MEDIUM - `DUPLICATE_RESULT`** at OBX-1: Potassium: final result already filed for A26000001
  - Next step: Confirm which value is correct. If the value changed, file it as a corrected result so the change is documented and the provider is notified.
- **MEDIUM - `DUPLICATE_RESULT`** at OBX-2: Sodium: final result already filed for A26000001
  - Next step: Confirm which value is correct. If the value changed, file it as a corrected result so the change is documented and the provider is notified.
- **MEDIUM - `DUPLICATE_RESULT`** at OBX-3: Glucose: final result already filed for A26000001
  - Next step: Confirm which value is correct. If the value changed, file it as a corrected result so the change is documented and the provider is notified.

### 030_duplicate_final.hl7

- **MEDIUM - `DUPLICATE_RESULT`** at OBX-1: Hemoglobin: final result already filed for A26000002
  - Next step: Confirm which value is correct. If the value changed, file it as a corrected result so the change is documented and the provider is notified.

### 032_missing_control_id.hl7

- **HIGH - `MISSING_REQUIRED_FIELD`** at MSH-10: Message control ID is empty
  - Next step: Hold the result. Look up the specimen by label or order and correct at the source. Never guess an identifier.

### 033_critical_low_glucose.hl7

- **HIGH - `CRITICAL_VALUE`** at OBX-3: Glucose 32 mg/dL is outside critical limits (40.0-450.0)
  - Next step: Verify the result and specimen integrity, notify the responsible provider within the policy time limit, use read-back, and document who was called and when.

### 034_multi_fault.hl7

- **HIGH - `MISSING_REQUIRED_FIELD`** at PID-3: Patient MRN is empty
  - Next step: Hold the result. Look up the specimen by label or order and correct at the source. Never guess an identifier.
- **MEDIUM - `NON_NUMERIC_VALUE`** at OBX-1 (OBX-5): WBC: 'CLOTTED' is not a number
  - Next step: Hold the result. Check the specimen and instrument flags, then rerun or result with a proper comment.

See docs/RUNBOOK.md for causes and escalation paths for each finding.
