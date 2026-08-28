# Test Selection Guide
# Used by the test-planner skill
# Decides which test type (API / Selenium UI / Both) to use for each scenario

---

## The Core Decision

API tests and Selenium UI tests are complementary — not interchangeable.
Use this guide to pick the right layer for each testing scenario.

---

## API vs UI: When to Use Each

### Use API Tests When:

| Scenario | Example | Why API |
|----------|---------|---------|
| Creating records | Create PR, Create WO | Fast, reliable, no browser needed |
| Verifying status transitions | PR WAPPR → APPR | Direct state check via REST |
| Reading/querying records | Get WO by number | Instant, no UI rendering wait |
| Validating field values | Check PR description | API response is ground truth |
| Schema/structure validation | Field exists, type correct | API exposes schema directly |
| Fast regression (< 30s) | All CRUD operations | 58 API tests in under 20 seconds |
| Parallel execution | Multiple object types | API calls are fully parallelisable |

### Use Selenium UI Tests When:

| Scenario | Example | Why UI |
|----------|---------|--------|
| UI field layout validation | Fields visible on screen | Only UI can verify visual elements |
| Button/link availability | Approve button present | User-facing functionality |
| Navigation flow | Click PR → see PO | Full user journey validation |
| End-to-end business workflow | PR → PO → Receipt → Invoice | Validates the complete user experience |
| Post-upgrade visual regression | DOM structure changed | Catches locator drift after upgrades |
| Workflow that requires UI input | Approval via UI only | Some approvals cannot be done via API |

### Use Both (API + UI) When:

| Scenario | Why Both |
|----------|----------|
| CRITICAL priority workflow | Backend correctness + frontend usability |
| Post-major-upgrade validation | API confirms data, UI confirms experience |
| P2P full lifecycle | API for data creation, UI for end-to-end flow |
| Pre-release sign-off | Both layers must pass before deployment |

---

## P2P Scenario Mapping (Reference)

| P2P Step | Recommended Test Type | Test File |
|----------|----------------------|-----------|
| Create PR | API | test_06_pr.py |
| Validate PR data | API | test_06_pr.py |
| Approve PR | API (status transition) | test_06_pr.py |
| Create PO from PR | API | test_07_po.py |
| Approve PO | UI/API (config dependent) | test_07_po.py / test_10_ui |
| Receive goods | API | test_07_po.py |
| Create invoice | API | test_07_po.py |
| Verify UI fields | Selenium | test_10_ui_procurement_lifecycle.py |
| End-to-end flow | Selenium | test_10_ui_procurement_lifecycle.py |

---

## Work Order Scenario Mapping (Reference)

| WO Step | Recommended | Test File |
|---------|-------------|-----------|
| Create WO | API | test_01_workorder.py |
| WO status transitions | API | test_01_workorder.py |
| Location lookup | API | test_02_location.py |
| WO approval via UI | Selenium | test_08_ui_workorder.py |
| WO end-to-end | Selenium | test_08_ui_workorder.py |

---

## Strategy by Priority

| Workflow Priority | Default Strategy | Override When |
|------------------|-----------------|---------------|
| CRITICAL | API + UI (both) | Time constraint → API only first |
| HIGH | API + UI if UI exists, else API only | Fast feedback needed → API first |
| MEDIUM | API only | Explicit UI coverage needed |
| LOW / api_only | API only | Never add UI for low-priority |

---

## Parallel Execution Opportunities

These test modules are independent and can run in parallel:
```
tests/api/test_02_location.py ──┐
tests/api/test_03_asset.py     ──┤── Run simultaneously
tests/api/test_08_sr.py        ──┘

tests/api/test_06_pr.py ──→ tests/api/test_07_po.py  (sequential — PO needs PR number)
```

To run with parallelism: `pytest tests/api/ -n auto` (requires pytest-xdist)

Sequential dependencies in P2P:
```
PR tests → PO tests → Receipt → Invoice
(each step uses the record number from the previous step)
```

---

## Time Budget Guidelines

| Budget | Strategy | What to Run |
|--------|----------|-------------|
| < 1 minute | API-only fast | test_00_schema_check + target API module |
| < 5 minutes | API full suite | All 10 API modules (58 tests) |
| < 15 minutes | API + 1 UI module | Targeted workflow |
| < 30 minutes | Full regression | All 78 tests (10 API + 3 UI) |
| Unlimited | Full regression + re-run failures | Most thorough |
