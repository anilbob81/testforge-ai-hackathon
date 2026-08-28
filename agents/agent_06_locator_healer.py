"""
Agent 6 - Locator Healer
------------------------
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  When Agent 5 classifies a failure as LOCATOR_DRIFT, this agent
  attempts to autonomously heal the broken Selenium locator.

  STEP 1: Navigate to the failing Maximo page with Selenium
  STEP 2: Probe the live DOM -- capture all element IDs, aria-labels, names
  STEP 3: Fuzzy-match the broken locator against live elements
  STEP 4: HIGH confidence  -> auto-patch test file + re-run + report HEALED
          MEDIUM confidence -> propose the fix in the report (human confirms)
          LOW confidence   -> report NEEDS_HUMAN with candidate list
  STEP 5: Always create a .bak backup before patching
  STEP 6: Always revert if the healed test still fails

Bob 2.0 Feature Demonstrated:
  Autonomous Re-test Agent -- the loop that makes "autonomous" meaningful:
    Test failed -> Investigate -> Classify -> Fix -> Re-run -> Report

Confidence thresholds:
  HIGH   score > 0.85  -- auto-apply patch + re-run
  MEDIUM score > 0.60  -- propose only, human confirms
  LOW    score <= 0.60 -- escalate to human with candidates listed
"""

import json
import sys
import re
import time
import difflib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

AGENT_DIR = Path(__file__).parent
ROOT_DIR  = AGENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import (
    MAXIMO_BASE_URL, API_KEY, PROJECT_ROOT,
)

# Selenium -- graceful fallback if not installed or browser unavailable
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# ── Maximo application page paths ────────────────────────────────────────────
MAXIMO_PAGE_MAP = {
    "pr":        "PurchaseRequisitions",
    "po":        "PurchaseOrders",
    "receipt":   "Receiving",
    "invoice":   "InvoiceProcessing",
    "workorder": "WorkOrders",
    "wo":        "WorkOrders",
    "asset":     "Assets",
    "pm":        "PreventiveMaintenance",
    "sr":        "ServiceRequests",
}


