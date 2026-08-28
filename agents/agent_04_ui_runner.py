"""
Agent 4 - UI Test Runner (Selenium)

IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  • Receives the execution plan from Agent 2
  • Runs the selected Selenium UI pytest test files
  • Chrome browser opens visibly - full end-user workflow automation
  • Captures full JSON results
  • Returns structured results for Agent 5 (Failure Analyst)

Bob 2.0 Feature Demonstrated: Agent Mode - Chrome browser automation
  Drives real IBM Maximo UI through complete business workflows.

IMPORTANT: Do not click inside Chrome while tests are running.
           Selenium controls the browser - user interaction causes failures.
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path(__file__).parent
ROOT_DIR  = AGENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import PROJECT_ROOT, REPORTS_DIR


class UITestRunner:
    """
    Agent 4 - Executes Selenium UI tests for the planned modules.
    Chrome opens visibly and automates the full Maximo user workflow.
    """

    def run(self, plan: dict) -> dict:
        """
        Execute UI (Selenium) tests from the execution plan.

        Returns structured results including pass/fail counts,
        per-test outcomes, and raw JSON for Agent 5.
        """
        print(f"\n{'='*60}")
        print(f"  [Agent 4 - UI Test Runner (Selenium)]")
        print(f"{'='*60}")

        ui_files = plan.get("ui_test_files", [])

        if not ui_files:
            print("  [INFO]  No UI tests in this plan - skipping.")
            return {
                "success":  True,
                "skipped":  True,
                "reason":   "No UI test files in plan",
                "total":    0,
                "passed":   0,
                "failed":   0,
                "tests":    [],
                "duration": 0.0,
            }

        est_mins = len(ui_files) * 9
        print(f"  Running {len(ui_files)} UI test module(s):")
        for f in ui_files:
            print(f"    • {Path(f).name}")
        print(f"\n  [WARN]  Chrome will open - do NOT click inside it during the test run")
        print(f"    Estimated time: ~{est_mins} minutes")

        # Write JSON report
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_report = REPORTS_DIR / f"ui_results_{ts}.json"

        # Build pytest command - uses ui_selenium marker to filter correctly
        cmd = [
            sys.executable, "-m", "pytest",
            *ui_files,
            "-v",
            "--tb=short",
            "-m", "ui_selenium",
            "--json-report",
            f"--json-report-file={json_report}",
        ]

        print(f"\n  Executing Selenium tests...")
        start = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=False,
                timeout=1800,   # 30 min max for full UI suite
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            return {
                "success":  False,
                "error":    "UI tests timed out after 30 minutes",
                "total":    0, "passed": 0, "failed": 0, "tests": [],
                "duration": 1800.0,
            }
        except Exception as e:
            return {
                "success":  False,
                "error":    str(e),
                "total":    0, "passed": 0, "failed": 0, "tests": [],
                "duration": 0.0,
            }

        duration = (datetime.now() - start).total_seconds()

        # Parse JSON report
        tests   = []
        summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        json_path = str(json_report)

        if json_report.exists():
            try:
                with open(json_report) as f:
                    data = json.load(f)
                tests = data.get("tests", [])
                s     = data.get("summary", {})
                summary = {
                    "total":   s.get("total",   0),
                    "passed":  s.get("passed",  0),
                    "failed":  s.get("failed",  0),
                    "skipped": s.get("skipped", 0),
                }
            except Exception as e:
                print(f"  [WARN]  Could not parse JSON report: {e}")

        passed  = summary["passed"]
        failed  = summary["failed"]
        total   = summary["total"]
        success = exit_code == 0

        m, s_rem = divmod(int(duration), 60)
        icon = "[OK]" if success else "[FAIL]"
        print(f"\n  {icon} UI Results: {passed}/{total} passed in {m}m {s_rem}s")
        if failed > 0:
            failed_tests = [t["nodeid"].split("::")[-1] for t in tests if t.get("outcome") == "failed"]
            print(f"  [FAIL] Failed: {', '.join(failed_tests)}")

        return {
            "success":          success,
            "skipped":          False,
            "exit_code":        exit_code,
            "total":            total,
            "passed":           passed,
            "failed":           failed,
            "skipped_count":    summary["skipped"],
            "duration":         duration,
            "tests":            tests,
            "json_report_path": json_path,
            "test_type":        "ui",
        }


#  Standalone run 
if __name__ == "__main__":
    sample_plan = {
        "ui_test_files": [
            str(PROJECT_ROOT / "tests/ui/test_10_ui_procurement_lifecycle.py"),
        ],
    }
    runner  = UITestRunner()
    results = runner.run(sample_plan)
    print(json.dumps({k: v for k, v in results.items() if k != "tests"}, indent=2))

# Made with IBM Bob 2.0
