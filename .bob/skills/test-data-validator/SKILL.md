---
name: test-data-validator
description: >-
  Verify that the required test data exists and is active in the target Maximo
  environment before running tests. Use when tests are failing with TEST_DATA
  errors, when setting up a new environment, or before running P2P regression.
---

# Test Data Validator Skill

When activated, check that all reference data required by the test suite exists
in the target Maximo environment. This prevents TEST_DATA failures before they
happen — proactive validation rather than reactive investigation.

---

## Why This Matters

The test suite depends on specific reference data in Maximo:
- Vendor records (must be ACTIVE)
- Site and Organization (must exist and be active)
- Storeroom (must be ACTIVE and org-linked)
- Item master records (must exist)
- GL accounts (must be configured)

If any of these are missing or inactive, P2P tests will fail with TEST_DATA errors.
After a MAS upgrade, these records can be inadvertently deactivated or reconfigured.

---

## Required Data Checklist

Use the detailed requirements in `data-requirements.md` as the full reference.

### Pre-Run Quick Check

Before running any P2P tests, verify:

| Data Type | Expected Value | Check Method |
|-----------|---------------|-------------|
| Vendor | EMI (ACTIVE, linked to EAGLENA) | Query MXVENDOR |
| Site | BEDFORD (active) | Query MXSITE |
| Organization | EAGLENA (active) | Query MXORGANIZATION |
| Storeroom | CENTRAL (ACTIVE, BEDFORD/EAGLENA) | Query MXINVBALANCES |
| Item | TEST-ITEM-001 (in item master) | Query MXITEM |

---

## Step 1 — Query Maximo for Each Required Record

Use the Maximo MCP tool to query each required data item.

For each item, check:
1. Does the record EXIST?
2. Is the record ACTIVE / in correct status?
3. Is it linked to the correct SITE (BEDFORD) and ORG (EAGLENA)?

---

## Step 2 — Report Findings

For each data item, report:
- ✅ EXISTS and ACTIVE — test can proceed
- ⚠️ EXISTS but INACTIVE — needs activation before test run
- ❌ NOT FOUND — needs creation before test run

Example output:
```
Data Validation Report — BEDFORD / EAGLENA
==========================================
✅ Vendor EMI — ACTIVE, org EAGLENA
✅ Site BEDFORD — exists and active
✅ Organization EAGLENA — exists and active
⚠️ Storeroom CENTRAL — EXISTS but status INACTIVE
   Fix: Inventory → Storerooms → CENTRAL → set Status = ACTIVE
❌ Item TEST-ITEM-001 — NOT FOUND in item master
   Fix: Create item TEST-ITEM-001 in Maximo item master
```

---

## Step 3 — Produce Fix Instructions

For each problem found, provide exact Maximo admin steps to fix it:

**Storeroom inactive**:
> Maximo → Inventory → Storerooms → search CENTRAL → Status → Change to ACTIVE → Save

**Vendor inactive**:
> Maximo → Purchasing → Companies → search EMI → Status → Change to ACTIVE → Save

**Item missing**:
> Maximo → Inventory → Item Master → New → Item: TEST-ITEM-001 → Commodity: PARTS → Save

**Site missing**:
> Contact your Maximo administrator — site configuration requires system-level access

---

## Step 4 — Re-Validate After Fix

After any fix is applied, re-run the validation:
```bash
python .bob/hooks/schema-verify.py
```

And confirm the data is now correct before re-running the test pipeline.

---

## Output Checklist

Before finishing, verify:
- [ ] All required data items checked
- [ ] Status (ACTIVE/INACTIVE/MISSING) reported for each item
- [ ] Fix instructions provided for every problem found
- [ ] Clear GO / NO-GO recommendation for test run
- [ ] If NO-GO: specific items to fix before proceeding
