"""
Agent 2 - Test Strategist
=========================
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  Receives the analysis from Agent 1 and decides the execution strategy:
  API_ONLY / API_AND_UI / SKIP — with estimated runtime and rationale.

AI Reasoning Layer (NEW):
  Calls IBM watsonx Granite to reason about the optimal test strategy
  based on workflow context, priority, available tests, and MAS change signals.
  Falls back to rule-based if/elif logic if watsonx is unavailable.

Bob 2.0 Feature Demonstrated:
  Subagent pattern — isolated planning context
  watsonx Granite AI — replaces hardcoded if/elif with live LLM reasoning
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path(__file__).parent
ROOT_DIR  = AGENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from agents.watsonx_client import get_client


class TestStrategist:
    """
    Agent 2 — Decides the test execution strategy.

    PRIMARY:  IBM watsonx Granite reasons about the strategy based on full context.
    FALLBACK: Rule-based if/elif logic (priority + workflow type).

    The AI path produces richer rationale and can weigh multiple signals
    (scout report, priority, workflow type, available tests) simultaneously.
    """

    UI_TIME_BUDGET  = 1200   # 20 min max for UI tests
    API_TIME_BUDGET = 60     # 1 min max for API tests

    def plan(self, analysis: dict) -> dict:
        """
        Build the execution plan from Agent 1's analysis.
        Returns an execution plan dict consumed by Agents 3 and 4.
        """
        print(f"\n{'='*60}")
        print(f"  [Agent 2 - Test Strategist]")
        print(f"{'='*60}")
        print(f"  Planning strategy for: '{analysis['workflow_name']}'")
        print(f"  Priority: {analysis['priority'].upper()}")

        workflow  = analysis["workflow_name"]
        priority  = analysis["priority"]
        api_files = analysis["api_test_files"]
        ui_files  = analysis["ui_test_files"]

        # ── Try watsonx AI reasoning first ───────────────────────────────────
        ai_strategy  = None
        ai_rationale = None
        wx = get_client()

        if wx.available:
            print(f"  [watsonx] Asking Granite to reason about strategy...")
            ai_strategy, ai_rationale = self._ask_granite_strategy(
                wx, workflow, priority, api_files, ui_files, analysis
            )

        # ── Decide run_api / run_ui from AI result or rules ──────────────────
        run_api = len(api_files) > 0
        run_ui  = len(ui_files) > 0

        if ai_strategy and ai_strategy in ("API_ONLY", "API_AND_UI", "SKIP"):
            strategy  = ai_strategy
            rationale = ai_rationale or f"IBM Granite AI decision: {strategy}"
            source    = "watsonx_granite"
            if strategy == "API_ONLY":
                run_ui = False
            elif strategy == "SKIP":
                run_api = False
                run_ui  = False
            print(f"  [watsonx] Granite strategy: {strategy}")
        else:
            # Rule-based fallback
            strategy, rationale = self._rule_based_strategy(
                workflow, priority, run_api, run_ui
            )
            source = "rule_engine"
            if strategy == "API_ONLY":
                run_ui = False
            print(f"  [rule] Fallback strategy: {strategy}")

        # ── Estimate times ────────────────────────────────────────────────────
        api_est = len(api_files) * 8      # ~8s per API module
        ui_est  = len(ui_files)  * 540    # ~9 min per UI module
        total   = api_est + (ui_est if run_ui else 0)

        plan = {
            "success":                   True,
            "workflow_name":             workflow,
            "strategy":                  strategy,
            "rationale":                 rationale,
            "strategy_source":           source,
            "run_api":                   run_api,
            "run_ui":                    run_ui,
            "api_test_files":            api_files if run_api else [],
            "ui_test_files":             ui_files  if run_ui  else [],
            "estimated_seconds":         total,
            "manual_hours_equivalent":   analysis["manual_hours_equivalent"],
            "business_process":          analysis["business_process"],
            "priority":                  priority,
            "planned_at":                datetime.now().isoformat(),
        }

        print(f"\n  [OK] Strategy: {strategy}  [{source}]")
        print(f"     Rationale  : {rationale[:80]}...")
        print(f"     Run API    : {'YES - ' + str(len(api_files)) + ' module(s)' if run_api else 'NO'}")
        print(f"     Run UI     : {'YES - ' + str(len(ui_files))  + ' module(s)' if run_ui  else 'NO'}")
        m, s = divmod(int(total), 60)
        print(f"     Est. time  : {m}m {s}s")
        print(f"     Manual equiv: {analysis['manual_hours_equivalent']}h saved")

        return plan

    # ── watsonx Granite reasoning ─────────────────────────────────────────────

    def _ask_granite_strategy(self, wx, workflow, priority, api_files,
                               ui_files, analysis) -> tuple:
        """
        Ask IBM Granite to reason about the best test strategy.
        Returns (strategy_string, rationale_string) or (None, None) on failure.
        """
        scout_signals = ""
        if analysis.get("scout_impacted"):
            scout_signals = f"Upgrade Scout detected changes in: {analysis['scout_impacted']}."

        prompt = (
            "You are an expert IBM Maximo test strategist.\n"
            "Decide the optimal test execution strategy for this scenario.\n\n"
            f"Workflow: {workflow}\n"
            f"Priority: {priority}\n"
            f"API test modules available: {len(api_files)}\n"
            f"UI (Selenium) test modules available: {len(ui_files)}\n"
            f"Business process: {analysis.get('business_process', '')[:100]}\n"
            f"{scout_signals}\n\n"
            "Rules:\n"
            "- API_AND_UI: use when critical/high priority AND UI tests exist AND "
            "the workflow involves end-to-end business flows that need browser validation\n"
            "- API_ONLY: use when medium/low priority OR no UI tests exist OR "
            "only backend validation is needed\n"
            "- SKIP: use only if the workflow has no tests at all\n\n"
            "Respond in exactly this format:\n"
            "STRATEGY: <API_ONLY or API_AND_UI or SKIP>\n"
            "REASON: <one sentence explaining why>\n"
        )

        response = wx.generate(prompt)
        if not response:
            return None, None

        strategy  = None
        rationale = None

        for line in response.strip().split("\n"):
            line = line.strip()
            if line.startswith("STRATEGY:"):
                raw = line.replace("STRATEGY:", "").strip().upper()
                for candidate in ("API_AND_UI", "API_ONLY", "SKIP"):
                    if candidate in raw:
                        strategy = candidate
                        break
            elif line.startswith("REASON:"):
                rationale = line.replace("REASON:", "").strip()

        return strategy, rationale

    # ── Rule-based fallback ───────────────────────────────────────────────────

    def _rule_based_strategy(self, workflow, priority, run_api, run_ui) -> tuple:
        """Original if/elif strategy logic — used when watsonx is unavailable."""
        if workflow == "api_only":
            return "API_ONLY", "Workflow explicitly requests API-only fast validation."
        if priority == "critical":
            s = "API_AND_UI" if run_ui else "API_ONLY"
            return s, "Critical workflow — full stack validation required (API + UI)."
        if priority == "high":
            s = "API_AND_UI" if run_ui else "API_ONLY"
            return s, "High priority — both layers provide comprehensive coverage."
        return "API_ONLY", "Medium priority — API tests provide sufficient coverage."


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_analysis = {
        "workflow_name":           "pr_to_po",
        "priority":                "critical",
        "api_test_files":          ["path/test_06_pr.py", "path/test_07_po.py"],
        "ui_test_files":           ["path/test_10_ui_procurement_lifecycle.py"],
        "manual_hours_equivalent": 6.0,
        "business_process":        "Procure-to-Pay lifecycle",
        "scout_impacted":          ["pr_to_po"],
    }
    strategist = TestStrategist()
    plan = strategist.plan(sample_analysis)
    print(json.dumps({k: v for k, v in plan.items() if k != "api_test_files"}, indent=2))

# Made with IBM Bob 2.0