class LocatorHealer:
    """
    Agent 6 -- Autonomously heals broken Selenium locators after MAS upgrades.

    When a DOM element ID changes (e.g. MAS 9.2 renames form fields),
    this agent probes the live Maximo page, finds the best semantic match
    for the broken locator, and patches the test file automatically.
    """

    HIGH_THRESHOLD   = 0.85
    MEDIUM_THRESHOLD = 0.60

    def __init__(self):
        self.driver    = None
        self.dom_cache = {}

    # =========================================================================
    # Browser management
    # =========================================================================

    def _start_driver(self, headless: bool = True) -> bool:
        if not SELENIUM_AVAILABLE:
            print("  [Healer] Selenium not available -- static analysis only")
            return False
        try:
            opts = Options()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument("--log-level=3")
            self.driver = webdriver.Chrome(options=opts)
            print("  [Healer] Chrome started for DOM probing")
            return True
        except Exception as e:
            print(f"  [Healer] Chrome unavailable: {e}")
            return False

    def _quit_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def _login(self) -> bool:
        """Authenticate to Maximo via API key URL parameter."""
        try:
            url = f"{MAXIMO_BASE_URL}/ui/?apikey={API_KEY}"
            self.driver.get(url)
            WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            print(f"  [Healer] Authenticated to Maximo")
            return True
        except Exception as e:
            print(f"  [Healer] Login failed: {e}")
            return False

    # =========================================================================
    # DOM Probing
    # =========================================================================

    def probe_page_dom(self, page_key: str) -> list:
        """
        Navigate to a Maximo application page and extract all interactable
        elements. Returns a list of element descriptor dicts.
        Caches results -- only probes each page once per session.
        """
        cache_key = page_key.lower()
        if cache_key in self.dom_cache:
            return self.dom_cache[cache_key]

        app_name = MAXIMO_PAGE_MAP.get(cache_key, cache_key.capitalize())
        url = f"{MAXIMO_BASE_URL}/ui/#v={app_name}&type=loadapp&id={cache_key}"
        print(f"  [Healer] Probing DOM: {app_name} ({url[:65]}...)")

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Maximo SPA needs time to fully render

            elements = []
            for tag in ["input", "button", "select", "textarea", "a", "label", "div"]:
                try:
                    found = self.driver.find_elements(By.TAG_NAME, tag)
                    for el in found[:200]:  # cap per tag to avoid huge sets
                        try:
                            el_id    = el.get_attribute("id") or ""
                            el_name  = el.get_attribute("name") or ""
                            el_aria  = el.get_attribute("aria-label") or ""
                            el_datid = el.get_attribute("data-id") or ""
                            el_class = (el.get_attribute("class") or "")[:60]
                            el_text  = (el.text or "")[:50]

                            # Only keep elements with at least one useful identifier
                            if any([el_id, el_name, el_aria, el_datid]):
                                elements.append({
                                    "tag":       tag,
                                    "id":        el_id,
                                    "name":      el_name,
                                    "aria":      el_aria,
                                    "data_id":   el_datid,
                                    "class":     el_class,
                                    "text":      el_text,
                                    "visible":   el.is_displayed(),
                                })
                        except Exception:
                            continue
                except Exception:
                    continue

            print(f"  [Healer] DOM probe: {len(elements)} identifiable element(s)")
            self.dom_cache[cache_key] = elements
            return elements

        except TimeoutException:
            print(f"  [Healer] DOM probe timed out for {page_key}")
            return []
        except Exception as e:
            print(f"  [Healer] DOM probe failed: {e}")
            return []

    # =========================================================================
    # Locator matching
    # =========================================================================

    def find_best_match(self, broken_locator: str, dom_elements: list) -> dict:
        """
        Find the best semantic match for a broken locator in the live DOM.

        Scoring strategy:
          - Keyword coverage: how many tokens from broken_locator appear in the element?
          - Sequence similarity: fuzzy string match on the element ID

        Returns a match dict with confidence level and auto_apply flag.
        """
        broken_lower = broken_locator.lower()
        # Tokenise the broken locator: 'po_storeloc_input' -> ['po','storeloc','input']
        tokens = [t for t in re.split(r'[-_./\s]', broken_lower) if len(t) > 2]

        best_el    = None
        best_score = 0.0

        for el in dom_elements:
            # Combined searchable text for this element
            combined = " ".join([
                el["id"], el["name"], el["aria"], el["data_id"], el["text"]
            ]).lower()

            # Token coverage score
            coverage = (sum(1 for t in tokens if t in combined)
                        / max(len(tokens), 1))

            # Sequence similarity on ID specifically
            id_sim = (difflib.SequenceMatcher(None, broken_lower, el["id"].lower()).ratio()
                      if el["id"] else 0.0)

            score = max(coverage, id_sim)
            if score > best_score:
                best_score = score
                best_el    = el

        if not best_el or best_score < 0.25:
            return {
                "broken_locator": broken_locator,
                "candidate_id":   None,
                "confidence":     "NONE",
                "score":          0.0,
                "auto_apply":     False,
                "note":           "No semantic match found in live DOM",
            }

        if best_score >= self.HIGH_THRESHOLD:
            confidence = "HIGH"
        elif best_score >= self.MEDIUM_THRESHOLD:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return {
            "broken_locator":   broken_locator,
            "candidate_id":     best_el["id"],
            "candidate_name":   best_el["name"],
            "candidate_aria":   best_el["aria"],
            "candidate_tag":    best_el["tag"],
            "candidate_text":   best_el["text"],
            "confidence":       confidence,
            "score":            round(best_score, 3),
            "auto_apply":       confidence == "HIGH",
        }

    # =========================================================================
    # Test file patching
    # =========================================================================

    def _find_test_file(self, test_name: str) -> Optional[Path]:
        """Locate the .py test file that contains the given test function name."""
        for py_file in PROJECT_ROOT.rglob("test_*.py"):
            try:
                if test_name in py_file.read_text(encoding="utf-8", errors="ignore"):
                    return py_file
            except Exception:
                continue
        return None

    def patch_test_file(self, test_name: str,
                        broken_locator: str, new_locator: str) -> dict:
        """
        Replace broken_locator with new_locator in the test file.
        Creates a .bak backup first. Returns patch result dict.
        """
        if not new_locator or broken_locator == new_locator:
            return {"patched": False,
                    "reason": "No usable new locator or locators are identical"}

        test_file = self._find_test_file(test_name)
        if not test_file:
            return {"patched": False,
                    "reason": f"Test file not found for '{test_name}'"}

        try:
            original = test_file.read_text(encoding="utf-8")
            count    = original.count(f'"{broken_locator}"') + \
                       original.count(f"'{broken_locator}'")
            if count == 0:
                return {"patched": False,
                        "reason": f"Locator '{broken_locator}' not found in {test_file.name}"}

            # Backup
            backup = test_file.with_suffix(".py.bak")
            backup.write_text(original, encoding="utf-8")

            # Patch both quote styles
            patched = original.replace(f'"{broken_locator}"', f'"{new_locator}"')
            patched = patched.replace(f"'{broken_locator}'", f"'{new_locator}'")
            test_file.write_text(patched, encoding="utf-8")

            print(f"  [Healer] Patched {test_file.name}: "
                  f"'{broken_locator}' -> '{new_locator}' ({count} occurrence(s))")

            return {
                "patched":        True,
                "test_file":      str(test_file),
                "backup_file":    str(backup),
                "broken_locator": broken_locator,
                "new_locator":    new_locator,
                "occurrences":    count,
            }
        except Exception as e:
            return {"patched": False, "reason": str(e)}

    def revert_patch(self, test_name: str) -> bool:
        """Revert test file to backup if re-run still fails after patch."""
        test_file = self._find_test_file(test_name)
        if not test_file:
            return False
        backup = test_file.with_suffix(".py.bak")
        if backup.exists():
            test_file.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
            backup.unlink()
            print(f"  [Healer] Reverted {test_file.name} to backup")
            return True
        return False

    # =========================================================================
    # Re-run verification
    # =========================================================================

    def rerun_test(self, node_id: str) -> dict:
        """Re-run a specific test to verify the locator patch worked."""
        print(f"  [Healer] Re-running: {node_id}")
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", node_id, "-v", "--tb=short",
                 "--no-header", "-q", "--timeout=60"],
                capture_output=True, text=True,
                cwd=PROJECT_ROOT, timeout=90,
            )
            passed = result.returncode == 0
            lines  = (result.stdout + result.stderr).strip().splitlines()
            print(f"  [Healer] Re-run: {'PASS' if passed else 'FAIL'}")
            return {
                "node_id":    node_id,
                "passed":     passed,
                "returncode": result.returncode,
                "output":     "\n".join(lines[-8:]),
            }
        except subprocess.TimeoutExpired:
            return {"node_id": node_id, "passed": False,
                    "error": "Re-run timed out after 90s"}
        except Exception as e:
            return {"node_id": node_id, "passed": False, "error": str(e)}

    # =========================================================================
    # Main heal loop
    # =========================================================================

    def heal(self, failures: list) -> dict:
        """
        Entry point called by Agent 5 / orchestrator.
        Processes all LOCATOR_DRIFT failures and attempts autonomous healing.
        """
        print(f"\n{'='*60}")
        print(f"  [Agent 6 - Locator Healer]")
        print(f"{'='*60}")

        drift_failures = [f for f in failures if f.get("category") == "LOCATOR_DRIFT"]

        if not drift_failures:
            print("  [Healer] No LOCATOR_DRIFT failures -- nothing to heal.")
            return {"success": True, "healed": 0, "proposed": 0,
                    "needs_human": 0, "results": []}

        print(f"  [Healer] {len(drift_failures)} LOCATOR_DRIFT failure(s) to process")

        # Start browser
        browser_ok = self._start_driver(headless=True)
        if browser_ok:
            browser_ok = self._login()

        results = []

        for failure in drift_failures:
            test_name = failure.get("test_name", "")
            node_id   = failure.get("node_id", "")
            traceback = failure.get("traceback_snippet", "")

            print(f"\n  Processing: {test_name}")

            # Extract the broken locator string from the traceback
            # Looks for quoted strings like "po-storeloc-input" or 'mat_storeloc'
            locator_match = re.search(
                r'(?:locate element|Unable to find|id=|By\.\w+\s*,\s*)["\']([A-Za-z][\w\-]{3,60})["\']',
                traceback,
            )
            if not locator_match:
                # Broader fallback: any quoted identifier-looking string
                locator_match = re.search(r'["\']([A-Za-z][\w\-]{4,60})["\']', traceback)

            broken_locator = locator_match.group(1) if locator_match else ""

            if not broken_locator:
                results.append({
                    "test_name":    test_name,
                    "status":       "NEEDS_HUMAN",
                    "reason":       "Cannot extract broken locator from traceback",
                    "fix_hint":     "Open Chrome DevTools on the failing Maximo page and inspect the element manually",
                })
                print(f"  [Healer] Cannot extract locator from traceback -- NEEDS_HUMAN")
                continue

            print(f"  [Healer] Broken locator: '{broken_locator}'")

            # Determine which Maximo page to probe
            page_key = "workorder"
            test_lower = (node_id + " " + test_name).lower()
            for key in MAXIMO_PAGE_MAP:
                if key in test_lower:
                    page_key = key
                    break

            # Probe live DOM
            dom_elements = self.probe_page_dom(page_key) if browser_ok else []

            # Find best match
            match = self.find_best_match(broken_locator, dom_elements)
            confidence   = match.get("confidence", "NONE")
            new_locator  = match.get("candidate_id") or match.get("candidate_aria") or ""

            print(f"  [Healer] Best match: '{new_locator}' "
                  f"(confidence={confidence}, score={match.get('score', 0):.2f})")

            if confidence == "HIGH" and new_locator:
                # Auto-patch + re-run
                patch = self.patch_test_file(test_name, broken_locator, new_locator)
                if patch["patched"]:
                    rerun = self.rerun_test(node_id)
                    if rerun["passed"]:
                        results.append({
                            "test_name":       test_name,
                            "broken_locator":  broken_locator,
                            "new_locator":     new_locator,
                            "status":          "HEALED",
                            "confidence":      confidence,
                            "score":           match["score"],
                            "patch_applied":   True,
                            "rerun_passed":    True,
                            "test_file":       patch.get("test_file", ""),
                            "backup_file":     patch.get("backup_file", ""),
                            "message":         (
                                f"Auto-healed: '{broken_locator}' -> '{new_locator}'. "
                                f"Test re-run: PASS. Patch committed."
                            ),
                        })
                        print(f"  [Healer] HEALED: {test_name}")
                    else:
                        # Patch didn't help -- revert
                        self.revert_patch(test_name)
                        results.append({
                            "test_name":      test_name,
                            "broken_locator": broken_locator,
                            "new_locator":    new_locator,
                            "status":         "NEEDS_HUMAN",
                            "confidence":     confidence,
                            "score":          match["score"],
                            "patch_applied":  True,
                            "rerun_passed":   False,
                            "patch_reverted": True,
                            "message":        (
                                f"Patch applied ('{broken_locator}' -> '{new_locator}') "
                                f"but test still fails. Patch reverted. Manual investigation needed."
                            ),
                        })
                        print(f"  [Healer] Patch applied but test still fails -- reverted")
                else:
                    results.append({
                        "test_name":      test_name,
                        "broken_locator": broken_locator,
                        "status":         "NEEDS_HUMAN",
                        "confidence":     confidence,
                        "reason":         patch.get("reason", "Patch failed"),
                    })

            elif confidence == "MEDIUM" and new_locator:
                results.append({
                    "test_name":         test_name,
                    "broken_locator":    broken_locator,
                    "proposed_locator":  new_locator,
                    "status":            "PROPOSED",
                    "confidence":        confidence,
                    "score":             match["score"],
                    "action":            (
                        f"Proposed fix: replace '{broken_locator}' -> '{new_locator}' "
                        f"in the test file. Confidence: {confidence} ({match['score']:.0%}). "
                        f"Verify in Maximo UI before applying."
                    ),
                })
                print(f"  [Healer] PROPOSED: '{broken_locator}' -> '{new_locator}'")

            else:
                candidates = []
                if dom_elements:
                    # List top 3 closest candidates for human to review
                    scored = []
                    tokens = [t for t in re.split(r'[-_]', broken_locator.lower()) if len(t) > 2]
                    for el in dom_elements:
                        combined = " ".join([el["id"], el["name"], el["aria"]]).lower()
                        s = sum(1 for t in tokens if t in combined) / max(len(tokens), 1)
                        if s > 0:
                            scored.append((s, el["id"] or el["name"] or el["aria"]))
                    scored.sort(reverse=True)
                    candidates = [c[1] for c in scored[:3] if c[1]]

                results.append({
                    "test_name":      test_name,
                    "broken_locator": broken_locator,
                    "status":         "NEEDS_HUMAN",
                    "confidence":     confidence,
                    "score":          match.get("score", 0),
                    "top_candidates": candidates,
                    "action":         (
                        f"Cannot auto-heal '{broken_locator}'. "
                        + (f"Top candidates: {candidates}. " if candidates else "No close matches found. ")
                        + f"Open Maximo {page_key} page in Chrome DevTools and inspect the element."
                    ),
                })
                print(f"  [Healer] NEEDS_HUMAN: no reliable match for '{broken_locator}'")

        self._quit_driver()

        healed      = sum(1 for r in results if r["status"] == "HEALED")
        proposed    = sum(1 for r in results if r["status"] == "PROPOSED")
        needs_human = sum(1 for r in results if r["status"] == "NEEDS_HUMAN")

        print(f"\n  [Healer] Results: "
              f"{healed} HEALED | {proposed} PROPOSED | {needs_human} NEEDS_HUMAN")

        return {
            "success":     True,
            "healed":      healed,
            "proposed":    proposed,
            "needs_human": needs_human,
            "results":     results,
            "healed_at":   datetime.now().isoformat(),
        }


# ── Standalone demo ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = [{
        "test_name":         "test_create_receipt",
        "node_id":           "tests/ui/test_10_ui_procurement_lifecycle.py::test_create_receipt",
        "category":          "LOCATOR_DRIFT",
        "traceback_snippet": "NoSuchElementException: Unable to locate element: \"po-storeloc-input\"",
    }]
    healer = LocatorHealer()
    result = healer.heal(sample)
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))
    if result["results"]:
        print(json.dumps(result["results"], indent=2))

# Made with IBM Bob 2.0
