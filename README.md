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
├── bob_sessions/                   ← ⭐ REQUIRED: Bob task session screenshots
│   ├── How all agents are connected.png
│   ├── Test Strategist.png
│   └── Failure Analyst agent.png
├── orchestrator.py                 ← Pipeline entry point (7 agents)
├── workflow_map.json               ← Workflow → test file mappings
├── demo_locator_heal.py            ← Standalone Agent 6 demo (algorithm proof)
├── demo_score_analysis.py          ← Locator scoring benchmark (4 upgrade patterns)
├── demo_inspect_dom.py             ← Live DOM diagnostic tool
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

## Time & Effort Savings

### The Business Reality Before TestForge AI

Every IBM Maximo upgrade — and they happen every few weeks — forces a choice:
either spend days manually re-validating that critical business processes still work,
or ship the upgrade and hope nothing is broken. Neither is acceptable.
TestForge AI eliminates that choice entirely.

---

### Savings by Customer Scale

#### 🏢 Small Businesses & Single-Site Deployments
*Examples: a single manufacturing plant, a facilities management company, a mid-market utility*

| | Manual (Before) | TestForge AI (After) | Saving |
|---|---|---|---|
| **Workflows to validate** | 3–5 (WO, P2P, Assets) | Same | — |
| **Upgrade validation time** | **2–3 days** per upgrade | **~15 minutes** | **95% reduction** |
| **Consultant hours per upgrade** | 16–24 hours | 0 hours | **100% automated** |
| **Time-to-detect a regression** | Days after go-live | Within 15 minutes | **Immediate** |
| **Annual saving** (13 upgrades/year) | 208–312 consultant-hours | ~3.25 hours | **~300 hours/year** |
| **Who investigates failures** | Senior Maximo consultant | Any team member | **Skill democratised** |

> *"What used to require a senior consultant flying in for 2 days now runs unattended
> while the team sleeps."*

---

#### 🏭 Mid-Size Enterprises & Multi-Site Operations
*Examples: a regional utility with 5–10 sites, a healthcare network, a transport authority*

These customers run multiple sites, multiple workflows, and typically have change
management gates that require **signed-off test evidence** before an upgrade goes live.

| | Manual (Before) | TestForge AI (After) | Saving |
|---|---|---|---|
| **Workflows to validate** | 8–15 across sites | Same | — |
| **Upgrade validation time** | **1–3 weeks** per upgrade | **~1–2 hours** (parallel) | **97% reduction** |
| **Test evidence preparation** | Days of manual screenshots | Auto-generated HTML report | **Instant** |
| **Failure root cause** | 1–2 days triage per failure | Instant AI classification | **100% automated** |
| **Regression scope selection** | Senior architect decides | AI selects from change log | **Intelligent targeting** |
| **Annual saving** (13 upgrades/year) | 5–10 weeks of consultant time | ~26 hours total | **~2,000 hours/year** |

> *"A mid-size enterprise running full regression across 5 sites was spending 3 weeks
> per upgrade cycle. TestForge AI reduces that to an overnight automated run with
> a results email waiting in the morning."*

---

#### 🏗️ Large Asset-Intensive Industries
*Examples: oil & gas, mining, defence, national infrastructure — organisations with thousands of assets, complex PM schedules, and regulatory compliance requirements*

These organisations face the hardest version of this problem. An upgrade isn't just
a technical event — it's a compliance event. Every workflow that touches a regulated
asset must be validated and documented before the upgrade can be signed off.
Manual testing at this scale is measured in **months**.

| | Manual (Before) | TestForge AI (After) | Saving |
|---|---|---|---|
| **Workflows to validate** | 20–50+ across modules | Same | — |
| **Upgrade validation cycle** | **2–6 months** | **Hours to days** | **98% reduction** |
| **Test team size** | 5–15 dedicated testers | 1 engineer monitors pipeline | **10–15x headcount saving** |
| **Compliance evidence** | Manually assembled binders | Auto-generated, timestamped HTML reports | **Instant audit trail** |
| **Regression introduced by upgrade** | Found in production weeks later | Caught within 15 minutes of upgrade | **Pre-production detection** |
| **Annual saving** (4–8 upgrades/year) | 4–24 months of test team effort | Days | **Months of effort per year** |

> *"For an oil & gas operator with 50,000 assets across 20 sites, manual post-upgrade
> validation takes a dedicated test team 3–4 months per major upgrade cycle.
> TestForge AI compresses that to a pipeline run. The compliance evidence is
> auto-generated. The upgrade ships months earlier."*

---

### Per-Workflow Savings (This Implementation)

| Workflow | Manual Hours | Automated Time | Saves Per Run |
|----------|-------------|----------------|---------------|
| `api_only` — 58 API tests | 14.5h | ~20 sec | **14.5h** |
| `pr_to_po` — P2P lifecycle | 6.0h | ~9 min | **5.85h** |
| `work_order` — WO lifecycle | 3.0h | ~6 min | **2.9h** |
| `pm_maintenance` — PM + WO gen | 4.0h | ~10 min | **3.83h** |
| `full_regression` — 78 tests | 29.5h | ~15 min | **29.25h** |

**For a small customer running full regression on every upgrade (13/year):**
29.5h × 13 = **~383 consultant-hours saved per year, per environment.**

**For a large enterprise running full regression across 10 environments:**
383h × 10 = **~3,830 consultant-hours saved per year.**

---

### Traditional Test Automation Projects vs TestForge AI

Building and maintaining a test automation suite at this scale traditionally requires:

