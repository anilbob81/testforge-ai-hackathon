"""
Agent 6 -- Scoring across the 4 real Maximo upgrade ID-change patterns.
Tests what the algorithm can and cannot auto-correct.
"""
import sys
sys.path.insert(0, '.')
from agents.agent_06_locator_healer import LocatorHealer

healer = LocatorHealer()

# DOM snapshot AFTER a Maximo upgrade -- 4 different types of change
DOM_AFTER_UPGRADE = [
    # TYPE A: hash regenerated   mad3161b5-tb -> f9a7c2d1-tb
    {"tag": "input",  "id": "f9a7c2d1-tb",                     "name": "", "aria": "Work Order",        "data_id": "", "text": ""},
    # TYPE B: suffix version bump toolactions_INSERT-tbb_anchor -> toolactions_INSERT-tbb_anchor_v2
    {"tag": "button", "id": "toolactions_INSERT-tbb_anchor_v2", "name": "", "aria": "New Work Order",    "data_id": "", "text": "New Work Order"},
    # TYPE C: stable ID -- unchanged  quicksearch -> quicksearch
    {"tag": "input",  "id": "quicksearch",                     "name": "", "aria": "Search",             "data_id": "", "text": ""},
    # TYPE D: completely renamed  md86fe08f_ns_menu_APPR_OPTION_a -> approveWO_action_btn
    {"tag": "a",      "id": "approveWO_action_btn",            "name": "", "aria": "Approve Work Order", "data_id": "", "text": "Approve"},
    # Other page elements
    {"tag": "input",  "id": "m7b0033b9-tb",                    "name": "", "aria": "Location",           "data_id": "", "text": ""},
    {"tag": "div",    "id": "UIDrawerContainer",                "name": "", "aria": "",                   "data_id": "", "text": ""},
]

cases = [
    ("A: Hash regenerated",        "mad3161b5-tb",                    "f9a7c2d1-tb"),
    ("B: Suffix version bump",     "toolactions_INSERT-tbb_anchor",   "toolactions_INSERT-tbb_anchor_v2"),
    ("C: Stable ID (no change)",   "quicksearch",                     "quicksearch"),
    ("D: Completely renamed",      "md86fe08f_ns_menu_APPR_OPTION_a", "approveWO_action_btn"),
]

print()
print("=" * 85)
print("  Agent 6 -- Can it auto-correct these 4 upgrade ID-change patterns?")
print("=" * 85)
print(f"  {'CASE':<30} {'SCORE':>6}  {'CONF':<8}  {'AUTO?':<6}  {'CORRECT?':<9}  FOUND ID")
print("-" * 85)

for label, broken, expected_new in cases:
    m      = healer.find_best_match(broken, DOM_AFTER_UPGRADE)
    found  = m.get("candidate_id") or m.get("candidate_aria") or "none"
    correct = "[OK]   " if found == expected_new else "[MISS] "
    auto    = "YES" if m["auto_apply"] else "no"
    print(f"  {label:<30} {m['score']:>6.3f}  {m['confidence']:<8}  {auto:<6}  {correct}  {found}")

print()
print("=" * 85)
print("  LEGEND:")
print("  HIGH  (>0.85) = auto-corrects the file immediately")
print("  MEDIUM(>0.60) = proposes the fix, human must confirm")
print("  LOW   (<0.60) = escalates, lists top 3 candidates")
print("  NONE          = no match found at all")
print("=" * 85)
print()
print("  INTERPRETATION:")
print()
print("  A: Hash regenerated  -- score is LOW (0.000)")
print("     WHY: 'mad3161b5' shares zero tokens with 'f9a7c2d1'.")
print("          These are random IBM-generated hashes. No semantic overlap.")
print("          This is the hardest case -- Agent 6 CANNOT auto-correct it.")
print()
print("  B: Suffix version bump -- score should be HIGH (token overlap)")
print("     WHY: 'toolactions', 'INSERT', 'tbb', 'anchor' all appear in new ID.")
print("          Agent 6 CAN auto-correct this.")
print()
print("  C: Stable ID (no change) -- score is 1.000")
print("     WHY: Exact match. Correctly leaves it alone.")
print()
print("  D: Completely renamed -- check if aria-label saves it")
print("     WHY: Old ID 'md86fe08f_ns_menu_APPR_OPTION_a' shares no tokens with")
print("          new ID 'approveWO_action_btn'. But aria='Approve Work Order'")
print("          may bridge the gap via text matching.")
print()
