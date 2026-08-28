"""
Agent 3 - API Test Runner
━━━━━━━━━━━━━━━━━━━━━━━━
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  • Receives the execution plan from Agent 2
  • Runs the selected API pytest test files against live Maximo
  • Captures full JSON results
  • Returns structured results for Agent 5 (Failure Analyst)

Bob 2.0 Feature Demonstrated: Agent Mode - command execution
  Runs pytest subprocesses, reads results, surfaces failures.
"""

import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path(__file__).parent
ROOT_DIR  = AGENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import PROJECT_ROOT, REPORTS_DIR


class APITestRunner:
    """
    Agent 3 - Executes API pytest tests for the planned modules
    and returns structured results.
    """

    def run(self, plan: dict) -> dict:
        """
        Execute API tests from the execution plan.

        Returns structured results including pass/fail counts,
        per-test outcomes, and raw JSON for Agent 5.
        """
        print(f"\n{'='*60}")
        print(f"  [Agent 3 - API Test Runner]")
        print(f"{'='*60}")

        api_files = plan.get("api_test_files", [])

        if not api_files:
            print("  [INFO]️  No API tests in this plan - skipping.")
            return {
                "success":   True,
                "skipped":   True,
                "reason":    "No API test files in plan",
                "total":     0,
                "passed":    0,
                "failed":    0,
                "tests":     [],
                "duration":  0.0,
            }

        print(f"  Running {len(api_files)} API test module(s):")
        for f in api_files:
            print(f"    • {Path(f).name}")

        # Write JSON report to a temp file
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_report = REPORTS_DIR / f"api_results_{ts}.json"

        # Build pytest command - runs from the existing project root
        cmd = [
            sys.executable, "-m", "pytest",
            *api_files,
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={json_report}",
            "-q",
        ]

        print(f"\n  Executing pytest...")
        start = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=False,
                timeout=300,
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            return {
                "success":  False,
                "error":    "API tests timed out after 300 seconds",
                "total":    0, "passed": 0, "failed": 0, "tests": [],
                "duration": 300.0,
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
        tests     = []
        summary   = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        json_path = str(json_report)

        if json_report.exists():
            try:
                with open(json_report) as f:
                    data = json.load(f)
                tests   = data.get("tests", [])
                s       = data.get("summary", {})
                summary = {
                    "total":   s.get("total",   0),
                    "passed":  s.get("passed",  0),
                    "failed":  s.get("failed",  0),
                    "skipped": s.get("skipped", 0),
                }
            except Exception as e:
                print(f"  [WARN]️  Could not parse JSON report: {e}")

        passed  = summary["passed"]
        failed  = summary["failed"]
        total   = summary["total"]
        success = exit_code == 0

        icon = "[OK]" if success else "[FAIL]"
        print(f"\n  {icon} API Results: {passed}/{total} passed in {duration:.1f}s")
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
            "test_type":        "api",
        }


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_plan = {
        "api_test_files": [
            str(PROJECT_ROOT / "tests/api/test_06_pr.py"),
            str(PROJECT_ROOT / "tests/api/test_07_po.py"),
        ],
    }
    runner  = APITestRunner()
    results = runner.run(sample_plan)
    print(json.dumps({k: v for k, v in results.items() if k != "tests"}, indent=2))

# Made with IBM Bob 2.0
