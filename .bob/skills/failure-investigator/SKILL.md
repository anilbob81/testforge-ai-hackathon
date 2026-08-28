---
name: failure-investigator
description: >-
  Investigate a specific test failure, classify the root cause into one of
  five categories, and suggest the exact fix. Use when a test has failed and
  you need to understand WHY — Application Defect vs Locator Drift vs
  Environment vs Test Data vs Unknown.
---

# Failure Investigator Skill

When activated, systematically investigate a test failure using evidence-based
classification. This is the most valuable skill for a real testing team —
it transforms a raw traceback into an actionable root cause analysis.

---

## The Five Failure Categories

| Category | Icon | Meaning | Owner |
|----------|------|---------|-------|
| APPLICATION_DEFECT | 🔴 | Maximo business logic or data changed | Maximo Admin |
| LOCATOR_DRIFT | 🟡 | Selenium element ID changed after upgrade | Test Automation Engineer |
| TIMING_ENVIRONMENT | 🟠 | Race condition or server slowness | DevOps / Retry test |
| ENVIRONMENT_AUTH | 🔵 | API key expired or network unreachable | Infrastructure Team |
| TEST_DATA | 🟣 | Required reference data missing or inactive | Test Data Manager |
| UNKNOWN | ⚪ | Cannot classify from available evidence | Manual Investigation |

---

## Step 1 — Read the Failure Evidence

Collect all available evidence before classifying:

1. **Traceback / exception type** (the most important signal)
2. **HTTP status code** (400, 401, 403, 404, 500)
3. **Maximo error code** (BMXAA prefix — look it up in the BMXAA reference)
4. **Previous successful run** (was this passing before? What changed?)
5. **Application version** (MAS 9.1 vs 9.2 — did an upgrade happen?)
6. **Selenium screenshot** (if available — what does the screen show?)
7. **API response body** (what did Maximo actually return?)

---

## Step 2 — Follow the Classification Decision Tree

```
Is the exception a Selenium exception?
  ├─ StaleElementReferenceException → LOCATOR_DRIFT
  ├─ NoSuchElementException → LOCATOR_DRIFT
  ├─ ElementNotInteractableException → LOCATOR_DRIFT
  ├─ TimeoutException + "0 - 0 of 0" → TIMING_ENVIRONMENT (list didn't load)
  └─ TimeoutException (other) → TIMING_ENVIRONMENT (element didn't appear)

Is the exception a network/auth exception?
  ├─ ConnectionError / Max retries exceeded → ENVIRONMENT_AUTH
  ├─ HTTP 401 or 403 → ENVIRONMENT_AUTH
  └─ HTTP 503 / 504 → ENVIRONMENT_AUTH (Maximo down)

Is the exception an AssertionError?
  ├─ "Expected status X but got Y" → APPLICATION_DEFECT
  ├─ "was not auto-generated" → APPLICATION_DEFECT (autonumber config)
  ├─ "not found" or "0 records" + reference data term → TEST_DATA
  └─ "not found" + record created by test → APPLICATION_DEFECT

Is the HTTP status 400?
  ├─ BMXAA + "storeroom" → TEST_DATA (storeroom inactive/wrong)
  ├─ BMXAA + "vendor" → TEST_DATA (vendor inactive)
  ├─ BMXAA + "validation" → APPLICATION_DEFECT (business rule change)
  └─ Other 400 → APPLICATION_DEFECT or TEST_DATA (check message)

None of the above match → UNKNOWN
```

See `classification-rules.md` for the complete pattern table with examples.

---

## Step 3 — Query Live Maximo (When Available)

For TEST_DATA failures, query Maximo to confirm the state of reference data:

Using the MCP Maximo tool — query the relevant object structure:
- Vendor status: query MXVENDOR where vendornum="EMI" → check status field
- Storeroom status: query MXINVBALANCES where storeloc="CENTRAL" → check status
- Site config: query MXSITE where siteid="BEDFORD" → confirm active

Example via Python (for ENVIRONMENT_AUTH failures to test connectivity):
```bash
python .bob/hooks/schema-verify.py
```

---

## Step 4 — Produce the Classification Report

Output format for each failure:

```json
{
  "test_name": "test_create_receipt",
  "category": "TEST_DATA",
  "confidence": "HIGH",
  "evidence": "HTTP 400, BMXAA4073E: Invalid storeroom CENTRAL",
  "explanation": "The storeroom CENTRAL is inactive or not linked to BEDFORD site. MAS 9.2 tightened storeroom validation — storerooms must now be ACTIVE and org-linked.",
  "fix": "In Maximo admin: Inventory → Storerooms → CENTRAL → set Status to ACTIVE.",
  "action": "ESCALATE_TO_ADMIN",
  "rerun_after_fix": true
}
```

Actions:
- `FIX_LOCALLY` — fix in the test code (update config, locator, timeout)
- `RERUN` — transient failure, just re-run the test
- `ESCALATE_TO_ADMIN` — requires Maximo configuration or data change
- `RAISE_DEFECT` — confirmed application regression, file a bug

---

## Step 5 — Distinguish App Defect vs Automation Defect

This is critical — it determines who fixes the problem:

**Application Defect**: The application page loaded correctly, Maximo processed
the request, but the result was wrong (wrong status, wrong data, error code).
→ The TEST is correct. Maximo behaviour changed.

**Automation Defect**: The Selenium test tried to interact with the UI but the
interaction failed (element not found, element stale, click didn't register).
→ Maximo may be fine. The TEST needs updating to match the new DOM.

Quick test: "Would a human tester clicking through the UI succeed?"
- YES → Automation defect (test needs fixing)
- NO → Application defect (Maximo regression)

---

## Output Checklist

Before finishing, verify:
- [ ] Every failed test has a classification
- [ ] Evidence cited for each classification (not just a guess)
- [ ] Fix is specific (command, file, config, Maximo admin step)
- [ ] Confidence level stated (HIGH/MEDIUM/LOW)
- [ ] Recommended action stated (who fixes it)
- [ ] Application vs automation defect distinction made where relevant
