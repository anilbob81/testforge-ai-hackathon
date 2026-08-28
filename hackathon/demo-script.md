# TestForge AI — Demo Script
### IBM TechXchange 2026 Dev Day Hackathon
### "The 8-Minute Demo" — Full Autonomous Testing Showcase

---

## Objective

Demonstrate that a single plain-English statement triggers a complete autonomous
testing cycle — from reading a GitHub issue through to an email report with
AI-classified failure root causes and exact fix suggestions.

**The demo statement**: *"MAS has been upgraded. Validate that P2P still works."*

---

## Pre-Demo Setup Checklist

Run these BEFORE the demo starts:

```bash
# Verify quality gates pass
python .bob/hooks/pre-commit.py      # Should print: ✅ All quality gates passed

# Verify Maximo is reachable
python .bob/hooks/schema-verify.py   # Should print: ✅ Maximo schema verification PASSED

# Clear previous reports (for clean demo)
# (keep the reports/ folder, just note the timestamp)

# Verify email config works
python orchestrator.py --workflow service_request   # Fastest workflow with email
```

Have open and ready:
- [ ] Bob IDE with `test-architect` mode loaded
- [ ] Terminal in `maximo-ai-agent/` folder
- [ ] Email inbox open (for the live report delivery)
- [ ] `hackathon/github-issue-P2P-001.md` open in editor
- [ ] `workflow_map.json` open for reference

---

## The Demo Narrative

### Segment 1 — The Problem (0:00 → 1:30)

**Say**: *"Every IBM Maximo customer faces this. The system gets upgraded.
You need to know: does everything still work? Specifically — does P2P still work?
Purchase Requisition through to Invoice — the most business-critical workflow."*

**Show**: The traditional approach — point to a spreadsheet or test management tool.

*"Traditionally, a senior consultant spends 2-3 days manually clicking through
every step of P2P. That's 16-24 hours of billable time — for every upgrade cycle.
With upgrades happening every few weeks, this is a serious cost."*

**Show**: The GitHub issue file `hackathon/github-issue-P2P-001.md`

*"Here's a real scenario. MAS was upgraded to 9.2 yesterday. This issue
just came in — P2P is failing at the Receipt step. The team needs to know:
what broke, why, and how to fix it. Right now."*

---

### Segment 2 — The AI Takes Over (1:30 → 2:30)

**Action**: Switch Bob IDE to `test-architect` mode.

*"I'm switching to Test Architect mode — a custom Bob mode I've built for this project.
It gives Bob the right persona: a senior Maximo test architect who understands
the P2P lifecycle, the test catalogue, and how to run autonomous regression."*

**Type in Bob IDE**:
> *"Read the GitHub issue in hackathon/github-issue-P2P-001.md.
> Identify which tests to run and run them."*

**Show**: Bob activating the `requirement-analyser` skill automatically.

*"Watch what happens. Bob reads the issue. It activates the requirement-analyser skill
— a custom skill I've built that teaches Bob exactly how to map a change description
to the right test scope. It reads the change log, identifies P2P as impacted,
and selects the `pr_to_po` workflow — 18 tests instead of 78."*

**Show**: The impact matrix output from Bob.

*"This is AI-driven regression selection. Not 'run everything'. Run exactly
what's relevant to the change. That's the intelligence."*

---

### Segment 3 — Live Pipeline Execution (2:30 → 6:30)

**Action**: Run the pipeline (either Bob triggers it or demo runner does directly).

```bash
python orchestrator.py --workflow pr_to_po
```

**Narrate as each agent runs**:

**Agent 1** (~5 seconds):
*"Agent 1 — Requirement Analyser. It's reading the 67-page framework documentation
and mapping the workflow to test files. Document Understanding — Bob 2.0 feature."*

**Agent 2** (~1 second):
*"Agent 2 — Test Strategist. It's planning: API tests first for fast feedback,
then Selenium for the end-to-end UI flow. This is the subagent pattern —
planning in an isolated context."*

**Agent 3** (~4-8 seconds):
*"Agent 3 — API Test Runner. Firing 10 API tests against live Maximo right now.
pytest, JSON reporter, direct REST calls."*

**Watch the output**: Some tests pass quickly. Receipt test fails with HTTP 400.

**Agent 4** (~9 minutes — narrate during):
*"Agent 4 — Selenium. Chrome opens. It's clicking through the full P2P flow.
PR creation, approval, PO creation... the same steps a human tester would do.
Just faster. And it never gets tired."*

**If time is limited for demo**: Skip UI (pre-recorded video or use `--no-email api_only`
and explain that UI runs in full demo)

