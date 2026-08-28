# Failure Classification Rules
# Used by the failure-investigator skill
# Complete pattern-matching table for all known failure types

---

## Pattern Matching Rules

Each rule: Pattern → Category → Explanation → Fix → Action

Rules are evaluated in order — use the FIRST matching rule.

---

### Rule 1: Stale Element (LOCATOR_DRIFT)
**Pattern**: `StaleElementReferenceException` OR `stale element`
**Category**: LOCATOR_DRIFT 🟡
**Confidence**: HIGH
**Explanation**:
The Selenium element reference became stale — Maximo re-rendered the DOM
(likely after a partial page refresh triggered by item/lookup selection).
This happens when Maximo upgrades change the page rendering sequence.
**Fix**:
Re-run the DOM probe script to verify element IDs are still current.
Check `maximo-regression-tests/probes/` for element ID discovery tools.
Update the stale locator in the relevant page object or test file.
**Action**: FIX_LOCALLY

---

### Rule 2: Element Not Found (LOCATOR_DRIFT)
**Pattern**: `NoSuchElementException` OR `ElementNotInteractableException`
**Category**: LOCATOR_DRIFT 🟡
**Confidence**: HIGH
**Explanation**:
Selenium could not find or interact with the expected UI element.
The element ID, XPath, or CSS selector in the test no longer matches the DOM.
Maximo UI upgrades frequently change element IDs and page structure.
**Fix**:
Open Maximo in Chrome DevTools and inspect the current element ID.
Update the locator in the test's page object file.
Run the test again with the updated locator.
**Action**: FIX_LOCALLY

---

### Rule 3: Timeout + Empty List (TIMING_ENVIRONMENT)
**Pattern**: `TimeoutException` AND `0 - 0 of 0`
**Category**: TIMING_ENVIRONMENT 🟠
**Confidence**: HIGH
**Explanation**:
Maximo returned an empty list after navigation — the record was created but
the server had not finished indexing/committing it before the search executed.
This is a server-side timing race, not a code defect or application regression.
**Fix**:
Increase `PAGE_LOAD_WAIT` in `maximo_ui_driver.py` (current: 12s → try 18s).
This is typically not a persistent failure — re-run the test once.
**Action**: RERUN (first), FIX_LOCALLY (if persistent)

---

### Rule 4: Timeout (TIMING_ENVIRONMENT)
**Pattern**: `TimeoutException` (no other patterns match)
**Category**: TIMING_ENVIRONMENT 🟠
**Confidence**: MEDIUM
**Explanation**:
An expected UI element did not appear within the timeout window.
The Maximo instance may be under load or responding slowly after an upgrade.
**Fix**:
Re-run the test when the Maximo instance is less busy.
If persistent: increase `ELEMENT_TIMEOUT` in `maximo_ui_driver.py`.
Check Maximo server health / memory usage.
**Action**: RERUN

---

### Rule 5: Connection Error (ENVIRONMENT_AUTH)
**Pattern**: `ConnectionError` OR `Failed to establish` OR `Max retries exceeded`
**Category**: ENVIRONMENT_AUTH 🔵
**Confidence**: HIGH
**Explanation**:
Cannot connect to the Maximo instance. The URL is unreachable or the
network/VPN connection has dropped. Nothing can run until this is fixed.
**Fix**:
Verify network/VPN connectivity to the Maximo URL.
Run: `python .bob/hooks/schema-verify.py` to test basic connectivity.
Check `MAXIMO_BASE_URL` in `config/agent_config.py` is correct.
**Action**: ESCALATE_TO_ADMIN (infrastructure team)

---

### Rule 6: Authentication Failure (ENVIRONMENT_AUTH)
**Pattern**: `401` OR `403` OR `Authentication` OR `apikey`
**Category**: ENVIRONMENT_AUTH 🔵
**Confidence**: HIGH
**Explanation**:
Authentication failed — the API key may have expired, been revoked, or
the user account associated with the key has been locked.
**Fix**:
Verify `API_KEY` in `config/agent_config.py` is current.
Log in to Maximo manually and regenerate the API key if needed.
Update `API_KEY` in config and re-run the pipeline.
**Action**: ESCALATE_TO_ADMIN

---

