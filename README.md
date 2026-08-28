# 🤖 TestForge AI — Maximo Autonomous Test Engineer
### IBM Bob 2.0 Hackathon — IBM TechXchange 2026 Dev Day · Aug 28–30

---

## What This Is

A **7-agent AI-orchestrated pipeline** that transforms a single plain-English command
into a full Maximo regression test run — IBM Docs scraping, schema diffing, API tests,
Selenium UI tests, AI failure classification, autonomous locator healing, and an email
report — completely autonomous.

**One command. Seven agents. Live results. Email delivered.**

```bash
python orchestrator.py --workflow pr_to_po
```

---

## The Problem It Solves

IBM Maximo customers receive upgrades every few weeks. Each upgrade requires validating
that critical business processes still work — Work Orders, Procurement P2P, Preventive
Maintenance, etc.

| | Before | After |
|---|---|---|
| **Time per upgrade validation** | 2–3 days manual | ~15 minutes automated |
| **Consultant hours** | 16–24 hours | 0 hours |
| **Failure detection** | Days later | Within 15 minutes |
| **Root cause analysis** | Hours of log trawling | Instant AI classification |
| **Who can run it** | Senior engineer only | Any team member |

---

## The 7-Agent Pipeline

```
You type:  python orchestrator.py --workflow pr_to_po
               ↓
[Agent 0 — Upgrade Scout]
  Scrapes IBM Docs "What's New in Maximo 9.2" for real change items
  Queries live Maximo OSLC API — diffs 5 object structures vs baselines
  Diffs domain status values (WOSTATUS, PRSTATUS, POSTATUS)
  Identifies impacted workflows from live intelligence (MCP pattern)
               ↓
[Agent 1 — Requirement Analyser]
  Reads MAXIMO_TEST_AUTOMATION_FRAMEWORK.md (Document Understanding)
  Reads workflow_map.json + Agent 0 scout report
  Maps 'pr_to_po' → test_06_pr + test_07_po + test_10_ui_procurement
  Produces impact analysis with business context
               ↓
[Agent 2 — Test Strategist]
  Decides: API + UI (critical workflow — both layers needed)
  Estimates: ~9 minutes runtime, 6h manual equivalent
  Strategy: CRITICAL → full stack validation
               ↓
[Agent 3 — API Test Runner]           [Agent 4 — UI Test Runner]
  Runs pytest API tests                 Opens Chrome (Selenium WebDriver)
  test_06_pr + test_07_po               Drives PR→PO→Receipt→Invoice
  ~4 seconds                            ~9 minutes
               ↓                              ↓
               └──────────────┬───────────────┘
                              ↓
[Agent 5 — Failure Analyst]
  Reads tracebacks for every failed test
  Queries live Maximo via REST API to confirm record state (MCP pattern)
  Classifies: APPLICATION_DEFECT / LOCATOR_DRIFT / TIMING / AUTH / TEST_DATA
  Suggests exact fix per failure (not just the error message)
               ↓
[Agent 6 — Locator Healer]  (only if LOCATOR_DRIFT failures exist)
  Probes Maximo DOM for candidate replacement elements
  Fuzzy-matches to find best replacement locator
  Patches test file (.bak backup created first)
  Re-runs patched test — if pass: HEALED; if fail: reverts + PROPOSED
               ↓
[Reporter]
  Builds styled HTML report with all 7 agent results
  Includes Upgrade Scout banner + Locator Healer summary
  Sends email to team with report attached
```

---

## IBM Bob 2.0 Features Used

| Feature | Where | What It Does |
|---------|-------|-------------|
| **Agent Mode** | Entire orchestrator | Runs all 7 agents, executes pytest, sends email |
| **Subagents** | Agent 0 + 1 + 2 | Isolated doc/web reading + parallel planning |
| **Document Understanding** | Agent 0 + 1 | IBM Docs scraping + 67-page framework doc |
| **MCP Pattern** | Agent 0 + 5 | Live schema diff + failure context queries |
| **Parallel Tasks** | Agent 3 + 4 | API and UI tests designed for concurrent execution |
| **Autonomous Re-test** | Agent 6 | Heals LOCATOR_DRIFT failures + re-runs automatically |
| **Custom Skills** | `.bob/skills/` | 5 reusable skills (see table below) |
| **Custom Modes** | `.bob/custom_modes.yaml` | 4 specialist AI personas |
| **Rules / Guides** | `.bob/rules.md` | Steers Bob before every action (feedforward) |
| **Quality Gates** | `.bob/hooks/` | Machine-runnable sensors (feedback loop) |
| **PR Generation** | Git workflow | Bob generates commit messages and PR descriptions |

### The 5 Custom Skills

