# TestForge AI -- Living Plan
### Explore -> Plan -> Implement -> Verify
*IBM TechXchange 2026 Dev Day Hackathon -- IBM Bob 2.0*

> This is a living document. Updated as each phase progresses.
> It is the evidence trail that the work was structured and intentional.

---

## Current Status: VERIFY (Session 3)

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| Explore | DONE | Session 1 | Read all 5 agents, config, orchestrator, existing reports |
| Plan | DONE | Session 1 | Full design: agents, skills, modes, quality gates |
| Implement (Bob layer) | DONE | Session 2 | Skills, modes, rules, hooks, hackathon docs |
| Implement (Agent 0+6) | DONE | Session 3 | Upgrade Scout + Locator Healer added |
| Verify | IN PROGRESS | Session 3 | Quality gates running, baselines saving |

---

## Phase 1 — EXPLORE ✅

**Goal**: Understand the full existing codebase before building anything new.

**What was read**:
- `orchestrator.py` — the 5-agent pipeline entry point
- `agents/agent_01_analyser.py` — Document Understanding pattern
- `agents/agent_02_strategist.py` — Subagent + parallel planning pattern
- `agents/agent_03_api_runner.py` — pytest API execution
- `agents/agent_04_ui_runner.py` — Selenium UI execution
- `agents/agent_05_failure_analyst.py` — failure classification patterns
- `reporter/report_builder.py` — HTML report + email
- `config/agent_config.py` — Maximo connection + email config
- `workflow_map.json` — 8 workflows, 78 total tests
- `README.md` — existing project documentation
- `IBM-TXC-2026-Pre-conference-Dev-Day-hackathon-guide.pdf` — hackathon requirements

**Key findings**:
1. 5-agent pipeline is fully working — runs against live Maximo
2. Project already covers Agent mode, Subagents, Document Understanding, MCP pattern
3. Missing: Bob Skills, Modes, Rules, Quality Gates, Hackathon docs, Git workflow
4. Existing test suite in `maximo-regression-tests/` must never be modified

---

## Phase 2 — PLAN ✅

**Goal**: Design the complete Bob layer that elevates this from "working code" to "IBM Bob 2.0 showcase".

**Design decisions made**:

### Bob Skills (5 created)
| Skill | Why Needed |
|-------|-----------|
| `requirement-analyser` | Teaches Bob how to read a change and identify impacted tests |
| `test-planner` | Teaches Bob API vs UI decision logic |
| `failure-investigator` | Teaches Bob the 5-category classification system |
| `regression-impact` | Teaches Bob to map MAS versions to test scope |
| `test-data-validator` | Teaches Bob to verify Maximo data before running tests |

### Bob Modes (4 created)
| Mode | Why Needed |
|------|-----------|
| `test-architect` | Right persona for planning regression coverage |
| `failure-investigator` | Right persona for root cause analysis |
| `regression-analyst` | Right persona for MAS upgrade impact mapping |
| `report-writer` | Right persona for generating submission docs |

### Quality Gates (2 created)
| Gate | Purpose |
|------|---------|
| `pre-commit.py` | Blocks commits with broken agents, config issues, or protected file changes |
| `schema-verify.py` | Verifies Maximo connectivity before test runs |

### Hackathon Docs (5 created)
- `ONBOARDING.md` — team onboarding reference
- `AGENTS.md` — Bob /init style project context
- `PLAN.md` — this file (living plan)
- `github-issue-P2P-001.md` — the demo scenario as a real-format issue
- `demo-script.md` — 8-minute hackathon demo walkthrough

**Decision: killer demo scenario**
> "MAS has been upgraded to 9.2. Validate that P2P still works."
>
> Why: complex multi-step workflow, real customer pain, uses both API and UI,
> failure classification is compelling (storeroom = TEST_DATA, not code defect).

---

## Phase 3 — IMPLEMENT ✅

**Goal**: Create all Bob layer files. Zero changes to existing agents or test suite.

**Files created in this phase**:
```
.bob/
├── custom_modes.yaml                              ← 4 custom modes
├── rules.md                                       ← Quality gates + project rules
├── skills/
│   ├── requirement-analyser/SKILL.md + impact-matrix.md
│   ├── test-planner/SKILL.md + test-selection-guide.md
│   ├── failure-investigator/SKILL.md + classification-rules.md
│   ├── regression-impact/SKILL.md + mas-change-catalog.md
│   └── test-data-validator/SKILL.md + data-requirements.md
└── hooks/
    ├── pre-commit.py
    └── schema-verify.py

hackathon/
├── ONBOARDING.md
├── AGENTS.md
├── PLAN.md (this file)
├── github-issue-P2P-001.md
└── demo-script.md

bob_sessions/               ← Ready for screenshots
```

**Files NOT modified** (protected):
- `maximo-regression-tests/` — zero changes
- `agents/` — zero changes
- `config/` — zero changes
- `orchestrator.py` — zero changes

---

## Phase 4 — VERIFY 🔄

**Goal**: Confirm the pipeline and Bob layer are working correctly.

**Verification steps**:

- [ ] Run `python .bob/hooks/pre-commit.py` — all gates pass (exit 0)
- [ ] Run `python .bob/hooks/schema-verify.py` — Maximo reachable (exit 0)
- [ ] Run `python orchestrator.py --workflow api_only --no-email` — all API tests pass
- [ ] Run `python orchestrator.py --workflow pr_to_po` — P2P tests + email delivered
- [ ] Verify email received at `anil.dontaraju@nexergroup.com`
- [ ] Open Bob IDE in `test-architect` mode — activate `requirement-analyser` skill
- [ ] Read `hackathon/github-issue-P2P-001.md` in Bob and confirm impact analysis
- [ ] Run Bob's commit message generator — commit with `[TestForge] feat:` prefix
- [ ] Generate PR description with Bob — push to `feature/testforge-ai-hackathon`
- [ ] Take screenshots of all major Bob tasks → save to `bob_sessions/`

---

## Key Architectural Decisions

### Why is the existing pipeline untouched?
The agents in `agents/` are mature, tested, and running against live Maximo.
The Bob layer (skills, modes, rules) wraps around them — guiding how Bob interacts
with the pipeline, not changing the pipeline itself. This is the right separation.

### Why 5 skills not 1?
Each skill serves a different phase of the Explore→Plan→Implement→Verify loop.
They can be composed — e.g. `regression-analyst` mode uses both `regression-impact`
and `requirement-analyser` skills in sequence.

### Why quality gates in Python not shell scripts?
Cross-platform (Windows/Mac/Linux). Runs the same way on all team member machines.
Can use the same Python environment as the agents. Exit codes are explicit.

### How does this align with the hackathon Guides vs Sensors concept?
- **Guides (before Bob acts)**: `.bob/rules.md` + skills + modes
- **Sensors (after Bob acts)**: `pre-commit.py` + `schema-verify.py` + email report
- The constant improvement loop: results feed back into plan updates (this document)

---

## Metrics Tracked

| Metric | Value |
|--------|-------|
| Bob Skills created | 5 |
| Bob Modes created | 4 |
| Quality gates created | 2 |
| Hackathon docs created | 5+ |
| Existing agents modified | 0 |
| Existing test files touched | 0 |
| Max test automation hours saved | 29.5h (full_regression) |
| Fastest workflow | api_only (~20 seconds) |

---

*Made with IBM Bob 2.0 · Last updated: IBM TechXchange 2026 Dev Day Hackathon*
