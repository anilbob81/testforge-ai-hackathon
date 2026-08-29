# TestForge AI — Developer Onboarding
### IBM TechXchange 2026 Dev Day Hackathon | IBM Bob 2.0

---

## What This Project Does

**One sentence**: Type a plain-English testing requirement → 7 AI agents execute it autonomously → failures classified with root cause → locators auto-healed → email report delivered.

```bash
python orchestrator.py --workflow pr_to_po
```

```
[Agent 0] IBM Docs scrape: 5 MAS 9.2 changes detected...
[Agent 0] Schema diff: MXWO/MXASSET/MXAPISR unchanged
[Agent 1] Reading MAXIMO_TEST_AUTOMATION_FRAMEWORK.md...
[Agent 1] Workflow 'pr_to_po' → test_06_pr, test_07_po, test_10_ui_procurement
[Agent 2] Strategy: API + UI (CRITICAL — full stack validation)
[Agent 3] Running API tests... 10/10 passed
[Agent 4] Chrome opens — Selenium drives PR→PO→Receipt→Invoice
[Agent 5] Classifying failures... 0 failures — all clean
[Agent 6] Locator Healer — no LOCATOR_DRIFT failures, skipping
[Reporter] Email sent → anil.dontaraju@nexergroup.com
PIPELINE COMPLETE — 18/18 passed | 6h manual effort saved | 95% time reduction
```

---

## The Problem Being Solved

IBM Maximo customers receive upgrades every few weeks. Each upgrade requires
validating that critical business processes still work. Before this project:

| | Before | After |
|---|---|---|
| **Time per upgrade validation** | 2–3 days manual testing | ~15 minutes automated |
| **Consultant hours** | 16–24 hours | 0 hours (AI handles it) |
| **Time-to-detect failure** | Days later | Within 15 minutes |
| **Root cause analysis** | Hours of log investigation | Instant AI classification |
| **Who investigates failures** | Senior engineer | Any team member |

---

## 5-Minute Setup

### Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.11+ | `python --version` |
| Chrome | Latest stable | `google-chrome --version` |
| IBM Bob IDE | 2.0.2+ | Settings → About |
| Git | Any | `git --version` |

### Installation

```bash
# 1. Clone
git clone <your-repo-url>
cd maximo-ai-agent

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the quality gate (verifies project integrity)
python .bob/hooks/pre-commit.py

# 4. Verify Maximo connectivity
python .bob/hooks/schema-verify.py

# 5. Run the fastest workflow (20 seconds — no email)
python orchestrator.py --workflow api_only --no-email

# 6. List all available workflows
python orchestrator.py --list
```

---

## Project Structure — What Lives Where

```
maximo-ai-agent/
├── .bob/                        ← IBM Bob 2.0 configuration layer
│   ├── custom_modes.yaml        ← 4 specialist AI modes
│   ├── rules.md                 ← Project rules + quality gates
│   ├── skills/                  ← 5 reusable Bob skills
│   │   ├── requirement-analyser/
│   │   ├── test-planner/
│   │   ├── failure-investigator/
│   │   ├── regression-impact/
│   │   └── test-data-validator/
│   └── hooks/
│       ├── pre-commit.py        ← Quality gate (run before commit)
│       └── schema-verify.py     ← Maximo connectivity probe
├── agents/                      ← The 7 AI agents
│   ├── agent_00_upgrade_scout.py   ← IBM Docs + Live Schema Diff (MCP)
│   ├── agent_01_analyser.py        ← Document Understanding + workflow mapping
│   ├── agent_02_strategist.py      ← API vs UI strategy planning
│   ├── agent_03_api_runner.py      ← pytest API test execution
│   ├── agent_04_ui_runner.py       ← Selenium UI test execution
│   ├── agent_05_failure_analyst.py ← Root cause classification
│   └── agent_06_locator_healer.py  ← Autonomous locator healing + re-test
├── baselines/                   ← Live schema snapshots (Agent 0 diff)
│   ├── mxwo_schema.json         ← 159-field baseline
│   ├── mxasset_schema.json      ← 61-field baseline
│   ├── mxapisr_schema.json      ← 84-field baseline
│   ├── mxapioperloc_schema.json ← 54-field baseline
│   └── mxinventory_schema.json  ← 44-field baseline
├── config/agent_config.py       ← Maximo + email configuration
├── reporter/report_builder.py   ← HTML report + email sender
├── hackathon/                   ← Submission documentation
│   ├── ONBOARDING.md            ← This file
│   ├── AGENTS.md                ← Agent descriptions
│   ├── PLAN.md                  ← Living plan (Explore→Plan→Implement→Verify)
│   ├── github-issue-P2P-001.md  ← Demo scenario GitHub issue (resolved)
│   └── demo-script.md           ← 8-minute demo walkthrough
├── bob_sessions/                ← Task session screenshots (submission)
│   ├── How all agents are connected.png
│   ├── Test Strategist.png
│   └── Failure Analyst agent.png
├── orchestrator.py              ← Entry point — runs all 7 agents
├── workflow_map.json            ← Maps workflow names to test modules
├── reports/                     ← Generated HTML reports (auto-created)
└── logs/                        ← Execution logs (auto-created)

maximo-regression-tests/         ← EXISTING SUITE — NEVER MODIFY
```