| Skill | When Bob Activates It |
|-------|----------------------|
| `requirement-analyser` | Given an upgrade description or GitHub issue |
| `test-planner` | Planning API vs UI coverage for a workflow |
| `failure-investigator` | Investigating a specific test failure |
| `regression-impact` | Mapping a MAS version change to test scope |
| `test-data-validator` | Verifying Maximo reference data before test run |

### The 4 Custom Modes

| Mode | Purpose |
|------|---------|
| 🏗️ `test-architect` | Planning regression coverage for upgrades/changes |
| 🔍 `failure-investigator` | Root cause analysis of test failures |
| 📊 `regression-analyst` | Mapping MAS release notes to test scope |
| 📝 `report-writer` | Generating release-readiness reports |

### Guides vs Sensors (Bob 2.0 Control Concept)

```
GUIDES (Feedforward — steer BEFORE Bob acts):
  .bob/rules.md                ← Project rules Bob follows on every turn
  .bob/custom_modes.yaml       ← Right persona for each task type
  .bob/skills/                 ← Specialist knowledge for each agent role

SENSORS (Feedback — observe AFTER Bob acts):
  .bob/hooks/pre-commit.py     ← Quality gate before every commit
  .bob/hooks/schema-verify.py  ← Maximo connectivity probe
  reports/ HTML reports        ← Pipeline completion confirmation
  Email delivery               ← End-to-end verification
```

---

## Available Workflows

| Workflow | Description | Modules | Est. Time | Manual Hours |
|----------|-------------|---------|-----------|-------------|
| `api_only` | All 58 API tests — fastest | 10 API | ~20 sec | 14.5h |
| `pr_to_po` | Purchase Requisition → PO lifecycle | 2 API + 1 UI | ~9 min | 6.0h |
| `work_order` | Work Order create → approve → complete | 1 API + 1 UI | ~6 min | 3.0h |
| `pm_maintenance` | PM lifecycle + WO generation | 2 API + 1 UI | ~10 min | 4.0h |
| `asset_management` | Asset + Location hierarchy | 2 API | ~20 sec | 2.0h |
| `service_request` | Service Request lifecycle | 1 API | ~10 sec | 1.5h |
| `wo_from_jobplan` | End-to-end WO from Job Plan | 2 API | ~15 sec | 2.5h |
| `full_regression` | All 78 tests — complete suite | 10 API + 3 UI | ~15 min | 29.5h |

---

## Quick Start

```bash
# 1. Install dependencies
cd maximo-ai-agent
pip install -r requirements.txt

# 2. Run quality gate (verifies project integrity)
python .bob/hooks/pre-commit.py

# 3. Verify Maximo is reachable
python .bob/hooks/schema-verify.py

# 4. List available workflows
python orchestrator.py --list

# 5. Run the killer demo workflow
python orchestrator.py --workflow pr_to_po

# 6. Run without email (saves report to reports/ folder)
python orchestrator.py --workflow pr_to_po --no-email

# 7. Fastest run (API only — 20 seconds)
python orchestrator.py --workflow api_only
```

---

## Failure Classification

Agent 5 classifies every failure automatically with evidence and a fix suggestion:

| Category | Meaning | Example | Fix Owner |
|----------|---------|---------|-----------|
| 🔴 **APPLICATION_DEFECT** | Maximo returned unexpected data | Status WAPPR after upgrade (expected APPR) | Maximo Admin |
| 🟡 **LOCATOR_DRIFT** | Selenium element ID changed | `StaleElementReferenceException` | Test Engineer |
| 🟠 **TIMING_ENVIRONMENT** | Server response too slow | `TimeoutException` + empty list | DevOps / Retry |
| 🔵 **ENVIRONMENT_AUTH** | API key expired / unreachable | `ConnectionError` or 401 | Infrastructure |
| 🟣 **TEST_DATA** | Reference data missing/inactive | `BMXAA4073E` — storeroom inactive | Maximo Admin |
| ⚪ **UNKNOWN** | Cannot classify | Manual investigation needed | Senior Engineer |

---

## The Explore → Plan → Implement → Verify Loop

This project was built following the structured loop from the hackathon guide:

| Phase | What Happened |
|-------|--------------|
| **Explore** | Read all 5 agents, config, orchestrator, existing reports, hackathon PDF |
| **Plan** | Designed Bob layer: 5 skills, 4 modes, rules, quality gates, demo scenario |
| **Implement** | Bob layer (.bob/), Agent 0 (Upgrade Scout), Agent 6 (Locator Healer), baselines |
| **Verify** | 58/58 API tests pass, 18/18 P2P pass, email confirmed, all 7 quality gates pass |
| **Polish** | Docs updated to 7 agents, issue resolved, screenshots committed, final push |

See [`hackathon/PLAN.md`](hackathon/PLAN.md) for the full tracked plan.

---

## Project Structure

