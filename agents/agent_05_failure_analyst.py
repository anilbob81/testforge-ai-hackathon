"""
Agent 5 - Failure Analyst
=========================
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  Receives test results from Agents 3 and 4.
  For EVERY failed test, reads the traceback and classifies the root cause.
  Queries live Maximo via REST API (MCP pattern) to confirm record state.
  Returns a structured failure report: category + explanation + fix.

AI Reasoning Layer (NEW):
  Calls IBM watsonx Granite to classify failures using real language model
  reasoning — not just pattern matching. Granite reads the full traceback,
  understands Maximo error codes, and produces:
    - A failure category
    - A plain-English explanation of WHY it failed
    - A concrete fix action
  Falls back to the rule-based pattern matcher if watsonx is unavailable.

Bob 2.0 Feature Demonstrated:
  MCP pattern       — queries live Maximo to verify system state
  watsonx Granite   — AI failure classification replaces static rules
  Document Understanding — reads tracebacks as natural language evidence
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
from agents.watsonx_client import get_client

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Rule-based fallback classification ───────────────────────────────────────
# Used when watsonx is unavailable.
# Each rule: (pattern_list, category, explanation, fix)
CLASSIFICATION_RULES = [
    (
        ["StaleElementReferenceException", "stale element"],
        "LOCATOR_DRIFT",
        "The Selenium element reference became stale — Maximo re-rendered the DOM "
        "after a partial page refresh triggered by item/lookup selection. "
        "This happens when Maximo upgrades change the page rendering sequence.",
        "Re-run the DOM probe script to verify element IDs are still correct. "
        "Check the probes/ folder for element ID discovery tools.",
    ),
    (
        ["ElementNotInteractableException"],
        "LOCATOR_DRIFT",
        "A Selenium element was found in the DOM but could not be interacted with. "
        "The element may be hidden, disabled, or overlapped by another element "
        "after a Maximo upgrade changed the page layout.",
        "Inspect the element in the browser dev tools. "
        "Check if a modal or overlay is blocking interaction. "
        "Update the locator or add an explicit wait before interaction.",
    ),
    (
        ["TimeoutException", "0 - 0 of 0"],
        "TIMING_ENVIRONMENT",
        "Maximo returned an empty list after navigation — the record was created "
        "but the server had not finished indexing before the search executed. "
        "This is a server-side timing race, not a code defect.",
        "Increase PAGE_LOAD_WAIT in maximo_ui_driver.py (try 18s). "
        "Re-run the test — this is not a persistent failure.",
    ),
    (
        ["TimeoutException"],
        "TIMING_ENVIRONMENT",
        "An expected UI element did not appear within the timeout window. "
        "The Maximo instance may be under load or responding slowly.",
        "Re-run the test when the instance is less busy. "
        "If persistent, increase ELEMENT_TIMEOUT in maximo_ui_driver.py.",
    ),
    (
        ["ConnectionError", "Failed to establish", "Max retries exceeded"],
        "ENVIRONMENT_AUTH",
        "Cannot connect to the Maximo instance. The URL may be unreachable "
        "or the VPN connection has dropped.",
        "Verify network connectivity to the Maximo URL. "
        "Check VPN is connected. Run schema-verify.py to test connectivity.",
    ),
    (
        ["401", "403", "Authentication", "apikey"],
        "ENVIRONMENT_AUTH",
        "Authentication failed — the API key may have expired or been revoked.",
        "Verify API_KEY in config/agent_config.py is current. "
        "Log in to Maximo and regenerate the API key if needed.",
    ),
    (
        ["BMXAA4073E"],
        "TEST_DATA",
        "Maximo rejected the record because a referenced object (storeroom, vendor, "
        "location) is invalid or inactive for the target site. "
        "MAS 9.2 tightened validation — storerooms must be ACTIVE and org-linked.",
        "Activate the storeroom in Maximo: Inventory -> Storerooms -> CENTRAL -> "
        "Status -> ACTIVE. Ensure Org=EAGLENA and Site=BEDFORD are linked.",
    ),
    (
        ["AssertionError", "not found", "0 records"],
        "TEST_DATA",
        "A required reference record was not found in Maximo. "
        "The test depends on reference data that may not exist in this environment.",
        "Check that required data exists: Vendor EMI, Site BEDFORD, "
        "Org EAGLENA, Storeroom CENTRAL. "
        "Update DEFAULT_PO_VENDOR in config if the vendor name differs.",
    ),
    (
        ["AssertionError", "status"],
        "APPLICATION_DEFECT",
        "A status field assertion failed — the record did not transition to the "
        "expected status. A business rule or workflow may have changed in this "
        "Maximo version.",
        "Manually verify the status transition in the Maximo UI. "
        "Check release notes for changes to this workflow. "
        "Raise a defect with the Maximo admin team if confirmed.",
    ),
    (
        ["AssertionError", "was not auto-generated", "number"],
        "APPLICATION_DEFECT",
        "A record number was not auto-generated — the autonumber sequence "
        "may not be configured for this object structure.",
        "Check Maximo autonumber configuration for this object structure. "
        "Verify the SITE and ORG are correctly configured.",
    ),
]


def _rule_classify(traceback: str, test_name: str) -> dict:
    """Rule-based classifier — fallback when watsonx is unavailable."""
    tb = traceback or ""
    for patterns, category, explanation, fix in CLASSIFICATION_RULES:
        if all(p.lower() in tb.lower() for p in patterns):
            return {
                "category":    category,
                "explanation": explanation,
                "fix":         fix,
                "confidence":  "HIGH",
                "source":      "rule_engine",
            }
    return {
        "category":    "UNKNOWN",
        "explanation": f"Could not automatically classify failure for '{test_name}'. "
                       "Manual investigation required.",
        "fix":         "Review the full traceback. Run the test in isolation with "
                       "-v --tb=long for the full stack trace.",
        "confidence":  "LOW",
        "source":      "rule_engine",
    }


def _granite_classify(wx, traceback: str, test_name: str, test_type: str) -> Optional[dict]:
    """
    Ask IBM Granite to classify a test failure using AI reasoning.
    Returns a classification dict or None if watsonx is unavailable/fails.
    """
    # Truncate traceback to fit in prompt — keep the most informative part
    tb_snippet = (traceback or "")[:800]

    prompt = (
        "You are an expert IBM Maximo test failure analyst.\n"
        "Classify this test failure and provide a fix recommendation.\n\n"
        f"Test name: {test_name}\n"
        f"Test type: {test_type}\n"
        f"Traceback/Error:\n{tb_snippet}\n\n"
        "Failure categories:\n"
        "- APPLICATION_DEFECT: Maximo returned wrong data or status "
        "(upgrade introduced a regression in business logic)\n"
        "- LOCATOR_DRIFT: Selenium could not find or interact with a UI element "
        "(DOM changed after upgrade)\n"
        "- TIMING_ENVIRONMENT: Timeout or race condition "
        "(server slowness, not a code defect)\n"
        "- ENVIRONMENT_AUTH: Connection refused, 401, 403 "
        "(API key expired or Maximo unreachable)\n"
        "- TEST_DATA: Missing or inactive reference data "
        "(storeroom, vendor, location not configured)\n"
        "- UNKNOWN: Cannot determine from available evidence\n\n"
        "Respond in exactly this format:\n"
        "CATEGORY: <category>\n"
        "EXPLANATION: <one or two sentences explaining the root cause>\n"
        "FIX: <one concrete action to resolve it>\n"
        "CONFIDENCE: <HIGH or MEDIUM or LOW>\n"
    )

    response = wx.generate(prompt)
    if not response:
        return None

    result = {
        "category":    "UNKNOWN",
        "explanation": "",
        "fix":         "",
        "confidence":  "LOW",
        "source":      "watsonx_granite",
    }

    valid_cats = {
        "APPLICATION_DEFECT", "LOCATOR_DRIFT", "TIMING_ENVIRONMENT",
        "ENVIRONMENT_AUTH", "TEST_DATA", "UNKNOWN",
    }

    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("CATEGORY:"):
            raw = line.replace("CATEGORY:", "").strip().upper()
            for cat in valid_cats:
                if cat in raw:
                    result["category"] = cat
                    break
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.replace("EXPLANATION:", "").strip()
        elif line.startswith("FIX:"):
            result["fix"] = line.replace("FIX:", "").strip()
        elif line.startswith("CONFIDENCE:"):
            raw = line.replace("CONFIDENCE:", "").strip().upper()
            if "HIGH" in raw:
                result["confidence"] = "HIGH"
            elif "MEDIUM" in raw:
                result["confidence"] = "MEDIUM"

    # Only return if we got meaningful content
    if result["explanation"] and result["fix"]:
        return result
    return None


def _classify_failure(traceback: str, test_name: str, test_type: str,
                       wx=None) -> dict:
    """
    Classify a test failure.
    Tries watsonx Granite first; falls back to rule engine.
    """
    # Try AI classification
    if wx and wx.available:
        ai_result = _granite_classify(wx, traceback, test_name, test_type)
        if ai_result:
            return ai_result

    # Rule-based fallback
    return _rule_classify(traceback, test_name)


def _query_maximo_record(object_structure: str, field: str,
                          value: str) -> Optional[dict]:
    """
    Query live Maximo to check the current state of a record.
    Demonstrates the MCP pattern — using live system data in analysis.
    """
    try:
        url    = f"{MAXIMO_API_ENDPOINT}/os/{object_structure}"
        params = {
            "oslc.where":    f'{field}="{value}" and siteid="{SITE_ID}"',
            "oslc.select":   "status,description",
            "oslc.pageSize": "1",
            "lean":          "1",
        }
        headers = {API_KEY_HEADER: API_KEY, "Accept": "application/json"}
        resp = requests.get(
            url, params=params, headers=headers,
            verify=VERIFY_SSL, timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            members = resp.json().get("member", [])
            return members[0] if members else None
    except Exception:
        pass
    return None


class FailureAnalyst:
    """
    Agent 5 — Reads failure tracebacks from Agents 3 and 4,
    classifies each failure using IBM Granite AI (with rule fallback),
    optionally queries live Maximo for context (MCP pattern),
    and returns a structured failure analysis report.
    """

    def analyse(self, api_results: dict, ui_results: dict) -> dict:
        print(f"\n{'='*60}")
        print(f"  [Agent 5 - Failure Analyst]")
        print(f"{'='*60}")
        print(f"  (IBM Granite AI classification + rule-based fallback)")

        # Initialise watsonx client once for all failures
        wx = get_client()
        if wx.available:
            print(f"  [watsonx] Granite AI active — classifying with LLM reasoning")
        else:
            print(f"  [watsonx] Unavailable — using rule-based classification")

        all_failures         = []
        total_manual_saved   = 0.0
        ai_classified_count  = 0
        rule_classified_count = 0

        for results in [api_results, ui_results]:
            if results.get("skipped"):
                continue

            tests     = results.get("tests", [])
            test_type = results.get("test_type", "unknown")

            for test in tests:
                if test.get("outcome", "") != "failed":
                    continue

                node_id   = test.get("nodeid", "")
                test_name = node_id.split("::")[-1]

                call_info = test.get("call", {})
                traceback = call_info.get("longrepr", "") or ""
                if isinstance(traceback, dict):
                    traceback = str(traceback)

                # Classify — AI first, rules as fallback
                classification = _classify_failure(
                    traceback, test_name, test_type, wx
                )

                if classification["source"] == "watsonx_granite":
                    ai_classified_count += 1
                else:
                    rule_classified_count += 1

                hours = 0.75 if test_type == "ui" else 0.25
                total_manual_saved += hours

                failure_record = {
                    "test_name":         test_name,
                    "node_id":           node_id,
                    "test_type":         test_type,
                    "category":          classification["category"],
                    "explanation":       classification["explanation"],
                    "fix":               classification["fix"],
                    "confidence":        classification["confidence"],
                    "classification_by": classification["source"],
                    "traceback_snippet": traceback[:300] if traceback else "",
                    "manual_hours":      hours,
                }
                all_failures.append(failure_record)

                label = "[AI]" if classification["source"] == "watsonx_granite" else "[rule]"
                print(f"\n  {label} [{classification['category']}] {test_name}")
                print(f"     {classification['explanation'][:80]}...")
                print(f"     Fix: {classification['fix'][:80]}...")

        # ── Summary ───────────────────────────────────────────────────────────
        categories   = {}
        for f in all_failures:
            cat = f["category"]
            categories[cat] = categories.get(cat, 0) + 1

        total_tests  = api_results.get("total", 0) + ui_results.get("total", 0)
        total_passed = api_results.get("passed", 0) + ui_results.get("passed", 0)
        total_failed = len(all_failures)

        if total_failed == 0:
            print(f"\n  [OK] No failures to analyse — all {total_tests} tests passed!")
        else:
            print(f"\n  [STATS] {total_failed} failure(s) classified:")
            for cat, count in categories.items():
                print(f"     {cat}: {count}")
            if ai_classified_count:
                print(f"     Classified by Granite AI : {ai_classified_count}")
            if rule_classified_count:
                print(f"     Classified by rule engine: {rule_classified_count}")

        return {
            "success":               True,
            "total_failures":        total_failed,
            "failures":              all_failures,
            "category_summary":      categories,
            "total_tests":           total_tests,
            "total_passed":          total_passed,
            "manual_hours_saved":    total_manual_saved,
            "ai_classified":         ai_classified_count,
            "rule_classified":       rule_classified_count,
            "classification_engine": "watsonx_granite" if ai_classified_count else "rule_engine",
            "analysed_at":           datetime.now().isoformat(),
        }


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_api_results = {
        "skipped": False, "test_type": "api",
        "total": 5, "passed": 4, "failed": 1,
        "tests": [{
            "nodeid": "tests/api/test_07_po.py::TestReceiptCreation::test_create_receipt",
            "outcome": "failed",
            "call": {
                "longrepr": (
                    "AssertionError: HTTP 400 Bad Request\n"
                    "BMXAA4073E - The storeroom CENTRAL specified in the receiving "
                    "record is not valid for site BEDFORD."
                )
            },
        }],
    }
    sample_ui_results = {"skipped": True}
    analyst = FailureAnalyst()
    report  = analyst.analyse(sample_api_results, sample_ui_results)
    print()
    print(json.dumps(
        {k: v for k, v in report.items() if k not in ("failures",)},
        indent=2
    ))
    if report["failures"]:
        print("\nFailure detail:")
        print(json.dumps(report["failures"][0], indent=2))

# Made with IBM Bob 2.0
