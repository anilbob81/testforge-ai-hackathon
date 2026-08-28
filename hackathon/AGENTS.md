# TestForge AI — Agent Descriptions
### AGENTS.md — Project Context for IBM Bob 2.0
*Generated via Bob /init pattern — provides persistent context across conversations and modes.*

---

## Project: Maximo Autonomous Test Engineer

**One-liner**: Seven AI agents that transform a plain-English testing requirement into
a fully automated regression run, failure classification, autonomous locator healing,
and email report — all against a live IBM Maximo Application Suite instance.

**Repository**: `maximo-ai-agent/`
**Existing test suite**: `maximo-regression-tests/` (read-only — never modify)
**Entry point**: `python orchestrator.py --workflow <name>`

---

## The 7-Agent Pipeline

```
Human input: "MAS upgraded — validate P2P"
     ↓
Agent 0 — Upgrade Scout         (IBM Docs + Live Schema Diff + Domain Diff)
     ↓
Agent 1 — Requirement Analyser  (Document Understanding)
     ↓
Agent 2 — Test Strategist       (Subagent / Parallel planning)
     ↓                              ↓
Agent 3 — API Test Runner       Agent 4 — UI Test Runner
(pytest + Maximo REST)          (Selenium + Chrome)
     ↓                              ↓
     └──────────────┬───────────────┘
                    ↓
Agent 5 — Failure Analyst       (MCP pattern + AI classification)
                    ↓
Agent 6 — Locator Healer        (Autonomous re-test agent)
                    ↓
Reporter — HTML Report + Email  (Agent Mode)
```

---

## Agent Descriptions

### Agent 0 — Upgrade Scout
**File**: [`agents/agent_00_upgrade_scout.py`](../agents/agent_00_upgrade_scout.py)
**Bob 2.0 Feature**: MCP Pattern + Document Understanding
**Responsibility**:
- **Source 1**: Scrapes IBM Docs "What's New in Maximo 9.2" for real change items
- **Source 2**: Queries live Maximo OSLC API to diff schemas against saved baselines
- **Source 3**: Diffs status domain values (WOSTATUS, PRSTATUS, POSTATUS)
- Identifies impacted workflows from live intelligence — not hardcoded assumptions
- Saves `reports/upgrade_scout_report.json` for Agent 1 to consume

**Input**: IBM Docs URL + live Maximo OSLC API
**Output**: Scout report — `{ibm_docs_changes, schema_diffs, domain_diffs, impacted_workflows}`

**Bob Skill**: `regression-impact`

**Standalone run**:
```bash
python orchestrator.py --scout
```

---

### Agent 1 — Requirement Analyser
**File**: [`agents/agent_01_analyser.py`](../agents/agent_01_analyser.py)
**Bob 2.0 Feature**: Document Understanding
**Responsibility**:
- Reads `MAXIMO_TEST_AUTOMATION_FRAMEWORK.md` (67-page framework doc)
- Reads `workflow_map.json` to resolve the requested workflow
- Consumes Agent 0 scout report to enrich analysis with live change data
- Returns structured analysis: test files, business context, priority

**Input**: Workflow name (string) + workflow_map.json + scout_report
**Output**: Analysis dict — `{workflow_name, api_test_files, ui_test_files, priority, manual_hours_equivalent, doc_context_excerpt}`

**Bob Skill**: `requirement-analyser`

---

### Agent 2 — Test Strategist
**File**: [`agents/agent_02_strategist.py`](../agents/agent_02_strategist.py)
**Bob 2.0 Feature**: Subagent pattern (parallel planning)
**Responsibility**:
- Receives analysis from Agent 1
- Decides execution strategy: API only / UI only / API + UI
- Considers priority, time budget, risk level
- Produces execution plan consumed by Agents 3 and 4

**Strategy Rules**:
- `CRITICAL` priority → API + UI (full stack validation)
- `HIGH` priority → API + UI if UI tests exist, else API only
- `MEDIUM` priority → API only (faster feedback)
- `api_only` workflow → always API only

**Input**: Analysis dict from Agent 1
**Output**: Plan dict — `{strategy, run_api, run_ui, api_test_files, ui_test_files, estimated_seconds}`

**Bob Skill**: `test-planner`

---

### Agent 3 — API Test Runner
**File**: [`agents/agent_03_api_runner.py`](../agents/agent_03_api_runner.py)
**Bob 2.0 Feature**: Agent Mode (test execution)
**Responsibility**:
- Receives the execution plan from Agent 2
- Runs pytest with `--json-report` to capture structured results
- Executes against live Maximo REST API
- Collects pass/fail per test, duration, tracebacks

**Coverage** (when `api_only` workflow):
- 10 API test modules
- ~58 individual test cases
- ~20 seconds total runtime

**Input**: Plan dict from Agent 2
**Output**: API results dict — `{total, passed, failed, tests[], duration, skipped}`

---

### Agent 4 — UI Test Runner
**File**: [`agents/agent_04_ui_runner.py`](../agents/agent_04_ui_runner.py)
**Bob 2.0 Feature**: Agent Mode (browser automation)
**Responsibility**:
- Receives the execution plan from Agent 2
- Launches Chrome via ChromeDriver (Selenium WebDriver)
- Runs pytest with Selenium UI tests against live Maximo web interface
- Captures screenshots on failure, logs browser errors
- Collects pass/fail per test, duration, screenshots

**P2P Coverage** (when `pr_to_po` workflow):
- 1 UI test module: `test_10_ui_procurement_lifecycle.py`
- ~8 UI test cases: PR create → PR approve → PO → Receipt → Invoice
- ~9 minutes total runtime

