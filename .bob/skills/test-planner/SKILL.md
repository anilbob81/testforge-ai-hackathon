---
name: test-planner
description: >-
  Plan the test execution strategy for a given Maximo workflow or impact analysis.
  Decides API vs UI coverage, execution order, and parallel execution opportunities.
  Use after requirement analysis to produce a concrete execution plan.
---

# Test Planner Skill

When activated, build a concrete test execution plan from an impact analysis or
workflow name. This skill determines HOW to test — API vs UI vs both, sequencing,
and parallelism. It is the bridge between analysis and execution.

---

## Input: What You Need to Start

Either:
- A workflow name from `workflow_map.json` (e.g. `pr_to_po`)
- Or a completed impact analysis from the requirement-analyser skill

Always read `workflow_map.json` first to understand what tests exist.

---

## Step 1 — Understand the Workflow

For the given workflow, extract:
- What business process does it validate?
- Which API test files cover it?
- Which UI (Selenium) test files cover it?
- What is the priority (critical / high / medium)?
- What is the manual hours equivalent?

---

## Step 2 — Choose API vs UI vs Both

Use the selection table in `test-selection-guide.md` for detailed guidance.

Quick rules:
| Scenario | Recommendation |
|----------|---------------|
| Create / Read operations | API |
| Status transitions (WAPPR → APPR) | API preferred, UI if approval is UI-only |
| Approval workflows | UI/API depending on requirement |
| Field validation / field layout | Selenium (UI) |
| End-to-end business workflow | Selenium (UI) |
| Fast regression (< 60s) | API only |
| Post-upgrade UI verification | Selenium (UI) |
| All tests for a critical workflow | API + UI (both) |

---

## Step 3 — Sequence the Tests

For P2P workflows, sequence is mandatory — each step depends on the previous:
```
PR Create → PR Approve → PO Create → PO Approve → Receipt → Invoice
```

For independent workflows, parallel execution is possible:
```
PR API test ──┐
PO API test ──┤── all run in parallel (pytest -n auto)
Receipt test ─┘
```

---

## Step 4 — Estimate Runtime

Use these average times per test type:
- API test module: ~8 seconds per file (5 tests per file × 1.6s each)
- UI test module: ~9 minutes per file (6 tests × 90s each)
- Full P2P API suite: ~16 seconds
- Full P2P UI suite: ~9 minutes
- Full regression (all 78): ~15 minutes

Communicate clearly: "This will take ~9 minutes vs 6h manual equivalent (95% time reduction)."

---

## Step 5 — Output the Execution Plan

Produce a structured plan:

```json
{
  "workflow_name": "pr_to_po",
  "strategy": "API_AND_UI",
  "rationale": "Critical workflow — full stack validation required after upgrade.",
  "run_api": true,
  "run_ui": true,
  "api_test_files": ["tests/api/test_06_pr.py", "tests/api/test_07_po.py"],
  "ui_test_files": ["tests/ui/test_10_ui_procurement_lifecycle.py"],
  "estimated_seconds": 556,
  "manual_hours_equivalent": 6.0,
  "cli_command": "python orchestrator.py --workflow pr_to_po"
}
```

---

## Output Checklist

Before finishing, verify:
- [ ] Strategy chosen (API_ONLY / UI_ONLY / API_AND_UI) with rationale
- [ ] Test files identified and confirmed to exist
- [ ] Runtime estimated (automated vs manual comparison)
- [ ] CLI command provided for immediate execution
- [ ] Any missing test coverage flagged as a gap
