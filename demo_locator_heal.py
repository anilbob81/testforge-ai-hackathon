"""
Demo: Agent 6 Locator Healer -- Algorithm + File Patch Demo
============================================================

Proves the full Agent 6 healing loop:
  1. find_best_match()  -- fuzzy-scores the broken locator against a real DOM snapshot
  2. patch_test_file()  -- writes the fix directly into the .py test file
  3. File verification  -- confirms the broken ID is gone and the correct one is back

Broken locator: ELEM_WO_NUMBER = "mad3161b5-tb-OLD"  (was "mad3161b5-tb")
Score achieved: HIGH (0.857) -- auto_apply = True
"""

import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.agent_06_locator_healer import LocatorHealer

TEST_FILE = Path("../maximo-regression-tests/tests/ui/test_08_ui_workorder.py")

# Real Work Orders page DOM snapshot (elements present once the Maximo SPA loads)
WO_DOM_SNAPSHOT = [
    {"tag": "input",  "id": "quicksearch",                     "name": "",   "aria": "Search",              "data_id": "", "text": "", "visible": True},
    {"tag": "button", "id": "toolactions_INSERT-tbb_anchor",   "name": "",   "aria": "New Work Order",      "data_id": "", "text": "New Work Order", "visible": True},
    {"tag": "button", "id": "toolactions_SAVE-tbb_anchor",     "name": "",   "aria": "Save Work Order",     "data_id": "", "text": "Save", "visible": True},
    {"tag": "input",  "id": "mad3161b5-tb",                    "name": "",   "aria": "Work Order",          "data_id": "", "text": "", "visible": True},
    {"tag": "input",  "id": "mad3161b5-tb2",                   "name": "",   "aria": "Description",         "data_id": "", "text": "", "visible": True},
    {"tag": "input",  "id": "m7b0033b9-tb",                    "name": "",   "aria": "Location",            "data_id": "", "text": "", "visible": True},
    {"tag": "input",  "id": "md3801d08-tb",                    "name": "",   "aria": "Status",              "data_id": "", "text": "", "visible": True},
    {"tag": "a",      "id": "md86fe08f_ns_menu_APPR_OPTION_a", "name": "",   "aria": "Approve Work Order",  "data_id": "", "text": "Approve", "visible": True},
    {"tag": "div",    "id": "UIDrawerContainer",               "name": "",   "aria": "",                    "data_id": "", "text": "", "visible": True},
    {"tag": "div",    "id": "root",                            "name": "",   "aria": "",                    "data_id": "", "text": "", "visible": True},
]

healer = LocatorHealer()

print("\n" + "=" * 62)
print("  [DEMO] Agent 6 -- Locator Healer")
print("  Broken locator: ELEM_WO_NUMBER = 'mad3161b5-tb-OLD'")
print("=" * 62)

# ── Step 1: Fuzzy match ───────────────────────────────────────────────────────
broken = "mad3161b5-tb-OLD"
tokens = [t for t in re.split(r'[-_./\s]', broken.lower()) if len(t) > 2]
match  = healer.find_best_match(broken, WO_DOM_SNAPSHOT)

print(f"\n  STEP 1 -- Fuzzy Match")
print(f"    Broken locator   : '{broken}'")
print(f"    Tokens extracted : {tokens}")
print(f"    Best match found : '{match['candidate_id']}'  (aria: '{match.get('candidate_aria', '')}')")
print(f"    Score            : {match['score']:.3f}  ({match['score']:.0%})")
print(f"    Confidence       : {match['confidence']}")
print(f"    Auto-apply       : {match['auto_apply']}")
HIGH   = match['confidence'] == "HIGH"
MEDIUM = match['confidence'] == "MEDIUM"
print(f"    Decision         : {'AUTO-PATCH' if HIGH else 'PROPOSE ONLY' if MEDIUM else 'NEEDS_HUMAN'}")

# ── Step 2: Confirm the file has the broken locator ──────────────────────────
content_before = TEST_FILE.read_text(encoding="utf-8")
broken_present = "mad3161b5-tb-OLD" in content_before

print(f"\n  STEP 2 -- File State Before Patch")
print(f"    File             : {TEST_FILE.name}")
print(f"    Broken ID present: {broken_present}")

# ── Step 3: Apply the patch ───────────────────────────────────────────────────
print(f"\n  STEP 3 -- Applying Patch")
if broken_present and match["auto_apply"]:
    patch = healer.patch_test_file(
        "test_create_workorder_with_location_lookup",
        broken,
        match["candidate_id"],
    )
    print(f"    patch_test_file() called")
    print(f"    Patched          : {patch.get('patched')}")
    print(f"    Occurrences      : {patch.get('occurrences')}")
    print(f"    Backup file      : {Path(patch.get('backup_file', '')).name}")
    print(f"    '{broken}' -> '{match['candidate_id']}'")
else:
    print(f"    [SKIP] No patch needed or confidence not HIGH")
    patch = {"patched": False}

# ── Step 4: Verify file after patch ──────────────────────────────────────────
content_after = TEST_FILE.read_text(encoding="utf-8")
still_broken  = "mad3161b5-tb-OLD" in content_after
is_restored   = 'ELEM_WO_NUMBER      = "mad3161b5-tb"' in content_after

print(f"\n  STEP 4 -- File State After Patch")
print(f"    'mad3161b5-tb-OLD' still in file : {still_broken}")
print(f"    'mad3161b5-tb'     restored      : {is_restored}")

# ── Final verdict ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
if patch.get("patched") and is_restored and not still_broken:
    print("  RESULT: [HEALED]")
    print("  Agent 6 successfully auto-corrected the test file.")
    print(f"  '{broken}' -> '{match['candidate_id']}'")
    print(f"  Confidence: {match['confidence']} ({match['score']:.0%})")
    print(f"  Backup saved as: {Path(patch.get('backup_file', '')).name}")
elif MEDIUM:
    print("  RESULT: [PROPOSED]")
    print(f"  Proposed fix: '{broken}' -> '{match['candidate_id']}'")
    print("  Confidence MEDIUM -- human confirmation required before applying.")
else:
    print("  RESULT: [NEEDS_HUMAN]")
    print(f"  Score too low ({match['score']:.3f}) to auto-apply.")
print("=" * 62)
print()
