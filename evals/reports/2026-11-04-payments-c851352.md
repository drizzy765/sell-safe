# Sell-Safe Payment Verification Evaluation Report

- Suite: `payments`
- Dataset: `v1`
- Git SHA: `c851352`
- Timestamp: 2026-11-04T14:08:33.735133+00:00

## Summary

- Total cases: 20
- Passed: 20
- Failed: 0
- False CONFIRMED on fake cases: 0

## Confusion Matrix

| Expected \ Actual | CONFIRMED | NOT_FOUND | SUSPICIOUS | UNVERIFIED |
|---|---|---|---|---|
| CONFIRMED | 5 | 0 | 0 | 0 |
| NOT_FOUND | 0 | 4 | 0 | 0 |
| SUSPICIOUS | 0 | 0 | 7 | 0 |
| UNVERIFIED | 0 | 0 | 0 | 4 |

## Detail

- `clean-1` (PASS): expected CONFIRMED (release=True), got CONFIRMED (release=True, confidence=1.00)
- `clean-2` (PASS): expected CONFIRMED (release=True), got CONFIRMED (release=True, confidence=1.00)
- `clean-3` (PASS): expected CONFIRMED (release=False), got CONFIRMED (release=False, confidence=0.80)
- `edited-1` (PASS): expected UNVERIFIED (release=False), got UNVERIFIED (release=False, confidence=0.40)
  - rule_hits: R1_amount_mismatch
- `edited-2` (PASS): expected UNVERIFIED (release=False), got UNVERIFIED (release=False, confidence=0.40)
  - rule_hits: R1_amount_mismatch
- `edited-3` (PASS): expected SUSPICIOUS (release=False), got SUSPICIOUS (release=False, confidence=0.20)
  - rule_hits: R1_amount_mismatch, R7_visual_anomaly
- `reused-1` (PASS): expected SUSPICIOUS (release=False), got SUSPICIOUS (release=False, confidence=0.20)
  - rule_hits: R4_duplicate_ref
- `reused-2` (PASS): expected SUSPICIOUS (release=False), got SUSPICIOUS (release=False, confidence=0.20)
  - rule_hits: R4_duplicate_ref
- `reused-3` (PASS): expected SUSPICIOUS (release=False), got SUSPICIOUS (release=False, confidence=0.20)
  - rule_hits: R4_duplicate_ref
- `pending-1` (PASS): expected UNVERIFIED (release=False), got UNVERIFIED (release=False, confidence=0.40)
  - rule_hits: R8_status_text
- `pending-2` (PASS): expected CONFIRMED (release=False), got CONFIRMED (release=False, confidence=0.80)
  - rule_hits: R8_status_text
- `pending-3` (PASS): expected CONFIRMED (release=False), got CONFIRMED (release=False, confidence=0.80)
  - rule_hits: R8_status_text
- `not-receipt-1` (PASS): expected NOT_FOUND (release=False), got NOT_FOUND (release=False, confidence=0.50)
- `not-receipt-2` (PASS): expected NOT_FOUND (release=False), got NOT_FOUND (release=False, confidence=0.50)
- `not-receipt-3` (PASS): expected NOT_FOUND (release=False), got NOT_FOUND (release=False, confidence=0.50)
- `partial-1` (PASS): expected SUSPICIOUS (release=False), got SUSPICIOUS (release=False, confidence=0.20)
  - rule_hits: R1_amount_mismatch
- `partial-2` (PASS): expected SUSPICIOUS (release=False), got SUSPICIOUS (release=False, confidence=0.20)
  - rule_hits: R4_duplicate_ref
- `low-confidence-1` (PASS): expected UNVERIFIED (release=False), got UNVERIFIED (release=False, confidence=0.45)
- `tamper-1` (PASS): expected SUSPICIOUS (release=False), got SUSPICIOUS (release=False, confidence=0.30)
  - rule_hits: R7_visual_anomaly
- `time-mismatch-1` (PASS): expected NOT_FOUND (release=False), got NOT_FOUND (release=False, confidence=0.50)