**Agent 5** (~2 seconds after tests complete):
*"Agent 5 — this is the star of the show. The Failure Analyst."*

*"Traditional automation says: 'Test failed. Here's the traceback. Good luck.'
Our AI says something completely different."*

**Show Agent 5 output — point to the classification**:
```
🟣 [TEST_DATA] test_create_receipt
   The storeroom CENTRAL is not valid for site BEDFORD.
   Likely cause: MAS 9.2 tightened storeroom validation.
   Storeroom must now be ACTIVE and org-linked.
   Fix: Inventory → Storerooms → CENTRAL → set Status to ACTIVE
   Action: ESCALATE_TO_ADMIN
   Confidence: HIGH
```

*"It didn't just say 'failed'. It said:
THIS is a test data problem, not a code defect.
THIS is the specific storeroom that's inactive.
THIS is exactly how to fix it in Maximo admin.
One sentence. That's hours of investigation — automated."*

*"And critically — it distinguished between an APPLICATION DEFECT, which would mean
Maximo itself is broken and needs a code fix, versus TEST DATA, which means
the environment just needs a configuration update. That distinction
is invaluable to a real testing team."*

---

### Segment 4 — The Email Report (6:30 → 7:30)

**Action**: Show email inbox — the report has arrived.

*"While we were watching the agents run, the Reporter agent was building
this HTML email report and sending it to the team."*

**Show the email**:
- Status header (red — failures detected)
- Score cards (total/passed/failed/hours saved)
- Pass rate bar
- Agent pipeline banner
- Failure analysis card with root cause and fix
- Full test results table

*"This is what a Maximo consultant gets at the end of a 2-3 day validation exercise.
We just produced it in 9 minutes. Automatically. With root cause analysis included."*

---

### Segment 5 — The Value Statement (7:30 → 8:00)

**Show**: The summary numbers.

```
18 tests executed
PR creation   PASS ✅
PR approval   PASS ✅
PO creation   PASS ✅
PO approval   PASS ✅
Receipt       FAIL ❌  → TEST_DATA: storeroom inactive (not a code bug)
Invoice       NOT RUN  → skipped (blocked by receipt failure)

Manual equivalent: 6 hours
Actual time: 9 minutes
Time reduction: 95%
```

*"One command. Five agents. Nine minutes. Complete answer."*

*"And the value doesn't stop here — these Bob skills I've built persist.
Next upgrade, next change, the AI already knows the P2P lifecycle,
the failure patterns, the test catalogue. It gets better over time."*

*"This is TestForge AI. The future of autonomous testing for IBM Maximo."*

---

## If Things Go Wrong (Fallback Plan)

### Maximo is unreachable
Run with pre-recorded results:
```bash
# Agent 5 can run standalone with pre-recorded results from reports/
python agents/agent_05_failure_analyst.py
```
Show the `reports/agent_report_pr_to_po_*.html` from a previous successful run.

### Email doesn't arrive live
```bash
python orchestrator.py --workflow pr_to_po --no-email
# Show the saved HTML report file
```

### Tests are all passing (no failures to demonstrate)
Temporarily set a wrong config to force a failure, or use the pre-saved report
showing the storeroom failure classification.

---

## Key Messages to Land

1. **One command → full autonomous cycle** (not step-by-step prompting)
2. **AI-driven regression selection** (18 tests not 78 — intelligent targeting)
3. **Failure classification** (the most valuable feature — not just "it failed")
4. **App defect vs test defect distinction** (saves escalation time)
5. **IBM Bob 2.0 features** (Skills, Modes, Rules, Subagents, Document Understanding, MCP)
6. **Durable value** (Skills + Modes survive the hackathon — team asset)

---

## Bob Features to Call Out Explicitly

| Feature | Where in Demo | Line to Say |
|---------|--------------|-------------|
| Custom Modes | Switching to test-architect | "Right persona for the right task" |
| Skills | Requirement-analyser activating | "Teaches Bob how — not just what" |
| Document Understanding | Agent 1 reading framework doc | "Reading 67 pages in 2 seconds" |
| Subagents | Agent 1 & 2 isolated contexts | "Each agent thinks independently" |
| Agent Mode | Whole pipeline | "This is Agent mode — autonomous" |
| MCP Pattern | Agent 5 querying Maximo | "Live system state, not just code" |
| Quality Gates | Pre-commit.py | "Sensors — feedback after Bob acts" |
| Rules | .bob/rules.md | "Guides — steer Bob before it acts" |

---

*Made with IBM Bob 2.0 · IBM TechXchange 2026 Dev Day Hackathon*
