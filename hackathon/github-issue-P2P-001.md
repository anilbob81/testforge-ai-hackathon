# [TestForge] Issue #001 — P2P Regression Failure After MAS 9.2 Upgrade

**Labels**: `bug`, `regression`, `p2p`, `high-priority`, `mas-9.2`
**Assignee**: TestForge AI Agent (automated)
**Milestone**: MAS 9.2 Validation — Sprint 1
**Created**: 2026-08-26
**Status**: Open → Pending AI Analysis

---

## Problem Description

After upgrading from MAS 9.1 to 9.2 in the staging environment, the
Procure-to-Pay end-to-end workflow is failing at the Receipt step.
The same test was passing consistently on MAS 9.1 as recently as last week.

The error originates from the Maximo REST API (`BMXAA4073E`) and is also
reproduced by the Selenium UI test when attempting to create a receipt against
a purchase order.

---

## Failure Evidence

```
Test Suite: P2P Regression — Post-Upgrade Validation
Environment: BEDFORD / EAGLENA — MAS 9.2 (upgraded 2026-08-25)

Test: P2P_005_Create_Receipt (test_07_po.py::TestReceiptCreation::test_create_receipt)
Result: FAIL
Duration: 2.3s

API Response:
  HTTP Status: 400 Bad Request
  Body: {
    "Error": {
      "statusCode": "400",
      "message": "BMXAA4073E - The storeroom CENTRAL specified in the
                  receiving record is not valid for site BEDFORD."
    }
  }

Previous run (MAS 9.1, 2026-08-20):
  HTTP Status: 201 Created
  Receipt created successfully: REC-00147

Additional symptom (Selenium):
  test_10_ui_procurement_lifecycle.py::test_ui_create_receipt: FAIL
  selenium.common.exceptions.ElementNotInteractableException at receipt step
  The storeroom field is present but the dropdown is empty / validation fails
```

---

## MAS 9.2 Change Log Reference

From the IBM MAS 9.2 Release Notes (Section 4.3 — Receiving):

> **Storeroom Validation Enhancement**
> In MAS 9.2, storeroom validation for receipt creation has been tightened.
> The storeroom must now meet ALL of the following conditions:
> - Status: ACTIVE (previously any status was accepted)
> - Linked to the correct organization (EAGLENA)
> - Linked to the correct site (BEDFORD)
>
> This change prevents receipt creation against storerooms that are in a
> pending deactivation state. Existing environments may have storerooms
> that were previously accepted but no longer pass the new validation.

> **Invoice Matching**
> 3-way match (PO → Receipt → Invoice) is now the default for all purchase
> orders. Previously this was an optional configuration.

> **PO Approval**
> PO approval now requires organization-level authorization in addition to
> site-level authorization. Users with site-only approval roles may be
> affected.

---

## Impact Assessment (for AI Agent to validate)

| P2P Step | Expected Impact | Test |
|----------|----------------|------|
| Create PR | Low — no changes to PR creation | test_06_pr.py |
| Approve PR | Low — no PR approval changes | test_06_pr.py |
| Create PO | Medium — vendor validation may be affected | test_07_po.py |
| Approve PO | **High** — org-level auth requirement is new | test_07_po.py |
| Create Receipt | **High** — storeroom validation CONFIRMED failing | test_07_po.py |
| Create Invoice | **High** — 3-way match now required | test_07_po.py |
| UI End-to-End | **High** — storeroom dropdown affected | test_10_ui_procurement_lifecycle.py |

---

## Expected AI Agent Behaviour

When the TestForge AI pipeline reads this issue, it should:

### Step 1 — Agent 1 (Requirement Analyser)
- Read this issue fully
- Identify the affected area: Procure-to-Pay — Receiving / Receipt
- Cross-reference MAS 9.2 change notes in `.bob/skills/regression-impact/mas-change-catalog.md`
- Map to `pr_to_po` workflow (not `full_regression` — targeted selection)
- Produce impact analysis with `pr_to_po` as CRITICAL priority

### Step 2 — Agent 2 (Test Strategist)
- Strategy decision: `API_AND_UI` (critical workflow + known UI symptom)
- Estimate: ~9 minutes, saves 6h manual effort
- Command: `python orchestrator.py --workflow pr_to_po`

### Step 3 — Agent 3 (API Test Runner)
- Run `test_06_pr.py` and `test_07_po.py`
- Expected: PR tests PASS, PO receipt test FAIL with 400/BMXAA4073E

### Step 4 — Agent 4 (UI Test Runner)
- Run `test_10_ui_procurement_lifecycle.py`
- Expected: PR→PO PASS, Receipt step FAIL

### Step 5 — Agent 5 (Failure Analyst)
- Classify receipt failure as: **TEST_DATA** (storeroom CENTRAL is inactive)
- NOT APPLICATION_DEFECT (Maximo is working correctly — storeroom config is the issue)
- Evidence: HTTP 400, BMXAA4073E, "storeroom not valid"
- Fix suggestion: "Activate storeroom CENTRAL in Maximo: Inventory → Storerooms → CENTRAL → Status → ACTIVE"
- Rerun required: YES after data fix

### Step 6 — Reporter
- Email sent with: failure analysis, fix steps, P2P chain status
- Subject: `[Maximo AI Agent] Pr To Po - FAILURE - 2026-08-26 HH:MM`

---

## Acceptance Criteria

- [ ] Agent reads this issue and identifies `pr_to_po` as the target workflow
- [ ] Regression scope is `pr_to_po` — NOT `full_regression` (AI regression selection)
- [ ] Receipt failure classified as `TEST_DATA` (not APPLICATION_DEFECT)
- [ ] Fix suggestion includes the specific storeroom name (CENTRAL) and path
- [ ] Email report delivered with complete failure analysis
- [ ] Hours saved quantified: "6h manual effort automated"
- [ ] Issue updated with analysis summary

---

## How to Trigger the AI Analysis

### Option A — Via Bob IDE (Test Architect Mode)
1. Switch to `test-architect` mode in Bob IDE
2. Say: *"Read hackathon/github-issue-P2P-001.md and run the appropriate regression tests"*
3. Bob will activate `requirement-analyser` skill, then `regression-impact` skill
4. Bob will run: `python orchestrator.py --workflow pr_to_po`

### Option B — Direct CLI
```bash
python orchestrator.py --workflow pr_to_po
```

### Option C — Via Bob Shell (non-interactive)
```bash
bob --message "Run pr_to_po regression workflow and send email report" \
    --chat-mode test-architect
```

---

## Resolution Notes

*(To be filled by AI Agent after analysis)*

**Analysis performed**: [PENDING]
**Classification**: [PENDING]
**Fix applied**: [PENDING]
**Verified**: [PENDING]
**Closed**: [PENDING]
