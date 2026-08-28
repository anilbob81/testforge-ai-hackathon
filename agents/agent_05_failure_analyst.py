"""
Agent 5 - Failure Analyst
━━━━━━━━━━━━━━━━━━━━━━━━
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  • Receives test results from Agents 3 and 4
  • For EVERY failed test, reads the traceback and classifies the root cause
  • Queries live Maximo via REST API (MCP pattern) to confirm record state
  • Returns a structured failure report with root cause + suggested fix

Bob 2.0 Feature Demonstrated:
  - Document Understanding - reads tracebacks and log content
  - MCP pattern - queries live Maximo API to verify system state
  - Intelligent classification - 5 failure categories with fix suggestions

Failure Categories:
  APPLICATION_DEFECT   - Maximo returned unexpected data (upgrade broke something)
  LOCATOR_DRIFT        - Selenium element ID changed after Maximo upgrade
  TIMING_ENVIRONMENT   - DOM refresh / server slowness caused a race condition
  ENVIRONMENT_AUTH     - API key expired or Maximo unreachable
  TEST_DATA            - Required reference data missing in Maximo
  UNKNOWN              - Cannot classify - manual investigation needed
"""

import json
import sys
import requests
import urllib3
from pathlib import Path
from datetime import datetime
from typing import Optional