### Rule 7: Status Assertion Failed (APPLICATION_DEFECT)
**Pattern**: `AssertionError` AND (`status` OR `Expected status`)
**Category**: APPLICATION_DEFECT 🔴
**Confidence**: HIGH
**Explanation**:
A status field assertion failed — the Maximo record did not transition
to the expected status. This indicates a business rule change, workflow
configuration change, or a Maximo upgrade introduced a regression.
**Fix**:
Manually verify the status transition in the Maximo UI.
Check MAS release notes for changes to this workflow's status transitions.
If confirmed regression: raise a defect with the Maximo admin team.
**Action**: RAISE_DEFECT

---

### Rule 8: Autonumber Not Generated (APPLICATION_DEFECT)
**Pattern**: `AssertionError` AND (`was not auto-generated` OR `number`)
**Category**: APPLICATION_DEFECT 🔴
**Confidence**: MEDIUM
**Explanation**:
A record number was not auto-generated — Maximo's autonumber sequence
may not be configured for this object structure in this environment.
**Fix**:
Check Maximo autonumber configuration for this object structure.
Verify the SITE and ORG are correctly configured.
Check if the sequence was reset or re-configured during the upgrade.
**Action**: ESCALATE_TO_ADMIN

---

### Rule 9: Reference Data Missing (TEST_DATA)
**Pattern**: `AssertionError` AND (`not found` OR `0 records`)
**Category**: TEST_DATA 🟣
**Confidence**: HIGH
**Explanation**:
A required reference record was not found in Maximo.
The test depends on reference data (vendor, location, item, storeroom)
that may not exist or may have been deactivated during the upgrade.
**Fix**:
Check that all required reference data exists and is ACTIVE:
  - Vendor: EMI (must be ACTIVE status, linked to EAGLENA org)
  - Site: BEDFORD (must exist and be active)
  - Storeroom: CENTRAL (must be ACTIVE, linked to BEDFORD/EAGLENA)
  - Item: TEST-ITEM-001 (must exist in item master)
Update `DEFAULT_PO_VENDOR` in `config/config.py` if vendor name differs.
**Action**: ESCALATE_TO_ADMIN (data setup)

---

### Rule 10: HTTP 400 + Storeroom Error (TEST_DATA)
**Pattern**: `400` AND `storeroom` (or `BMXAA4073`)
**Category**: TEST_DATA 🟣
**Confidence**: HIGH
**Explanation**:
Receipt creation failed because the storeroom is invalid or inactive.
MAS 9.2 tightened storeroom validation — storerooms must now be ACTIVE
and linked to the correct organization and site.
**Fix**:
In Maximo: Inventory → Storerooms → CENTRAL → set Status to ACTIVE.
Verify storeroom is linked to site BEDFORD and org EAGLENA.
**Action**: ESCALATE_TO_ADMIN

---

### Rule 11: HTTP 400 + Vendor Error (TEST_DATA)
**Pattern**: `400` AND (`vendor` OR `BMXAA`)
**Category**: TEST_DATA 🟣
**Confidence**: MEDIUM
**Explanation**:
The vendor used in the test is inactive or not approved for purchasing.
**Fix**:
In Maximo: Purchasing → Companies → EMI → verify Status is ACTIVE.
Verify vendor is approved for BEDFORD site and EAGLENA org.
**Action**: ESCALATE_TO_ADMIN

---

### Rule 12: Fallback (UNKNOWN)
**Pattern**: No other rule matched
**Category**: UNKNOWN ⚪
**Confidence**: LOW
**Explanation**:
Could not automatically classify this failure. Manual investigation required.
**Fix**:
Review the full traceback: run with `-v --tb=long` for details.
Check `logs/agent_run.log` for additional context.
Try running the failing test in isolation:
  `cd maximo-regression-tests && python -m pytest <test_file>::<test_name> -v`
**Action**: FIX_LOCALLY or RAISE_DEFECT (after investigation)

---

## BMXAA Error Code Reference

| Code | Meaning | Likely Category |
|------|---------|----------------|
| BMXAA4073E | Invalid/inactive storeroom | TEST_DATA |
| BMXAA6918E | Vendor not found or inactive | TEST_DATA |
| BMXAA4312E | Approval required (status issue) | APPLICATION_DEFECT |
| BMXAA7560E | Autonumber not configured | APPLICATION_DEFECT |
| BMXAA0023E | Object not found | TEST_DATA or APPLICATION_DEFECT |
| BMXAA4020E | Site/org mismatch | TEST_DATA or CONFIG |
| BMXAA0503E | Authentication required | ENVIRONMENT_AUTH |