**Input**: Plan dict from Agent 2
**Output**: UI results dict — `{total, passed, failed, tests[], duration, skipped}`

---

### Agent 5 — Failure Analyst
**File**: [`agents/agent_05_failure_analyst.py`](../agents/agent_05_failure_analyst.py)
**Bob 2.0 Feature**: MCP pattern + Document Understanding
**Responsibility**:
- Receives results from Agents 3 and 4
- For EVERY failed test: reads the traceback and classifies root cause
- Optionally queries live Maximo via REST API (MCP pattern) to verify system state
- Returns structured failure report: category + explanation + suggested fix

**Failure Categories**:
| Category | Icon | Meaning |
|----------|------|---------|
| APPLICATION_DEFECT | RED | Maximo regression / business rule changed |
| LOCATOR_DRIFT | YELLOW | Selenium element ID changed after upgrade |
| TIMING_ENVIRONMENT | ORANGE | Race condition / server slowness |
| ENVIRONMENT_AUTH | BLUE | API key expired / network issue |
| TEST_DATA | PURPLE | Reference data missing / inactive |
| UNKNOWN | GREY | Manual investigation needed |

**Input**: API results dict + UI results dict
**Output**: Failure analysis dict — `{failures[], category_summary, total_failures}`

**Bob Skill**: `failure-investigator`

---

### Agent 6 — Locator Healer
**File**: [`agents/agent_06_locator_healer.py`](../agents/agent_06_locator_healer.py)
**Bob 2.0 Feature**: Autonomous Re-test Agent
**Responsibility**:
- Only activates when Agent 5 classifies one or more `LOCATOR_DRIFT` failures
- For each LOCATOR_DRIFT failure: probes the Maximo DOM for candidate elements
- Uses fuzzy matching to find the best replacement locator
- Patches the test file (creates `.bak` backup first)
- Re-runs the patched test to verify the fix
- Reports: healed count, proposed (needs review) count, needs_human count
- Reverts patch if re-run still fails

**Heal outcomes**:
| Outcome | Meaning |
|---------|---------|
| `HEALED` | Patched + re-ran + passed — fully autonomous fix |
| `PROPOSED` | Patch generated but confidence below threshold — needs review |
| `NEEDS_HUMAN` | Cannot find replacement — escalate to test engineer |

**Input**: Failure analysis from Agent 5 (LOCATOR_DRIFT items only)
**Output**: Heal analysis dict — `{healed, proposed, needs_human, results[]}`

---

### Reporter
**File**: [`reporter/report_builder.py`](../reporter/report_builder.py)
**Bob 2.0 Feature**: Agent Mode (report generation + email)
**Responsibility**:
- Combines results from all 7 agents into a final HTML email report
- Shows: test counts, pass/fail, per-failure root cause + fix, hours saved
- Includes Upgrade Scout banner (Agent 0 intelligence summary)
- Includes Locator Healer summary (Agent 6 heal outcomes)
- Saves HTML to `reports/` folder
- Sends via SMTP to configured recipients

**Report includes**:
- Status header (ALL PASSED green / FAILURES DETECTED red)
- Score cards (total, passed, failed, pass rate, hours saved)
- Upgrade Scout intelligence banner (MAS 9.2 change signals)
- Pass rate progress bar
- Agent pipeline banner (7 agents)
- Per-failure analysis cards (category + root cause + fix + traceback snippet)
- Locator Healer summary (auto-healed / proposed / needs human)
- Full test results tables (API and UI)

---

## Bob 2.0 Features Demonstrated

| Feature | Agent / Location |
|---------|-----------------|
| **Agent Mode** | Orchestrator — runs all agents, pytest, email |
| **Subagents** | Agent 0 + 1 in isolated context; Agent 2 parallel planning |
| **Document Understanding** | Agent 0 IBM Docs; Agent 1 reads 67-page framework doc |
| **MCP Pattern** | Agent 0 schema/domain diff; Agent 5 failure context queries |
| **Parallel Tasks** | Agents 3 + 4 designed for concurrent execution |
| **Autonomous Re-test** | Agent 6 heals LOCATOR_DRIFT failures, re-runs, reports |
| **Skills** | 5 custom skills in `.bob/skills/` |
| **Custom Modes** | 4 specialist modes in `.bob/custom_modes.yaml` |
| **Rules/Guides** | `.bob/rules.md` steers Bob before every action |
| **Quality Gates** | `.bob/hooks/` provides machine-runnable sensors |
| **PR Generation** | Bob generates commit messages + PR descriptions |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `orchestrator.py` | Single entry point for the whole pipeline |
| `workflow_map.json` | Maps workflow names to test files |
| `config/agent_config.py` | All environment configuration |
| `baselines/` | Live schema snapshots for Agent 0 diff |
| `.bob/custom_modes.yaml` | 4 Bob specialist modes |
| `.bob/rules.md` | Quality gates + project constraints |
| `.bob/hooks/pre-commit.py` | Run before every commit |
| `hackathon/PLAN.md` | Living plan — tracks all 4 phases |

---

## Constraints (Read These First)

1. **NEVER modify `maximo-regression-tests/`** — the existing test suite is untouched
2. **Agents are Python classes** — they can be run standalone or via orchestrator
3. **Config is in `agent_config.py`** — update Maximo URL and API key there
4. **Reports go to `reports/`** — do not commit HTML report files to Git
5. **Quality gates are in `.bob/hooks/`** — run `pre-commit.py` before every commit
6. **Agent 6 only activates on LOCATOR_DRIFT** — it will not run if all tests pass

---

*Made with IBM Bob 2.0 · IBM TechXchange 2026 Dev Day Hackathon*
