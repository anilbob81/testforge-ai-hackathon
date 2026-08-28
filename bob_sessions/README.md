# Bob Sessions — Task Session Screenshots
## IBM TechXchange 2026 Dev Day Hackathon Submission
### TestForge AI — Maximo Autonomous Test Engineer

---

## Screenshots in This Folder

The following screenshots were captured from IBM Bob 2.0 task sessions
during the development of the TestForge AI hackathon project.

| File | Description | Bob Mode Used |
|------|-------------|---------------|
| `How all agents are connected.png` | Full 7-agent pipeline architecture diagram — how Agents 0-6 connect from IBM Docs scrape through to email report | `test-architect` |
| `Test Strategist.png` | Agent 2 (Test Strategist) task session — showing API vs UI strategy decision for the P2P workflow (CRITICAL priority → API_AND_UI) | `test-architect` |
| `Failure Analyst agent.png` | Agent 5 (Failure Analyst) task session — showing TEST_DATA classification for storeroom CENTRAL failure after MAS 9.2 upgrade | `failure-investigator` |

---

## What the Screenshots Show

### `How all agents are connected.png`
The complete TestForge AI pipeline architecture:
- Agent 0 (Upgrade Scout) feeds IBM Docs + schema diff → Agent 1
- Agent 1 (Requirement Analyser) maps workflow to test files
- Agent 2 (Strategist) decides API vs UI coverage
- Agents 3 + 4 run in parallel (API and Selenium)
- Agent 5 classifies every failure with root cause
- Agent 6 autonomously heals LOCATOR_DRIFT failures
- Reporter builds HTML + sends email

### `Test Strategist.png`
Agent 2 in action — the subagent pattern demonstrated:
- Receives `pr_to_po` analysis from Agent 1
- Priority = CRITICAL → strategy = `API_AND_UI`
- Estimates 9 minutes runtime, 6h manual equivalent
- Produces execution plan for Agents 3 and 4

### `Failure Analyst agent.png`
Agent 5 classifying the storeroom failure — the star of the demo:
- Input: HTTP 400 + `BMXAA4073E` traceback
- Pattern match: `BMXAA4073E` + `not valid` + `storeroom`
- Classification: `TEST_DATA` (HIGH confidence)
- Fix: `Inventory → Storerooms → CENTRAL → Status → ACTIVE`
- Distinguishes APPLICATION_DEFECT vs TEST_DATA — saves hours of investigation

---

## Screenshot Instructions (for future sessions)

1. In Bob IDE, select **Tasks** in the chat panel header
2. Select the relevant task from the list
3. Click the **task header** to open the session consumption summary
4. Take a screenshot of the full summary panel
5. Save as PNG with the naming convention: `teamname_task##_description.png`
6. Place in this folder and update this README

---

## Bob 2.0 Features Captured

| Feature | Screenshot |
|---------|-----------|
| Custom Modes (`test-architect`) | `Test Strategist.png` |
| Custom Modes (`failure-investigator`) | `Failure Analyst agent.png` |
| Subagent pattern | `Test Strategist.png` |
| MCP Pattern + classification | `Failure Analyst agent.png` |
| Full pipeline architecture | `How all agents are connected.png` |

---

*Made with IBM Bob 2.0 · IBM TechXchange 2026 Dev Day Hackathon*
