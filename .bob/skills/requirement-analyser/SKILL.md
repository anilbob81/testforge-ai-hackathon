---
name: requirement-analyser
description: >-
  Analyse a Maximo upgrade, change request, or GitHub issue and identify
  which test workflows are impacted. Use when given release notes, a change
  description, or a scenario like "MAS upgraded from 9.1 to 9.2 — validate P2P".
---

# Requirement Analyser Skill

When activated, follow this structured process to map a change requirement to
the correct test workflows. This demonstrates IBM Bob 2.0 Document Understanding.

---

## Step 1 — Parse the Change Description

Read the input carefully and extract:
- **What changed?** (application, module, feature)
- **Which MAS version?** (source → target, e.g. 9.1 → 9.2)
- **What is the stated risk?** (what might break)
- **Is there a GitHub issue?** If so, read it fully and extract the failure evidence

Example inputs:
> "MAS has been upgraded to 9.2. Validate that P2P still works."
> "PR approval workflow was changed. Receipt validation is now stricter."
> "GitHub Issue #001: P2P receipt failing with BMXAA4073E after upgrade."

---

## Step 2 — Read Supporting Documents

Always read these in order:
1. `workflow_map.json` — the full test catalogue (available workflows + test files)
2. `MAXIMO_TEST_AUTOMATION_FRAMEWORK.md` (in maximo-regression-tests/) — business context
3. `.bob/skills/regression-impact/mas-change-catalog.md` — MAS version change reference
4. `hackathon/PLAN.md` — current project context and prior decisions

---

## Step 3 — Produce an Impact Matrix

Output a table mapping each functional area to its potential impact level.
Use the `impact-matrix.md` reference in this skill folder for guidance.

| Area | Potential Impact | Evidence | Test Workflow |
|------|-----------------|----------|---------------|
| PR creation | High | PO approval workflow mentioned | pr_to_po |
| PO approval | High | Approval process changed | pr_to_po |
| PR → PO conversion | High | Direct impact of PR changes | pr_to_po |
| Receiving / Receipt | Medium | Storeroom validation note | pr_to_po |
| Invoice matching | High | 3-way match now required | pr_to_po |
| Work Order status | Low | No mention in change notes | work_order |
| Asset hierarchy | None | Not referenced | asset_management |

---

## Step 4 — Recommend Regression Scope

Based on the impact matrix, state the recommended scope:

> "Recommended regression scope: **pr_to_po** workflow"
> "Rationale: Changes directly affect PR, PO, Receipt, and Invoice steps."
> "Instead of running 78 tests, run these 18 first (saves 6h manual effort)."

Priority rules:
- **CRITICAL**: Any HIGH impact area → run immediately
- **HIGH**: MEDIUM impact areas → run before sign-off
- **MEDIUM**: LOW impact areas → include in next regression window
- **SKIP**: NONE impact areas → do not run, save time

---

## Step 5 — Output Structured Analysis JSON

Produce a JSON block that can be consumed by the Test Planner / orchestrator:

```json
{
  "workflow_name": "pr_to_po",
  "trigger": "MAS 9.2 upgrade — procurement workflow changes",
  "impact_areas": ["PR creation", "PO approval", "Receipt", "Invoice"],
  "priority": "critical",
  "recommended_workflows": ["pr_to_po"],
  "skip_workflows": ["asset_management", "service_request"],
  "rationale": "Procurement changes in 9.2 directly impact the full P2P chain.",
  "manual_hours_equivalent": 6.0,
  "confidence": "HIGH"
}
```

---

## Output Checklist

Before finishing, verify:
- [ ] Impact matrix produced (all major areas assessed)
- [ ] At least one recommended workflow identified
- [ ] Rationale explains WHY each workflow was included/excluded
- [ ] Hours saved quantified
- [ ] JSON analysis block produced for downstream agents
- [ ] Any missing test coverage flagged (gap analysis)

---

## What NOT to Do

- Do NOT recommend running `full_regression` unless every area is impacted
- Do NOT modify any test files — read only
- Do NOT guess — if the change notes are unclear, say so and ask for clarification
- Do NOT skip the impact matrix — it is the evidence trail for the recommendation
