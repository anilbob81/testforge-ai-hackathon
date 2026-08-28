# TestForge AI — Bob Project Rules
# IBM TechXchange 2026 Dev Day Hackathon
#
# These rules are loaded on every Bob interaction (Guides = Feedforward).
# They steer Bob BEFORE it acts — preventing mistakes before they happen.
# Quality gates in .bob/hooks/ are the Sensors — they verify AFTER Bob acts.

---

## 🔒 Core Protection Rule — NON-NEGOTIABLE

NEVER modify, rename, delete, or write any file inside the `maximo-regression-tests/` folder.
That folder is the existing production test suite owned by the team.
This project (`maximo-ai-agent/`) only READS from it — it never touches it.

If any request would require modifying a file in `maximo-regression-tests/`, STOP and tell
the user: "This change would modify the existing test suite. Please make that change manually
in the maximo-regression-tests/ project."

---

## 🔄 Explore → Plan → Implement → Verify Loop

Always follow this four-phase loop for any non-trivial task:

1. **EXPLORE** — Read the relevant code before writing anything new.
   - Read workflow_map.json and the affected agent files first.
   - Use Ask mode or Plan mode for exploration.
   - Never guess at existing code — always read it.

2. **PLAN** — Write the plan to `hackathon/PLAN.md` before implementing.
   - Update the status table in PLAN.md to show which phase you are in.
   - For new workflows, add an entry to workflow_map.json first.

3. **IMPLEMENT** — Make the minimal change that solves the problem.
   - No unasked-for refactors, cleanups, or added features.
   - Every changed line must trace directly to the stated requirement.
   - Use Agent mode for all file creation and modification.

4. **VERIFY** — Run quality gates before declaring done.
   - `python .bob/hooks/pre-commit.py` — must exit 0
   - `python .bob/hooks/schema-verify.py` — must exit 0
   - `python orchestrator.py --workflow api_only --no-email` for full pipeline check

---

## 🚦 Quality Gates (Machine-Runnable — Not Discovered Afterwards)

These gates MUST pass before any commit. Run them explicitly:

```bash
# Gate 1: Project integrity check
python .bob/hooks/pre-commit.py

# Gate 2: Maximo connectivity + schema check
python .bob/hooks/schema-verify.py

# Gate 3: Fast pipeline smoke test
python orchestrator.py --workflow api_only --no-email
```

All three must exit with code 0. If any gate fails, fix the issue before committing.

---

## 🤖 Agent Behaviour Rules

Every agent in `agents/` must follow these conventions:

- Print its identity on start: `[Agent N — Name]`
- Return a Python `dict` with `"success": bool` as the first key
- Failed agents must use graceful degradation — never crash the pipeline
- The Reporter must always generate a report, even if all tests fail
- Agent output dicts must be JSON-serialisable (no Path objects, no exceptions)

---

## 📝 Git Workflow

Branch naming:
- All hackathon work lives on: `feature/testforge-ai-hackathon`
- Hotfixes: `fix/description-of-fix`

Commit message format: `[TestForge] <type>: <description>`
- Types: `feat`, `fix`, `docs`, `skill`, `mode`, `config`, `report`, `gate`
- Example: `[TestForge] feat: add regression-impact skill`
- Use Bob's built-in commit message generator for consistency

PR workflow:
1. Push branch to origin
2. Use Bob IDE PR generation feature to write the PR description
3. PR description must include: what changed, Bob features used, quality gates passed
4. `bob_sessions/` folder must contain task session screenshots before merging

What NOT to commit:
- `reports/*.html` — auto-generated, add to .gitignore
- `logs/` contents — runtime logs, add to .gitignore
- `config/agent_config.py` API keys — use environment variables in production
- Any file from `maximo-regression-tests/`

---

## 📊 Report Rules

- Every pipeline run generates an HTML report saved to `reports/`
- Email is sent to configured recipients unless `--no-email` flag is used
- Report filename format: `agent_report_<workflow>_<YYYYMMDD_HHMMSS>.html`
- Every report must include: workflow, pass/fail counts, duration, hours saved
- Failure reports must include: category, explanation, fix suggestion, confidence

---

## 🎭 Mode Selection Guide

| Task | Use This Mode |
|------|--------------|
| Analysing a new upgrade/change | `regression-analyst` |
| Planning which tests to run | `test-architect` |
| Investigating a failure | `failure-investigator` |
| Writing reports or docs | `report-writer` |
| Writing/editing code | `agent` (default) |
| Asking questions about the codebase | `ask` (default) |
| Planning a complex feature | `plan` (default) |

---

## 📚 Skill Activation Guide

| Situation | Activate This Skill |
|-----------|-------------------|
| Analysing a requirement or GitHub issue | `requirement-analyser` |
| Planning test coverage for a workflow | `test-planner` |
| Investigating a test failure | `failure-investigator` |
| Mapping MAS version changes to tests | `regression-impact` |
| Verifying test data exists in Maximo | `test-data-validator` |

---

## 🏆 Hackathon Submission Checklist

Before final submission, verify:
- [ ] `bob_sessions/` contains screenshots of all major Bob tasks
- [ ] `hackathon/PLAN.md` shows all 4 phases completed
- [ ] `hackathon/ONBOARDING.md` is up to date
- [ ] All quality gates pass: `python .bob/hooks/pre-commit.py`
- [ ] Pipeline runs end-to-end: `python orchestrator.py --workflow pr_to_po --no-email`
- [ ] Email report received (or `--no-email` report saved to reports/)
- [ ] README.md reflects all Bob 2.0 features used
- [ ] `.bob/custom_modes.yaml` and `.bob/skills/` are committed
- [ ] GitHub Issue #001 has been read and analysed by the agent
