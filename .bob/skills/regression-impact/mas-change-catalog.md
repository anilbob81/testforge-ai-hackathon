# MAS Change Catalog
# Used by the regression-impact skill
# Maps IBM Maximo Application Suite version changes to affected functional areas

---

## How to Use

When given a MAS version upgrade description, find the relevant version range
in this catalog. Use the "Affected Functional Areas" to drive the impact matrix.
For changes not in this catalog, use the general pattern guidelines at the bottom.

---

## MAS 9.1 → 9.2 Changes (Reference for Hackathon Demo)

### Procurement / Purchasing Changes

| Change | Description | Impact | Affected Tests |
|--------|-------------|--------|----------------|
| Storeroom validation tightened | Storerooms must be ACTIVE and org-linked to receive goods | HIGH | test_07_po.py (receipt tests) |
| PO approval org-level auth | PO approval now requires org-level authorization role | HIGH | test_07_po.py (approval tests) |
| PR autonumber format | PR autonumber sequence format changed (prefix added) | MEDIUM | test_06_pr.py |
| Invoice 3-way match | 3-way matching now default for all POs (was optional) | HIGH | test_07_po.py (invoice tests) |
| Vendor status validation | Vendors must be ACTIVE at time of PO creation | MEDIUM | test_07_po.py, test_06_pr.py |

**P2P Verdict**: CRITICAL — run `pr_to_po` workflow immediately.

---

### Work Order Changes

| Change | Description | Impact | Affected Tests |
|--------|-------------|--------|----------------|
| WO approval logging | Approver name now logged in WOAPPROVAL table | LOW | test_01_workorder.py |
| WAPPR status description | Status label changed, not behaviour | NONE | N/A |

**WO Verdict**: LOW — monitor, include in next scheduled regression.

---

### Asset / Location Changes

| Change | Description | Impact | Affected Tests |
|--------|-------------|--------|----------------|
| Asset operating status | Additional validation on DECOMMISSIONED transition | LOW | test_03_asset.py |
| Location hierarchy | No changes to hierarchy rules | NONE | N/A |

**Asset Verdict**: LOW — not required for immediate post-upgrade validation.

---

### Preventive Maintenance Changes

| Change | Description | Impact | Affected Tests |
|--------|-------------|--------|----------------|
| PM generation frequency | No changes | NONE | N/A |
| Job Plan task association | Minor UI label changes only | NONE | N/A |

**PM Verdict**: NONE — skip entirely for 9.2 upgrade validation.

---

### Service Request Changes

| Change | Description | Impact | Affected Tests |
|--------|-------------|--------|----------------|
| SR priority rules | No changes | NONE | N/A |
| Affected person lookup | Performance improvement only | NONE | N/A |

**SR Verdict**: NONE — skip for 9.2 upgrade validation.

---

## MAS 9.0 → 9.1 Changes (Historical Reference)

| Change | Area | Impact |
|--------|------|--------|
| New approval workflow engine | Work Orders, PRs | HIGH |
| REST API pagination default changed | All API tests | MEDIUM |
| Selenium DOM IDs refactored | All UI tests | HIGH (LOCATOR_DRIFT risk) |
| Job Plan craft assignment UI | PM, WO | MEDIUM |

**9.0→9.1 Verdict**: Run `full_regression` — UI DOM changes affect all Selenium tests.

---

## MAS 8.x → 9.x Migration (Major Version Change)

Any major version upgrade (8.x → 9.x) should trigger `full_regression`.
Major versions introduce significant DOM structure changes, API breaking changes,
and business rule updates that affect all functional areas.

---

## General Pattern Guidelines

When you have a change description but no version catalog entry, use these patterns:

| Change Keywords | Likely Impact Area | Risk |
|----------------|-------------------|------|
| "storeroom", "receiving", "receipt" | Procurement P2P | HIGH |
| "approval", "routing", "workflow" | Any approval flow | HIGH |
| "vendor", "supplier", "company" | Procurement P2P | HIGH |
| "invoice", "matching", "GL account" | Procurement P2P | HIGH |
| "work order", "WO", "WAPPR" | Work Order | HIGH |
| "preventive", "PM", "job plan" | PM Maintenance | MEDIUM |
| "asset", "location", "hierarchy" | Asset Management | MEDIUM |
| "service request", "SR" | Service Request | LOW |
| "UI", "DOM", "page", "locator" | All Selenium tests | HIGH (LOCATOR_DRIFT) |
| "API", "REST", "OSLC", "schema" | All API tests | MEDIUM |
| "authentication", "API key", "session" | All tests (ENVIRONMENT_AUTH) | HIGH |
| "performance", "timeout", "slow" | Timing (all tests) | LOW (TIMING_ENVIRONMENT) |

---

## Regression Scope Decision Matrix

| Impact Summary | Recommended Scope | Estimated Time |
|---------------|------------------|----------------|
| 3+ HIGH in P2P area | pr_to_po | ~9 minutes |
| 2+ HIGH in WO area | work_order | ~6 minutes |
| Mixed HIGH across areas | Multiple targeted workflows | ~15 minutes |
| HIGH in UI/DOM | Full regression (UI tests) | ~15 minutes |
| MEDIUM only | API-only suite | ~20 seconds |
| LOW / NONE | Skip — monitor | 0 minutes |
| Major version upgrade | full_regression | ~15 minutes |
