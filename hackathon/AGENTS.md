# TestForge AI — Agent Descriptions
### AGENTS.md — Project Context for IBM Bob 2.0
*Generated via Bob /init pattern — provides persistent context across conversations and modes.*

---

## Project: Maximo Autonomous Test Engineer

**One-liner**: Five AI agents that transform a plain-English testing requirement into
a fully automated regression run, failure classification, and email report — all
against a live IBM Maximo Application Suite instance.

**Repository**: `maximo-ai-agent/`
**Existing test suite**: `maximo-regression-tests/` (read-only — never modify)
**Entry point**: `python orchestrator.py --workflow <name>`

---

## The Agent Pipeline

```
Human input: "MAS upgraded — validate P2P"
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
Reporter — HTML Report + Email  (Agent Mode)
```

---

## Agent Descriptions

### Agent 1 — Requirement Analyser
**File**: [`agents/agent_01_analyser.py`](../agents/agent_01_analyser.py)
**Bob 2.0 Feature**: Document Understanding
**Responsibility**:
- Reads `MAXIMO_TEST_AUTOMATION_FRAMEWORK.md` (67-page framework doc)
- Reads `workflow_map.json` to resolve the requested workflow
- Extracts relevant sections for the requested workflow/scenario
- Returns structured analysis: test files, business context, priority

**Input**: Workflow name (string) + workflow_map.json
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
| APPLICATION_DEFECT | 🔴 | Maximo regression / business rule changed |
| LOCATOR_DRIFT | 🟡 | Selenium element ID changed after upgrade |
| TIMING_ENVIRONMENT | 🟠 | Race condition / server slowness |
| ENVIRONMENT_AUTH | 🔵 | API key expired / network issue |
| TEST_DATA | 🟣 | Reference data missing / inactive |
| UNKNOWN | ⚪ | Manual investigation needed |

**Input**: API results dict + UI results dict
**Output**: Failure analysis dict — `{failures[], category_summary, total_failures}`

**Bob Skill**: `failure-investigator`

---

### Reporter
**File**: [`reporter/report_builder.py`](../reporter/report_builder.py)
**Bob 2.0 Feature**: Agent Mode (report generation + email)
**Responsibility**:
- Combines results from all 5 agents into a final HTML email report
- Shows: test counts, pass/fail, per-failure root cause + fix, hours saved
- Saves HTML to `reports/` folder
- Sends via SMTP to configured recipients

**Report includes**:
- Status header (ALL PASSED green / FAILURES DETECTED red)
- Score cards (total, passed, failed, pass rate, hours saved)
- Pass rate progress bar
- Agent pipeline banner
- Per-failure analysis cards (category + root cause + fix + traceback snippet)
- Full test results tables (API and UI)

---

## Bob 2.0 Features Demonstrated

| Feature | Agent / Location |
|---------|-----------------|
| **Agent Mode** | Orchestrator — runs all agents, pytest, email |
| **Subagents** | Agent 1 reads docs in isolated context; Agent 2 plans separately |
| **Document Understanding** | Agent 1 reads 67-page MAXIMO_TEST_AUTOMATION_FRAMEWORK.md |
| **MCP Pattern** | Agent 5 queries live Maximo REST to verify record state |
| **Parallel Tasks** | Agents 3 + 4 designed for concurrent execution |
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

---

*Made with IBM Bob 2.0 · IBM TechXchange 2026 Dev Day Hackathon*