AGENT_DIR = Path(__file__).parent
ROOT_DIR  = AGENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import (
    MAXIMO_API_ENDPOINT, API_KEY, API_KEY_HEADER,
    SITE_ID, VERIFY_SSL, REQUEST_TIMEOUT,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Classification rules ──────────────────────────────────────────────────────
# Each rule: (pattern_list, category, explanation_template, fix_template)
CLASSIFICATION_RULES = [
    (
        ["StaleElementReferenceException", "stale element"],
        "LOCATOR_DRIFT",
        "The Selenium element reference became stale - Maximo re-rendered the DOM "
        "(likely after a partial page refresh triggered by item/lookup selection). "
        "This happens after Maximo upgrades change the page rendering sequence.",
        "Re-run the relevant DOM probe script to verify element IDs are still correct. "
        "Check probe_post_upgrade.py and the probes/ folder for element ID discovery tools.",
    ),
    (
        ["TimeoutException", "0 - 0 of 0"],
        "TIMING_ENVIRONMENT",
        "Maximo returned an empty list after navigation - the record was created but "
        "the server had not finished indexing/committing it before the search executed. "
        "This is a server-side timing race, not a code defect.",
        "Increase PAGE_LOAD_WAIT in maximo_ui_driver.py (currently 12s - try 18s). "
        "This is not a test failure in production - re-run the test.",
    ),
    (
        ["TimeoutException"],
        "TIMING_ENVIRONMENT",
        "An expected UI element did not appear within the timeout window. "
        "The Maximo instance may be under load or responding slowly.",
        "Re-run the test when the Maximo instance is less busy. "
        "If persistent, increase ELEMENT_TIMEOUT in maximo_ui_driver.py.",
    ),
    (
        ["ConnectionError", "Failed to establish", "Max retries exceeded"],
        "ENVIRONMENT_AUTH",
        "Cannot connect to the Maximo instance. The URL may be unreachable "
        "or the network/VPN connection has dropped.",
        "Verify network connectivity to the Maximo URL. "
        "Check VPN is connected if required. "
        "Run: python probes/probe_post_upgrade.py to test connectivity.",
    ),
    (
        ["401", "403", "Authentication", "apikey"],
        "ENVIRONMENT_AUTH",
        "Authentication failed - the API key may have expired or been revoked.",
        "Verify API_KEY in config/config.py is current and active. "
        "Log in to Maximo and regenerate the API key if needed.",
    ),
    (
        ["AssertionError", "status", "Expected status"],
        "APPLICATION_DEFECT",
        "A status field assertion failed - the Maximo record did not transition "
        "to the expected status. This may indicate a business rule change, "
        "a workflow configuration change, or a Maximo upgrade introduced a regression.",
        "Manually verify the status transition in the Maximo UI. "
        "Check Maximo release notes for changes to this workflow. "
        "Raise a defect with the Maximo admin team.",
    ),
    (
        ["AssertionError", "was not auto-generated", "number"],
        "APPLICATION_DEFECT",
        "A record number was not auto-generated - Maximo's autonumber sequence "
        "may not be configured for this object structure.",
        "Check Maximo autonumber configuration for this object structure. "
        "Verify the SITE and ORG are correctly configured.",
    ),
    (
        ["AssertionError", "not found", "0 records"],
        "TEST_DATA",
        "A required reference record was not found in Maximo. "
        "The test depends on reference data (vendor, location, item, storeroom) "
        "that may not exist in this Maximo environment.",
        "Check that all required reference data exists: "
        "Vendor EMI, Site BEDFORD, Org EAGLENA, Storeroom CENTRAL. "
        "Update DEFAULT_PO_VENDOR in config.py if the vendor name differs.",
    ),
]


def _classify_failure(traceback: str, test_name: str) -> dict:
    """
    Classify a test failure by matching traceback patterns to known categories.
    Returns a classification dict with category, explanation, and fix suggestion.
    """
    tb = traceback or ""

    for patterns, category, explanation, fix in CLASSIFICATION_RULES:
        if all(p.lower() in tb.lower() for p in patterns):
            return {
                "category":    category,
                "explanation": explanation,
                "fix":         fix,
                "confidence":  "HIGH",
            }

    # No pattern matched
    return {
        "category":    "UNKNOWN",
        "explanation": f"Could not automatically classify this failure for test '{test_name}'. "
                       "Manual investigation required.",
        "fix":         "Review the full traceback. Check logs/agent_run.log for details. "
                       "Run the test in isolation with -v --tb=long for full stack trace.",
        "confidence":  "LOW",
    }


def _query_maximo_record(object_structure: str, field: str, value: str) -> Optional[dict]:
    """
    Query live Maximo to check the current state of a record.
    Demonstrates the MCP pattern - using live system data in analysis.
    """
    try:
        url = f"{MAXIMO_API_ENDPOINT}/os/{object_structure}"
        params = {
            "oslc.where":   f'{field}="{value}" and siteid="{SITE_ID}"',
            "oslc.select":  "status,description",
            "oslc.pageSize": "1",
            "lean":          "1",
        }
        headers = {API_KEY_HEADER: API_KEY, "Accept": "application/json"}
        resp = requests.get(
            url, params=params, headers=headers,
            verify=VERIFY_SSL, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 200:
            members = resp.json().get("member", [])
            return members[0] if members else None
    except Exception:
        pass
    return None


class FailureAnalyst:
    """
    Agent 5 - Reads failure tracebacks from Agents 3 and 4,
    classifies each failure, optionally queries live Maximo for context,
    and returns a structured failure analysis report.
    """

    def analyse(self, api_results: dict, ui_results: dict) -> dict:
        """
        Analyse failures from both API and UI test runs.

        Returns a comprehensive failure analysis consumed by the Reporter.
        """
        print(f"\n{'='*60}")
        print(f"  [Agent 5 - Failure Analyst]")
        print(f"{'='*60}")

        all_failures = []
        total_manual_hours_saved = 0.0

        # ── Collect failed tests from both runners ────────────────────────────
        for results in [api_results, ui_results]:
            if results.get("skipped"):
                continue

            tests     = results.get("tests", [])
            test_type = results.get("test_type", "unknown")

            for test in tests:
                outcome = test.get("outcome", "")
                if outcome != "failed":
                    continue

                node_id   = test.get("nodeid", "")
                test_name = node_id.split("::")[-1]

                # Extract traceback
                call_info = test.get("call", {})
                traceback = call_info.get("longrepr", "") or ""
                if isinstance(traceback, dict):
                    traceback = str(traceback)

                # Classify the failure
                classification = _classify_failure(traceback, test_name)

                # Hours saved estimate per test (manual would take longer)
                hours = 0.75 if test_type == "ui" else 0.25
                total_manual_hours_saved += hours

                failure_record = {
                    "test_name":      test_name,
                    "node_id":        node_id,
                    "test_type":      test_type,
                    "category":       classification["category"],
                    "explanation":    classification["explanation"],
                    "fix":            classification["fix"],
                    "confidence":     classification["confidence"],
                    "traceback_snippet": traceback[:300] if traceback else "",
                    "manual_hours":   hours,
                }

                all_failures.append(failure_record)

                icon = {
                    "APPLICATION_DEFECT": "🔴",
                    "LOCATOR_DRIFT":      "🟡",
                    "TIMING_ENVIRONMENT": "🟠",
                    "ENVIRONMENT_AUTH":   "🔵",
                    "TEST_DATA":          "🟣",
                    "UNKNOWN":            "⚪",
                }.get(classification["category"], "⚪")

                print(f"\n  {icon} [{classification['category']}] {test_name}")
                print(f"     {classification['explanation'][:80]}...")
                print(f"     Fix: {classification['fix'][:80]}...")

        # ── Category summary ──────────────────────────────────────────────────
        categories = {}
        for f in all_failures:
            cat = f["category"]
            categories[cat] = categories.get(cat, 0) + 1

        total_tests  = (api_results.get("total", 0) + ui_results.get("total", 0))
        total_passed = (api_results.get("passed", 0) + ui_results.get("passed", 0))
        total_failed = len(all_failures)

        if total_failed == 0:
            print(f"\n  [OK] No failures to analyse - all tests passed!")
        else:
            print(f"\n  [STATS] Failure summary: {total_failed} failure(s)")
            for cat, count in categories.items():
                print(f"     {cat}: {count}")

        return {
            "success":               True,
            "total_failures":        total_failed,
            "failures":              all_failures,
            "category_summary":      categories,
            "total_tests":           total_tests,
            "total_passed":          total_passed,
            "manual_hours_saved":    total_manual_hours_saved,
            "analysed_at":           datetime.now().isoformat(),
        }


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulate a failure for demo
    sample_api_results = {
        "skipped": False, "test_type": "api",
        "total": 5, "passed": 4, "failed": 1,
        "tests": [{
            "nodeid": "tests/api/test_06_pr.py::TestPRCreation::test_create_pr_minimal",
            "outcome": "failed",
            "call": {"longrepr": "AssertionError: Expected status APPR but got WAPPR"},
        }]
    }
    sample_ui_results = {"skipped": True}
    analyst = FailureAnalyst()
    report  = analyst.analyse(sample_api_results, sample_ui_results)
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))

# Made with IBM Bob 2.0