---

## The 4 Bob Modes

Switch modes in Bob IDE using the mode selector in the chat header.

| Mode | Slug | Use It When |
|------|------|-------------|
| 🏗️ Test Architect | `test-architect` | Planning tests for an upgrade/change |
| 🔍 Failure Investigator | `failure-investigator` | Analysing why a test failed |
| 📊 Regression Analyst | `regression-analyst` | Mapping MAS changes to test scope |
| 📝 Report Writer | `report-writer` | Generating release-readiness reports |

---

## The 5 Bob Skills

Bob activates these automatically based on context, or you can request them explicitly.

| Skill | Use It When |
|-------|-------------|
| `requirement-analyser` | Analysing a GitHub issue or upgrade description |
| `test-planner` | Deciding API vs UI coverage for a workflow |
| `failure-investigator` | Deep-diving into a specific test failure |
| `regression-impact` | Mapping MAS version changes to test scope |
| `test-data-validator` | Checking Maximo reference data before test run |

**Example**: In `test-architect` mode, say: *"Read the GitHub issue and identify which tests to run."*
Bob will activate `requirement-analyser` skill automatically.

---

## Available Workflows

| Workflow | Description | Tests | Est. Time | Manual Equiv. |
|----------|-------------|-------|-----------|---------------|
| `api_only` | All 58 API tests (fastest) | 58 API | ~20 sec | 14.5h |
| `pr_to_po` | P2P full lifecycle | 10 API + 8 UI | ~9 min | 6.0h |
| `work_order` | WO create → approve → complete | 5 API + 6 UI | ~6 min | 3.0h |
| `pm_maintenance` | PM + WO generation | 10 API + 6 UI | ~10 min | 4.0h |
| `asset_management` | Asset + Location hierarchy | 10 API | ~20 sec | 2.0h |
| `service_request` | SR lifecycle | 5 API | ~10 sec | 1.5h |
| `wo_from_jobplan` | WO from Job Plan | 10 API | ~15 sec | 2.5h |
| `full_regression` | All 78 tests (complete) | 58 API + 20 UI | ~15 min | 29.5h |

---

## The Killer Demo Scenario

**Trigger**: *"MAS has been upgraded to 9.2. Validate that P2P still works."*

**What the AI does — autonomously**:

1. Reads the GitHub issue or change description
2. Activates `regression-impact` skill — maps MAS 9.2 changes to P2P workflow
3. Identifies P2P as impacted (storeroom validation, PO approval, invoice matching)
4. Selects `pr_to_po` workflow (18 tests instead of 78 — AI regression selection)
5. Runs API tests in ~4 seconds
6. Runs Selenium UI tests in ~9 minutes
7. Classifies any failures (APPLICATION_DEFECT / LOCATOR_DRIFT / TEST_DATA / etc.)
8. Sends email report with root cause + exact fix suggestion
9. Creates a Git commit and PR description

**This is the full Explore → Plan → Implement → Verify loop — zero human steps.**

---

## Agent 0 — Upgrade Scout (New in Session 3)

Before any tests run, Agent 0 gathers **live** upgrade intelligence:

```bash
# Run Agent 0 standalone to save schema baselines
python orchestrator.py --scout

# Skip Agent 0 on subsequent runs (use cached data)
python orchestrator.py --workflow pr_to_po --no-scout
```