```
maximo-ai-agent/                    ← This project — IBM Bob 2.0 hackathon
├── .bob/
│   ├── custom_modes.yaml           ← 4 specialist modes
│   ├── rules.md                    ← Quality gates + project rules
│   ├── skills/
│   │   ├── requirement-analyser/   ← Impact analysis skill
│   │   ├── test-planner/           ← API vs UI selection skill
│   │   ├── failure-investigator/   ← Root cause classification skill
│   │   ├── regression-impact/      ← MAS version → test mapping skill
│   │   └── test-data-validator/    ← Pre-run data verification skill
│   └── hooks/
│       ├── pre-commit.py           ← Quality gate (run before commit)
│       └── schema-verify.py        ← Maximo connectivity probe
├── agents/
│   ├── agent_00_upgrade_scout.py   ← IBM Docs scrape + live schema diff (MCP)
│   ├── agent_01_analyser.py        ← Document Understanding + workflow mapping
│   ├── agent_02_strategist.py      ← Test strategy planning
│   ├── agent_03_api_runner.py      ← pytest API test execution
│   ├── agent_04_ui_runner.py       ← Selenium UI test execution
│   ├── agent_05_failure_analyst.py ← Failure classification (MCP pattern)
│   └── agent_06_locator_healer.py  ← Autonomous locator healing + re-test
├── baselines/                      ← Live schema snapshots (Agent 0 diffs against these)
│   ├── mxwo_schema.json            ← 159-field WO schema baseline
│   ├── mxasset_schema.json         ← 61-field Asset schema baseline
│   ├── mxapisr_schema.json         ← 84-field SR schema baseline
│   ├── mxapioperloc_schema.json    ← 54-field Location schema baseline
│   └── mxinventory_schema.json     ← 44-field Inventory schema baseline
├── config/agent_config.py          ← Maximo + email configuration
├── reporter/report_builder.py      ← HTML report + SMTP email
├── hackathon/
│   ├── ONBOARDING.md               ← Developer onboarding guide
│   ├── AGENTS.md                   ← Bob /init style project context (7 agents)
│   ├── PLAN.md                     ← Living plan (Explore→Plan→Implement→Verify)
│   ├── github-issue-P2P-001.md     ← Demo scenario GitHub issue (RESOLVED)
│   └── demo-script.md              ← 8-minute demo walkthrough
├── bob_sessions/                   ← Task session screenshots (submission)
│   ├── How all agents are connected.png
│   ├── Test Strategist.png
│   └── Failure Analyst agent.png
├── orchestrator.py                 ← Pipeline entry point (7 agents)
├── workflow_map.json               ← Workflow → test file mappings
├── reports/                        ← Generated HTML reports
└── logs/                           ← Execution logs

maximo-regression-tests/            ← EXISTING SUITE — NEVER MODIFIED
```

> **Zero changes to the existing `maximo-regression-tests/` project.**
> This folder only reads test files from it — never writes to it.

---

## Demo Script

See [`hackathon/demo-script.md`](hackathon/demo-script.md) for the full 8-minute
demo walkthrough including narrative, fallback plans, and key messages.

**Core scenario**: *"MAS has been upgraded to 9.2. Validate that P2P still works."*

The autonomous engineer:
1. **Agent 0**: Reads IBM Docs + live schema diff → detects 5 MAS 9.2 change signals
2. **Agent 1**: Reads GitHub issue — identifies P2P as impacted (AI regression selection)
3. **Agent 2**: Selects `pr_to_po` — 18 tests instead of 78, API + UI strategy
4. **Agent 3**: Runs 10 API tests — PR/PO PASS, Receipt FAIL (HTTP 400 BMXAA4073E)
5. **Agent 4**: Runs 8 Selenium tests — Chrome drives full P2P flow
6. **Agent 5**: Classifies failure as TEST_DATA (storeroom inactive — not a code bug)
7. **Agent 6**: LOCATOR_DRIFT check — none, skipped (all clean)
8. **Reporter**: Email report with root cause + exact fix suggestion

---

## Made with IBM Bob 2.0

> Built entirely in IBM Bob 2.0 Agent mode during the IBM TechXchange 2026 Dev Day Hackathon.
> The existing `maximo-regression-tests/` project was not modified.
> Everything in this folder was generated from scratch using IBM Bob 2.0.

| Bob Feature | Usage Count |
|-------------|------------|
| Custom Skills | 5 |
| Custom Modes | 4 |
| Quality Gate hooks | 2 |
| Hackathon docs | 5+ |
| Agent pipeline | **7 agents** |
| New agents added this hackathon | 2 (Agent 0: Upgrade Scout, Agent 6: Locator Healer) |
| Schema baselines saved | 5 OSLC object structures |
| Workflows | 8 |
| Test cases covered | 78 |
| Final verified run (pr_to_po) | 18/18 passed |
| Final verified run (api_only) | 58/58 passed |
| Max manual hours automated | 29.5h |
