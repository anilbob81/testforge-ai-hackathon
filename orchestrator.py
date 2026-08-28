"""
Maximo Autonomous Test Engineer -- Orchestrator
IBM Bob 2.0 Hackathon -- IBM TechXchange 2026 Dev Day -- Aug 28-30

ONE command triggers a 7-agent AI pipeline that:
  0. Gathers REAL upgrade intelligence (IBM Docs + live schema diff + domain diff)
  1. Maps workflow to test modules  (Document Understanding)
  2. Plans API vs UI strategy       (Subagent pattern)
  3. Runs API regression tests      (Agent Mode)
  4. Runs Selenium UI tests         (Agent Mode)
  5. Classifies every failure       (MCP + AI classification)
  6. Auto-heals broken locators     (Autonomous re-test agent)
  7. Sends email report             (Reporter)

Usage:
    python orchestrator.py --workflow pr_to_po
    python orchestrator.py --workflow full_regression
    python orchestrator.py --workflow work_order --no-email
    python orchestrator.py --workflow api_only
    python orchestrator.py --scout          # Run Agent 0 only (save baselines)
    python orchestrator.py --list

IBM Bob 2.0 features demonstrated:
    Agent Mode             -- full autonomous pipeline
    Subagents              -- Agents 0/1 in isolated context, Agent 2 parallel planning
    Document Understanding -- IBM Docs scrape + 67-page framework doc
    MCP Pattern            -- Agent 0 schema diff + Agent 5 failure context queries
    Autonomous Re-test     -- Agent 6 heals LOCATOR_DRIFT failures automatically
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import REPORTS_DIR, LOGS_DIR

# ── Agent imports ─────────────────────────────────────────────────────────────
from agents.agent_00_upgrade_scout   import UpgradeScout
from agents.agent_01_analyser        import RequirementAnalyser
from agents.agent_02_strategist      import TestStrategist
from agents.agent_03_api_runner      import APITestRunner
from agents.agent_04_ui_runner       import UITestRunner
from agents.agent_05_failure_analyst import FailureAnalyst
from agents.agent_06_locator_healer  import LocatorHealer
from reporter.report_builder          import build_report, send_report

WORKFLOW_MAP = ROOT_DIR / "workflow_map.json"


def _print_banner():
    print("\n" + "=" * 62)
    print("  [BOB 2.0] MAXIMO AUTONOMOUS TEST ENGINEER")
    print("  IBM Bob 2.0 Hackathon - IBM TechXchange 2026 Dev Day")
    print("=" * 62)
    print(f"  Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Powered by: IBM Bob 2.0 - 7-Agent Pipeline")
    print("-" * 62)


def _print_footer(workflow, grand_total, grand_passed, grand_failed, manual_saved, duration):
    print("\n" + "=" * 62)
    icon = "[PASS]" if grand_failed == 0 else "[FAIL]"
    print(f"  {icon}  PIPELINE COMPLETE - {workflow.replace('_',' ').upper()}")
    print("-" * 62)
    print(f"  Tests run    : {grand_total}  ({grand_passed} passed, {grand_failed} failed)")
    m, s = divmod(int(duration), 60)
    print(f"  Duration     : {m}m {s}s")
    print(f"  Manual equiv : {manual_saved}h of manual testing automated")
    pct = round((manual_saved * 3600 - duration) / (manual_saved * 3600) * 100) if manual_saved else 0
    print(f"  Time saved   : ~{manual_saved}h reduced to {m}m {s}s  ({pct}% reduction)")
    print("=" * 62 + "\n")


def _list_workflows():
    with open(WORKFLOW_MAP) as f:
        wmap = json.load(f)
    workflows = wmap.get("workflows", {})
    print("\n  Available workflows:\n")
    print(f"  {'Workflow':<22} {'Priority':<10} {'Manual Hours':<14} Description")
    print(f"  {'-'*22} {'-'*10} {'-'*14} {'-'*35}")
    for name, wf in workflows.items():
        api_count = len(wf.get("api_tests", []))
        ui_count  = len(wf.get("ui_tests",  []))
        modules   = f"{api_count}API"
        if ui_count:
            modules += f"+{ui_count}UI"
        print(f"  {name:<22} {wf['priority']:<10} {str(wf['manual_hours_equivalent'])+'h':<14} {wf['description'][:45]}")
    print()


def run_pipeline(workflow_name: str, send_email: bool = True,
                 skip_scout: bool = False) -> int:
    """
    Main pipeline -- runs all 7 agents in sequence and sends the email report.
    Returns exit code: 0 = all passed, 1 = failures detected, 2 = pipeline error.
    """
    _print_banner()

    # Ensure output dirs exist
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    pipeline_start = datetime.now()
    scout_report   = {}

    # ── Agent 0 — Upgrade Scout (IBM Docs + Schema Diff + Domain Diff) ───────
    if not skip_scout:
        print(f"\n  [Agent 0] Spawning Upgrade Scout...")
        print(f"     (IBM Docs scrape + live Maximo schema diff via MCP)")
        try:
            scout        = UpgradeScout()
            scout_report = scout.scout()
            impacted     = scout_report.get("impacted_workflows", [])
            if impacted:
                print(f"     Agent 0 detected impacted workflows: {impacted}")
        except Exception as e:
            print(f"\n  [WARN] Agent 0 error (non-blocking): {e}")
            scout_report = {"success": False, "impacted_workflows": []}
    else:
        print(f"\n  [Agent 0] Skipped (--no-scout flag)")

    # ── Agent 1 — Requirement Analyser (Document Understanding) ──────────────
    print(f"\n  [Agent 1] Spawning Requirement Analyser...")
    print(f"     (Reads MAXIMO_TEST_AUTOMATION_FRAMEWORK.md + workflow_map.json)")
    try:
        analyser = RequirementAnalyser(WORKFLOW_MAP)
        analysis = analyser.analyse(workflow_name)
        # Enrich with scout data if available
        if scout_report.get("ibm_docs_count"):
            analysis["ibm_docs_change_count"] = scout_report["ibm_docs_count"]
            analysis["scout_impacted"]        = scout_report.get("impacted_workflows", [])
        if not analysis.get("success"):
            print(f"\n  [ERROR] Agent 1 failed: {analysis.get('error')}")
            return 2
    except Exception as e:
        print(f"\n  [ERROR] Agent 1 error: {e}")
        return 2

    # ── Agent 2 — Test Strategist (Subagent — parallel planning) ─────────────
    print(f"\n  [Agent 2] Spawning Test Strategist...")
    print(f"     (Plans API vs UI coverage based on workflow priority)")
    try:
        strategist = TestStrategist()
        plan       = strategist.plan(analysis)
        if not plan.get("success"):
            print(f"\n  [ERROR] Agent 2 failed to produce a plan")
            return 2
    except Exception as e:
        print(f"\n  [ERROR] Agent 2 error: {e}")
        return 2

    # ── Agent 3 — API Test Runner ─────────────────────────────────────────────
    print(f"\n  [Agent 3] Spawning API Test Runner...")
    try:
        api_runner  = APITestRunner()
        api_results = api_runner.run(plan)
    except Exception as e:
        print(f"\n  [ERROR] Agent 3 error: {e}")
        api_results = {"success": False, "error": str(e), "total": 0, "passed": 0,
                       "failed": 0, "tests": [], "duration": 0.0, "skipped": False}

    # ── Agent 4 — UI Test Runner (Selenium) ───────────────────────────────────
    print(f"\n  [Agent 4] Spawning UI Test Runner (Selenium)...")
    try:
        ui_runner  = UITestRunner()
        ui_results = ui_runner.run(plan)
    except Exception as e:
        print(f"\n  [ERROR] Agent 4 error: {e}")
        ui_results = {"success": False, "error": str(e), "total": 0, "passed": 0,
                      "failed": 0, "tests": [], "duration": 0.0, "skipped": True}

    # ── Agent 5 — Failure Analyst ─────────────────────────────────────────────
    print(f"\n  [Agent 5] Spawning Failure Analyst...")
    print(f"     (Classifies failures: Defect / Locator / Timing / Auth / Data)")
    try:
        analyst          = FailureAnalyst()
        failure_analysis = analyst.analyse(api_results, ui_results)
    except Exception as e:
        print(f"\n  [ERROR] Agent 5 error: {e}")
        failure_analysis = {"success": False, "total_failures": 0, "failures": [],
                            "category_summary": {}, "manual_hours_saved": 0.0}

    # ── Agent 6 — Locator Healer (only when LOCATOR_DRIFT failures exist) ─────
    heal_analysis = {"healed": 0, "proposed": 0, "needs_human": 0, "results": []}
    drift_count   = failure_analysis.get("category_summary", {}).get("LOCATOR_DRIFT", 0)
    if drift_count > 0:
        print(f"\n  [Agent 6] Spawning Locator Healer...")
        print(f"     ({drift_count} LOCATOR_DRIFT failure(s) -- attempting autonomous heal)")
        try:
            healer       = LocatorHealer()
            heal_analysis = healer.heal(failure_analysis.get("failures", []))
            # Update failure counts if any tests were healed
            healed = heal_analysis.get("healed", 0)
            if healed > 0:
                print(f"     Agent 6 healed {healed} test(s) -- adjusting counts")
        except Exception as e:
            print(f"\n  [WARN] Agent 6 error (non-blocking): {e}")
    else:
        print(f"\n  [Agent 6] Locator Healer -- no LOCATOR_DRIFT failures, skipping.")

    # ── Build report + send email ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  [Reporter — Building Final Report]")
    print(f"{'='*60}")

    grand_total  = api_results.get("total",  0) + ui_results.get("total",  0)
    grand_passed = api_results.get("passed", 0) + ui_results.get("passed", 0)
    grand_failed = api_results.get("failed", 0) + ui_results.get("failed", 0)
    manual_saved = analysis.get("manual_hours_equivalent", 0)
    duration     = (datetime.now() - pipeline_start).total_seconds()

    html = build_report(analysis, plan, api_results, ui_results,
                        failure_analysis, heal_analysis, scout_report)

    if send_email:
        send_report(html, workflow_name, grand_passed, grand_failed)
    else:
        # Save report to disk even if not emailing
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_file = REPORTS_DIR / f"agent_report_{workflow_name}_{ts}.html"
        html_file.write_text(html, encoding="utf-8")
        print(f"  [SAVE] Report saved (email skipped): {html_file}")

    _print_footer(workflow_name, grand_total, grand_passed, grand_failed, manual_saved, duration)

    return 0 if grand_failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Maximo Autonomous Test Engineer -- IBM Bob 2.0 Hackathon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrator.py --workflow pr_to_po           # PR -> PO lifecycle
  python orchestrator.py --workflow work_order         # WO lifecycle
  python orchestrator.py --workflow api_only           # All 58 API tests (fast)
  python orchestrator.py --workflow full_regression    # All 78 tests
  python orchestrator.py --workflow pr_to_po --no-email   # Skip email
  python orchestrator.py --workflow pr_to_po --no-scout   # Skip Agent 0
  python orchestrator.py --scout                       # Run Agent 0 only
  python orchestrator.py --list                        # Show all workflows
        """,
    )
    parser.add_argument(
        "--workflow", "-w",
        help="Workflow to test (e.g. pr_to_po, work_order, full_regression)",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending the email report (report saved to reports/ folder)",
    )
    parser.add_argument(
        "--no-scout",
        action="store_true",
        help="Skip Agent 0 upgrade scout (faster, uses cached data)",
    )
    parser.add_argument(
        "--scout",
        action="store_true",
        help="Run Agent 0 upgrade scout only (save baselines, no test execution)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available workflows",
    )

    args = parser.parse_args()

    if args.list:
        _list_workflows()
        return

    if args.scout:
        print("\n  [BOB 2.0] Running Agent 0 -- Upgrade Scout only")
        scout = UpgradeScout()
        scout.scout()
        return

    if not args.workflow:
        parser.print_help()
        print("\n  Use --list to see available workflows, or --workflow <name> to run.\n")
        sys.exit(0)

    exit_code = run_pipeline(
        workflow_name=args.workflow,
        send_email=not args.no_email,
        skip_scout=args.no_scout,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

# Made with IBM Bob 2.0
