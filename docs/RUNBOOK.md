# Troubleshooting Runbook: Lab Result Interface Faults

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
| high | [`ACCESSION_NOT_FOUND`](#accession_not_found) | Accession number has no matching order |
| high | [`CRITICAL_VALUE`](#critical_value) | Critical value - notification required |
| high | [`MALFORMED_SEGMENT`](#malformed_segment) | Line is not a valid HL7 segment |
| high | [`MISSING_REQUIRED_FIELD`](#missing_required_field) | Required field is empty |
| high | [`MISSING_SEGMENT`](#missing_segment) | Required segment missing |
| high | [`PATIENT_ID_MISMATCH`](#patient_id_mismatch) | Patient ID does not match the order |
| high | [`UNIT_MISMATCH`](#unit_mismatch) | Result units differ from the test build |
| high | [`WRONG_MESSAGE_TYPE`](#wrong_message_type) | Not a lab result message |
| medium | [`ABNORMAL_FLAG_MISMATCH`](#abnormal_flag_mismatch) | Abnormal flag does not match the value |
| medium | [`DUPLICATE_MESSAGE`](#duplicate_message) | Same message received twice |
| medium | [`DUPLICATE_RESULT`](#duplicate_result) | Second final result for the same test |
| medium | [`INVALID_DATETIME`](#invalid_datetime) | Invalid or impossible date/time |
| medium | [`INVALID_RESULT_STATUS`](#invalid_result_status) | Unrecognized result status |
| medium | [`NON_NUMERIC_VALUE`](#non_numeric_value) | Numeric test has a non-numeric value |
| medium | [`UNKNOWN_TEST_CODE`](#unknown_test_code) | Test code not in the test catalog |

## ACCESSION_NOT_FOUND

**Accession number has no matching order** (severity: high)

- **What it means:** OBR-3 does not match any open order in the LIS.
- **Common causes:** Specimen run before the order was received; accession typed manually with a typo; order cancelled after the specimen was loaded.
- **First steps:** Hold the result. Verify the order exists and is active, then relink the result to the correct accession.
- **Escalate:** Tier 2 if orders are consistently missing (order interface delay).

## CRITICAL_VALUE

**Critical value - notification required** (severity: high)

- **What it means:** The result is outside critical limits. This is not an interface fault; it is a workflow alert that starts the critical-call process.
- **Common causes:** True patient result (most common); specimen issue such as hemolysis or contamination.
- **First steps:** Verify the result and specimen integrity, notify the responsible provider within the policy time limit, use read-back, and document who was called and when.
- **Escalate:** Supervisor if the provider cannot be reached within policy time.

## MALFORMED_SEGMENT

**Line is not a valid HL7 segment** (severity: high)

- **What it means:** A line does not start with a 3-character segment ID followed by '|'.
- **Common causes:** Free text or instrument comments inserted without an NTE segment; broken line wrapping or segment terminators in the interface engine; truncated transmission.
- **First steps:** Open the raw message in the interface engine. Check segment terminator settings. Request a resend from the sending system.
- **Escalate:** Tier 3 if it repeats for the same instrument or channel.

## MISSING_REQUIRED_FIELD

**Required field is empty** (severity: high)

- **What it means:** A field needed to file the result safely is blank (message control ID, patient MRN, accession number, test code, result value or result status).
- **Common causes:** Manual entry skipped on the instrument; incomplete barcode read; mapping gap.
- **First steps:** Hold the result. Look up the specimen by label or order and correct at the source. Never guess an identifier.
- **Escalate:** Tier 2 if the same field is blank across many messages (mapping issue).

## MISSING_SEGMENT

**Required segment missing** (severity: high)

- **What it means:** A result message must contain MSH, PID, OBR and at least one OBX segment.
- **Common causes:** Sending system mapping error; message split across transmissions; filter in the interface engine dropping segments.
- **First steps:** Hold the message. Compare against a known-good message from the same source. Request a resend.
- **Escalate:** Tier 3 (interface team).

## PATIENT_ID_MISMATCH

**Patient ID does not match the order** (severity: high)

- **What it means:** The MRN in PID-3 differs from the MRN on the order for this accession.
- **Common causes:** Mislabeled specimen; wrong patient selected at collection; merged or duplicate patient records.
- **First steps:** Do NOT release. Treat as a potential misidentification event: follow the specimen identification policy, notify the supervisor, and recollect if required.
- **Escalate:** Supervisor immediately; Tier 2 if caused by a patient merge.

## UNIT_MISMATCH

**Result units differ from the test build** (severity: high)

- **What it means:** OBX-6 units do not match the units defined for the test in the LIS.
- **Common causes:** Instrument set to SI units while the LIS expects conventional units (or the reverse); test build changed without updating the instrument.
- **First steps:** Hold all results for this test. Verify the instrument unit setting against the LIS test build. Never convert values by hand without a validated conversion.
- **Escalate:** Tier 2 immediately.

## WRONG_MESSAGE_TYPE

**Not a lab result message** (severity: high)

- **What it means:** MSH-9 is not ORU^R01, so this message was routed to the results channel by mistake.
- **Common causes:** Routing rule in the interface engine sends ADT/ORM traffic to the result feed.
- **First steps:** Do not process as a result. Confirm the channel routing rules.
- **Escalate:** Tier 3 (interface team) to correct routing.

## ABNORMAL_FLAG_MISMATCH

**Abnormal flag does not match the value** (severity: medium)

- **What it means:** OBX-8 (H/L/N) does not agree with the value and the LIS reference range.
- **Common causes:** Reference range updated in the LIS but not on the instrument (or the reverse); age/sex-specific ranges not applied.
- **First steps:** Compare reference ranges in the LIS test build and on the instrument.
- **Escalate:** Tier 2 (reference range build).

## DUPLICATE_MESSAGE

**Same message received twice** (severity: medium)

- **What it means:** The message control ID (MSH-10) was already seen in this batch.
- **Common causes:** Sending system resent after an acknowledgment (ACK) timeout.
- **First steps:** Suppress the duplicate. Check ACK timeout and retry settings on the channel.
- **Escalate:** Tier 3 if resends are frequent.

## DUPLICATE_RESULT

**Second final result for the same test** (severity: medium)

- **What it means:** A final (F) result for this accession and test was already filed. Changes to a final result should arrive as corrected (C).
- **Common causes:** Specimen rerun and resent as final; duplicate transmission.
- **First steps:** Confirm which value is correct. If the value changed, file it as a corrected result so the change is documented and the provider is notified.
- **Escalate:** Tier 2 if the instrument sends reruns as F instead of C.

## INVALID_DATETIME

**Invalid or impossible date/time** (severity: medium)

- **What it means:** A timestamp is not in HL7 format (YYYYMMDDHHMM[SS]) or the collection time is later than the message time.
- **Common causes:** Instrument clock drift; time zone or daylight-saving misconfiguration; wrong date format in the sending system.
- **First steps:** Check the instrument and interface server clocks. Correct the collection time from the specimen record before release.
- **Escalate:** Tier 2 for clock sync; Tier 3 if the format is wrong at the source.

## INVALID_RESULT_STATUS

**Unrecognized result status** (severity: medium)

- **What it means:** OBX-11 is not a valid HL7 result status (F, P, C, X, R, I, S, D, W).
- **Common causes:** Custom status code from the instrument middleware not mapped to HL7.
- **First steps:** Hold the result and confirm its intended status with the bench.
- **Escalate:** Tier 2 (status mapping).

## NON_NUMERIC_VALUE

**Numeric test has a non-numeric value** (severity: medium)

- **What it means:** OBX-2 says the value is numeric (NM) but OBX-5 contains text.
- **Common causes:** Instrument error code or specimen comment (e.g. HEMOLYZED) placed in the value field instead of an NTE comment segment.
- **First steps:** Hold the result. Check the specimen and instrument flags, then rerun or result with a proper comment.
- **Escalate:** Tier 2 to map instrument comments to NTE segments.

## UNKNOWN_TEST_CODE

**Test code not in the test catalog** (severity: medium)

- **What it means:** The OBX-3 code has no matching test build in the LIS.
- **Common causes:** New assay on the instrument not built yet in the LIS; typo in the code mapping table.
- **First steps:** Hold the result. Check the instrument-to-LIS test mapping table.
- **Escalate:** Tier 2 (test build / mapping).
