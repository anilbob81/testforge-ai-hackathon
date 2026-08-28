"""
Agent 2 - Test Strategist
━━━━━━━━━━━━━━━━━━━━━━━━
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  • Receives the analysis from Agent 1
  • Decides the execution strategy: API only / UI only / Both / Skip
  • Considers: priority, time budget, risk level
  • Produces an execution plan consumed by Agents 3 and 4

Bob 2.0 Feature Demonstrated: Subagent pattern - parallel planning
  In a full Bob 2.0 session, this agent is spawned in parallel with
  the schema check so planning and pre-flight run simultaneously.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path(__file__).parent
ROOT_DIR  = AGENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))


class TestStrategist:
    """
    Agent 2 - Decides the test execution strategy based on the
    workflow analysis from Agent 1.

    Strategy rules:
      - CRITICAL workflows always run API + UI
      - HIGH workflows run API + UI if ui_tests exist
      - MEDIUM workflows run API only (faster, lower risk)
      - api_only / full_regression workflows use their own override
    """

    # Time budget thresholds (seconds)
    UI_TIME_BUDGET    = 1200   # 20 min max for UI tests
    API_TIME_BUDGET   = 60     # 1 min max for API tests

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

        workflow     = analysis["workflow_name"]
        priority     = analysis["priority"]
        api_files    = analysis["api_test_files"]
        ui_files     = analysis["ui_test_files"]

        # ── Strategy decision ─────────────────────────────────────────────────
        run_api = len(api_files) > 0
        run_ui  = len(ui_files) > 0

        if workflow == "api_only":
            run_ui = False
            strategy = "API_ONLY"
            rationale = "Workflow explicitly requests API-only fast validation."
        elif priority == "critical":
            strategy  = "API_AND_UI" if run_ui else "API_ONLY"
            rationale = "Critical workflow - full stack validation required (API backend + UI frontend)."
        elif priority == "high":
            strategy  = "API_AND_UI" if run_ui else "API_ONLY"
            rationale = "High priority - both layers provide comprehensive coverage."
        else:
            run_ui    = False
            strategy  = "API_ONLY"
            rationale = "Medium priority - API tests provide sufficient coverage with faster feedback."

        # Estimate times
        api_est_seconds = len(api_files) * 8     # ~8s per API module average
        ui_est_seconds  = len(ui_files)  * 540   # ~9 min per UI module average
        total_est       = api_est_seconds + (ui_est_seconds if run_ui else 0)

        plan = {
            "success":          True,
            "workflow_name":    workflow,
            "strategy":         strategy,
            "rationale":        rationale,
            "run_api":          run_api,
            "run_ui":           run_ui,
            "api_test_files":   api_files  if run_api else [],
            "ui_test_files":    ui_files   if run_ui  else [],
            "estimated_seconds": total_est,
            "manual_hours_equivalent": analysis["manual_hours_equivalent"],
            "business_process": analysis["business_process"],
            "priority":         priority,
            "planned_at":       datetime.now().isoformat(),
        }

        print(f"\n  [OK] Strategy decided: {strategy}")
        print(f"     Rationale    : {rationale}")
        print(f"     Run API      : {'YES - ' + str(len(api_files)) + ' module(s)' if run_api else 'NO'}")
        print(f"     Run UI       : {'YES - ' + str(len(ui_files))  + ' module(s)' if run_ui  else 'NO'}")
        m, s = divmod(total_est, 60)
        print(f"     Est. runtime : {int(m)}m {int(s)}s")
        print(f"     Manual equiv : {analysis['manual_hours_equivalent']}h saved")

        return plan


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulate receiving an analysis from Agent 1
    sample_analysis = {
        "workflow_name": "pr_to_po",
        "priority": "critical",
        "api_test_files": ["path/test_06_pr.py", "path/test_07_po.py"],
        "ui_test_files":  ["path/test_10_ui_procurement_lifecycle.py"],
        "manual_hours_equivalent": 6.0,
        "business_process": "Procure-to-Pay lifecycle",
    }
    strategist = TestStrategist()
    plan = strategist.plan(sample_analysis)
    print(json.dumps(plan, indent=2))

# Made with IBM Bob 2.0
