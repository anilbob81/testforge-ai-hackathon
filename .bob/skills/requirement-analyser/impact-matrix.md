# Impact Matrix Reference Guide
# Used by the requirement-analyser skill
# Provides standard impact assessment patterns for IBM Maximo Application Suite

---

## How to Use This Guide

When analysing a change, find the relevant Maximo application/module in the tables below.
Use the "Typical Impact Triggers" column to match what changed to an impact level.
Cross-reference the "Affected Test Workflows" column to know which tests to recommend.

---

## Procure-to-Pay (P2P) Impact Patterns

| Functional Area | High Impact Triggers | Medium Impact Triggers | Affected Workflows |
|----------------|---------------------|----------------------|-------------------|
| PR Creation | PR field schema change, autonumber config, status WAPPR change | New validation rules | pr_to_po |
| PR Approval | Approval workflow config, role changes, APPR status | Approval routing | pr_to_po |
| PR → PO Conversion | PO creation from PR, field mapping | Line item handling | pr_to_po |
| PO Approval | PO approval routing, APPR status transition | PO value thresholds | pr_to_po |
| Goods Receipt | Storeroom validation, receiving app changes | Quantity tolerance | pr_to_po |
| Invoice Matching | 3-way match requirement, GL account changes | Invoice tolerance | pr_to_po |
| Vendor Management | Vendor status validation, ACTIVE/INACTIVE rules | Vendor search | pr_to_po |

**Key insight**: Any change to the Purchasing or Receiving module in MAS impacts the entire
P2P chain. Recommend `pr_to_po` workflow for any procurement-related change.

---

## Work Order Impact Patterns

| Functional Area | High Impact Triggers | Medium Impact Triggers | Affected Workflows |
|----------------|---------------------|----------------------|-------------------|
| WO Creation | WO field schema, WAPPR status, autonumber | Description field changes | work_order |
| WO Approval | Approval routing, APPR transition | Role-based approval | work_order |
| WO Status Flow | INPRG, COMP, CLOSE status transitions | Status date recording | work_order |
| Labour / Craft | Labour reporting, timesheet integration | Craft rate changes | work_order |
| Location Lookup | Location hierarchy changes, BEDFORD site | Operating location | work_order, asset_management |

---

## Preventive Maintenance Impact Patterns

| Functional Area | High Impact Triggers | Affected Workflows |
|----------------|---------------------|-------------------|
| PM Schedule | PM frequency, activation logic | pm_maintenance |
| PM → WO Generation | Auto-generate WO from PM trigger | pm_maintenance, wo_from_jobplan |
| Job Plan | Task definition, craft assignment | pm_maintenance, wo_from_jobplan |
| Job Plan → WO | Task creation from JP, WOACTIVITY | wo_from_jobplan |

---

## Asset & Location Impact Patterns

| Functional Area | High Impact Triggers | Affected Workflows |
|----------------|---------------------|-------------------|
| Asset Creation | Asset number format, operating status | asset_management |
| Location Hierarchy | Parent-child location structure | asset_management |
| Asset Status | OPERATING, DECOMMISSIONED transitions | asset_management |
| Asset → WO Link | Asset association on WO creation | work_order, asset_management |

---

## Service Request Impact Patterns

| Functional Area | High Impact Triggers | Affected Workflows |
|----------------|---------------------|-------------------|
| SR Creation | SR field schema, affected person lookup | service_request |
| SR Priority | Priority classification rules | service_request |
| SR → WO Conversion | SR to WO conversion workflow | service_request |

---

## MAS 9.2 Known Changes (Reference)

These are the confirmed changes in MAS 9.2 that affect testing:

| Change | Area | Impact Level | Affected Workflow |
|--------|------|-------------|------------------|
| Storeroom validation tightened — must be ACTIVE | Receiving | HIGH | pr_to_po |
| PO approval now requires org-level authorization | PO Approval | HIGH | pr_to_po |
| PR autonumber sequence format changed | PR Creation | MEDIUM | pr_to_po |
| Work Order WAPPR → APPR transition now logs approver | WO Approval | LOW | work_order |
| Asset operating status validation tightened | Asset Status | LOW | asset_management |
| Invoice 3-way match now default (was optional) | Invoice | HIGH | pr_to_po |

**MAS 9.2 Verdict**: Run `pr_to_po` regression first. Then `work_order`. Skip others unless time allows.

---

## Confidence Levels

| Level | Meaning |
|-------|---------|
| HIGH | Change notes explicitly mention this area |
| MEDIUM | Change notes imply this area may be affected |
| LOW | Area is adjacent to the change — worth monitoring |
| NONE | No connection between change and this area |

---

## Impact Score → Recommendation

| Score | Recommendation |
|-------|---------------|
| 3+ HIGH areas | Run full_regression |
| 1-2 HIGH areas | Run targeted workflow(s) covering those areas |
| MEDIUM only | Run API-only fast validation |
| LOW / NONE | Skip — monitor next release |
