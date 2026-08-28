---
name: regression-impact
description: >-
  Map a MAS version upgrade or change log to the impacted test workflows.
  Use when MAS has been upgraded and you need to determine which regression
  tests to run. Produces AI-driven regression selection - not "run all 78 tests".
  Backed by Agent 0 (Upgrade Scout) which reads real IBM Docs and performs
  live Maximo schema diffs via MCP.
---

# Regression Impact Analyser Skill

When activated, map a MAS version change or change description to the minimum
viable set of test workflows. This is AI-driven regression selection - the goal
is to run the RIGHT tests, not ALL tests.

---

## IMPORTANT: Use Agent 0 (Upgrade Scout) for Real Intelligence

Before manually analysing change documents, run Agent 0 to get live data:

```bash
# Save baselines (first time, or after upgrade)
python orchestrator.py --scout

# Or run the full pipeline which includes Agent 0 automatically
python orchestrator.py --workflow pr_to_po
```

Agent 0 provides THREE live intelligence sources:
1. IBM Docs scrape - fetches the real What's New page from IBM documentation
2. Live schema diff (MCP) - queries OSLC API for MXWO, MXASSET, MXSR, MXLOCATION,
   MXINVENTORY and diffs field lists against stored baselines in baselines/
3. Domain diff (MCP) - compares WOSTATUS, PRSTATUS, POSTATUS values before/after

If reports/upgrade_scout_report.json exists, read it first - it contains
the real impacted workflows derived from live Maximo system data, not assumptions.

---

## The Core Insight

> "Instead of running 500 regression tests, the AI recommends: Run these 47 first."

This is the most valuable capability for a testing team facing upgrade cycles.
Every MAS release changes specific areas. Tests for unchanged areas add no value.
This skill identifies exactly which tests cover changed areas.

---

## Step 1 — Parse the Change Document

Read the provided change information and extract:
- Source version → Target version (e.g. MAS 9.1 → 9.2)
- List of changed modules/applications
- List of changed behaviours or rules
- Any known breaking changes or migration notes

Sources to read:
- Provided release notes / change description
- `hackathon/github-issue-P2P-001.md` (example issue for P2P scenario)
- `.bob/skills/regression-impact/mas-change-catalog.md` (version change reference)

---

## Step 2 -- Map Changes to Functional Areas

For each change identified, determine which Maximo functional area it affects.
Use the MAS Change Catalog (`mas-change-catalog.md`) as your reference.

Output a change-to-area mapping:
```
MAS 9.2 change: "Storeroom validation tightened"
  → Functional area: Receiving / Receipt
  → Impact level: HIGH
  → Evidence: "must now be ACTIVE and org-linked"
```

---

## Step 3 — Map Functional Areas to Test Workflows

Use `workflow_map.json` to identify which test workflows cover each impacted area.

| Changed Area | Impact | Test Workflow | Tests Affected |
|-------------|--------|---------------|----------------|
| Storeroom validation | HIGH | pr_to_po | test_07_po.py (receipt tests) |
| PO approval | HIGH | pr_to_po | test_07_po.py (approval tests) |
| WO status logging | LOW | work_order | test_01_workorder.py |

---

## Step 4 — Score and Prioritise

Score each workflow based on the number and severity of impacted areas:

| Workflow | Impact Score | Priority | Rationale |
|----------|-------------|----------|-----------|
| pr_to_po | 3×HIGH | CRITICAL | 3 high-impact areas directly in this workflow |
| work_order | 1×LOW | LOW | Minor change, no breaking behaviour |
| asset_management | 0 | SKIP | Zero changes in this area |

---

## Step 5 — Output the Minimum Viable Test Set

State the recommendation clearly:

> "For MAS 9.2 upgrade: Run `pr_to_po` workflow (18 tests, ~9 min)."
> "Do NOT run `asset_management`, `service_request`, `wo_from_jobplan` — zero impact."
> "This is 18 tests instead of 78. Saves 5.2h vs full regression."

Produce the CLI command:
```bash
python orchestrator.py --workflow pr_to_po
```

And the JSON plan for Agent 1 consumption:
```json
{
  "trigger": "MAS 9.2 upgrade",
  "source_version": "9.1",
  "target_version": "9.2",
  "changed_areas": ["storeroom_validation", "po_approval", "invoice_matching"],
  "recommended_workflows": ["pr_to_po"],
  "skipped_workflows": ["asset_management", "service_request", "work_order"],
  "skip_rationale": {"asset_management": "no_changes", "service_request": "no_changes", "work_order": "low_impact_only"},
  "total_tests": 18,
  "estimated_minutes": 9,
  "manual_hours_saved": 6.0,
  "full_regression_tests": 78,
  "tests_avoided": 60,
  "efficiency_gain": "77% fewer tests, same coverage for changed areas"
}
```

---

## Output Checklist

Before finishing, verify:
- [ ] All changed areas identified from the change document
- [ ] All changed areas mapped to test workflows
- [ ] Skipped workflows have explicit rationale ("no changes in this area")
- [ ] Total tests and estimated runtime calculated
- [ ] Efficiency gain quantified (N tests instead of 78)
- [ ] CLI command provided for immediate use