Agent 0 queries three sources:
1. **IBM Docs** — scrapes "What's New in Maximo 9.2" for real change items
2. **Live Schema Diff** — diffs 5 OSLC object structures against saved baselines
3. **Domain Diff** — compares status code domains (WOSTATUS, PRSTATUS, POSTATUS)

If a schema field is **removed**, Agent 0 flags it as `HIGH` impact and the relevant
workflow is automatically added to the regression scope.

---

## Quality Gates (Bob Sensors)

These must pass before every commit:

```bash
# Gate 1: Project integrity + agent syntax + config check
python .bob/hooks/pre-commit.py

# Gate 2: Maximo connectivity + schema availability
python .bob/hooks/schema-verify.py

# Gate 3: Fast pipeline smoke test
python orchestrator.py --workflow api_only --no-email
```

All three exit with code 0 = safe to commit and push.

---

## Git Workflow

```bash
# Branch
git checkout -b feature/testforge-ai-hackathon

# After changes — run gates
python .bob/hooks/pre-commit.py

# Stage changes
git add -A

# Let Bob generate the commit message (Bob IDE → commit message generator)
# Format: [TestForge] <type>: <description>

# Push
git push origin feature/testforge-ai-hackathon

# Create PR — use Bob IDE PR description generator
```

---

## Hackathon Submission Checklist

Before submitting:
- [x] `bob_sessions/` contains screenshots of all major Bob tasks
- [x] `hackathon/PLAN.md` shows all 4 phases (Explore/Plan/Implement/Verify) completed
- [x] All quality gates pass: `python .bob/hooks/pre-commit.py`
- [x] Pipeline runs end-to-end: `python orchestrator.py --workflow pr_to_po`
- [x] Email report received at `anil.dontaraju@nexergroup.com`
- [x] GitHub Issue #001 read, analysed, and resolved by the agent
- [x] README.md reflects all Bob 2.0 features used (7 agents)

---

## Configuration

All settings in [`config/agent_config.py`](../config/agent_config.py):

| Setting | Purpose |
|---------|---------|
| `MAXIMO_BASE_URL` | Maximo instance URL |
| `API_KEY` | Maximo REST API authentication key |
| `SITE_ID` | Target site (default: BEDFORD) |
| `ORGANIZATION` | Target org (default: EAGLENA) |
| `EMAIL_CONFIG` | SMTP settings for report delivery |

---

## Future Improvements

The following improvements are identified and scoped — ready for the next sprint:

### 1. Locator Registry (highest impact — 1 day effort)
**Problem**: Agent 6 auto-heals only ~20% of locator failures because Maximo uses random
hashes (`mad3161b5-tb`) that score LOW in fuzzy matching.

**Solution**: Run the existing `probes/` scripts nightly. Write all element IDs to
`baselines/locator_registry.json`. Agent 6 looks up the registry first — if the broken
ID was captured before, the replacement is known at 100% confidence.

```bash
# How it would work:
python probes/probe_all_pages.py          # saves baselines/locator_registry.json
python orchestrator.py --workflow work_order  # Agent 6 uses registry → all HEALED
```

### 2. Test Generator Agent (Agent 2.5)
**Problem**: Agent 0 detects new API fields but no test is auto-generated to verify them.

**Solution**: A new agent between Strategist and API Runner that reads
`scout_report.schema_diffs[].new_fields` and calls IBM Granite to write a pytest
assertion for each new field, injecting it into the test run automatically.

### 3. Sentinel-aware DOM Probe (30 min fix)
**Problem**: `probe_page_dom()` uses `time.sleep(5)` which may not be long enough
for the Maximo React SPA to load past the login page.

**Solution**:
```python
# In agent_06_locator_healer.py probe_page_dom():
# Replace: time.sleep(5)
# With:
WebDriverWait(self.driver, 30).until(
    EC.presence_of_element_located((By.ID, "quicksearch"))
)
```

### 4. Granite-enhanced locator matching
**Problem**: Completely renamed IDs (e.g. `approveWO_action_btn` replacing a hashed ID)
score LOW even though the semantic meaning is obvious from the aria label.

**Solution**: Pass the broken locator + top DOM candidates to Granite with the question:
*"The old element had aria='Approve Work Order'. Which of these is the same element?"*
This handles complete renames that fuzzy string matching cannot.

---

*Made with IBM Bob 2.0 · IBM TechXchange 2026 Dev Day Hackathon*