| Phase | Traditional Approach | TestForge AI |
|-------|---------------------|-------------|
| **Initial build** | 6–18 months, dedicated test automation team | Already built — deploy in hours |
| **Framework setup** | 2–3 months (tools, CI/CD, reporting) | Zero — pipeline is the framework |
| **Onboarding new team members** | Weeks of training | Bob Skills loaded automatically |
| **Maintaining after each upgrade** | 2–4 weeks (broken locators, changed APIs) | Agent 6 auto-heals locators; Agent 0 detects API changes |
| **Failure investigation** | Senior engineer, 1–2 days per failure | Agent 5 classifies instantly, fix suggested |
| **Scaling to new workflows** | Months of new test development | Add entry to `workflow_map.json` |
| **Scaling to new environments** | Rebuild/reconfigure everything | Change 4 lines in `agent_config.py` |
| **Knowledge transfer** | High risk — expertise locked in individuals | Bob Skills encode the knowledge permanently |

> *"Traditional test automation projects often cost more to maintain than the value they
> deliver — and they break silently when the application upgrades. TestForge AI inverts
> this: upgrades are the trigger that makes the system more valuable, not less."*

---

## Reusability — Adapting to Other Projects

TestForge AI is not Maximo-specific. Every layer is parameterised and replaceable.

### Adapting to a different Maximo environment
Only one file needs changing: [`config/agent_config.py`](config/agent_config.py)
```python
MAXIMO_BASE_URL = "https://your-instance.manage.apps.yourcluster.com/maximo"
API_KEY         = "your-api-key"
SITE_ID         = "YOURSITE"
ORGANIZATION    = "YOURORG"
```

### Adapting to a different application entirely
The 7-agent pattern is reusable for any application with:
- A REST API that returns JSON (replace OSLC queries in Agent 0 + 5)
- A web UI with stable/inspectable element IDs (Selenium in Agents 4 + 6)
- Pytest-based test suites (Agents 3 + 4 are generic pytest runners)

| Layer | What to replace | Effort |
|-------|----------------|--------|
| Agent 0 baseline schemas | Your API endpoints + field names | Low |
| Agent 0 IBM Docs scraper | Your product's release notes URL | Low |
| `workflow_map.json` | Your workflow → test file mapping | Low |
| Agent 6 `MAXIMO_PAGE_MAP` | Your app's page/route names | Low |
| Bob Skills | Rewrite SKILL.md files with your domain knowledge | Medium |
| Test suite itself | New pytest files for your app | High (already exists) |

### The Bob skills survive the hackathon
The 5 skills in `.bob/skills/` are persistent team assets. Any team member using
IBM Bob IDE on this project automatically gets the full Maximo testing intelligence —
impact analysis, test planning, failure classification, regression scoping —
without needing to be a Maximo expert.

---

## Known Limitations & Roadmap

### Current limitations (honest assessment)

| Limitation | Impact | Proposed Fix |
|-----------|--------|-------------|
| Agent 6 auto-heals only ~20% of locator failures | Hashed IDs (`mad3161b5-tb`) score LOW — can't auto-apply | **Locator Registry**: run probes periodically, store old→new ID mappings in `baselines/locator_registry.json` |
| New API fields detected but not tested | Agent 0 flags new fields; no test is auto-generated for them | **Test Generator agent** (Agent 2.5): Granite writes a pytest assertion for each new field |
| `probe_page_dom()` 5s wait too short for React SPA | Agent 6 browser probe lands on login page, not app | Replace `time.sleep(5)` with `WebDriverWait` for sentinel element (`quicksearch`) |
| IBM Docs scraper falls back to offline catalog | IBM Docs page sometimes blocks scraping → uses hardcoded MAS 9.2 changes | Use IBM RSS feed or official changelog API if available |
| Domain diff returns empty | MXDOMAIN query returns no members on this instance | Investigate MXDOMAIN endpoint permissions |

### Roadmap (next improvements, in priority order)

1. **Locator Registry** (highest impact)
   - Schedule `probes/probe_all_pages.py` nightly
   - Write element IDs to `baselines/locator_registry.json`
   - Agent 6 looks up registry first → 100% confidence for all patterns
   - Estimated effort: 1 day

2. **Test Generator agent** (closes the new-field gap)
   - New Agent 2.5 between Strategist and API Runner
   - Reads `scout_report.schema_diffs[].new_fields`
   - Calls Granite to write a pytest assertion per new field
   - Appends generated test to `api_test_files` before Agent 3 runs
   - Estimated effort: 2 days

3. **Sentinel-aware DOM probe** (fixes Agent 6 browser path)
   - Replace `time.sleep(5)` with `WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "quicksearch")))`
   - Makes full browser-based HEALED path work reliably
   - Estimated effort: 30 minutes

4. **Granite-enhanced locator matching** (improves MEDIUM→HIGH rate)
   - Pass broken locator + live DOM elements to Granite
   - "The old field had aria='Work Order'. Which of these DOM elements is the Work Order number input?"
   - Would handle complete renames (Case D) which currently score LOW
   - Estimated effort: 1 day

---

## Demo Scripts

Two standalone scripts for demonstrating Agent 6 capability without running the full pipeline:

```bash
# Proves the patch_test_file() + find_best_match() algorithm end-to-end
python demo_locator_heal.py

# Benchmarks all 4 real Maximo upgrade ID-change patterns with actual scores
python demo_score_analysis.py
```

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
| Agent 6 auto-heal rate | ~20% fully autonomous; ~80% PROPOSED/NEEDS_HUMAN |
| Demo scripts | 3 (`demo_locator_heal`, `demo_score_analysis`, `demo_inspect_dom`) |
