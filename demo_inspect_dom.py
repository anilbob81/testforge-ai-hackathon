"""
DOM Inspector -- shows exactly what Agent 6 sees when it probes the Work Orders page.
Helps diagnose why a locator match succeeds or fails.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.agent_06_locator_healer import LocatorHealer

healer = LocatorHealer()
browser_ok = healer._start_driver(headless=True)
if browser_ok:
    browser_ok = healer._login()

if browser_ok:
    elements = healer.probe_page_dom("workorder")
    print(f"\nLive DOM -- WorkOrders page: {len(elements)} identifiable elements\n")
    print(f"{'TAG':<10} {'ID':<45} {'NAME':<25} {'ARIA':<30}")
    print("-" * 115)
    for el in elements:
        print(f"{el['tag']:<10} {el['id'][:44]:<45} {el['name'][:24]:<25} {el['aria'][:29]:<30}")

    # Also run the matcher against our broken locator to show the scoring
    print("\n\nTop 10 matches for 'mad3161b5-tb-OLD' (token: mad3161b5, tb, OLD):\n")
    import re, difflib
    broken = "mad3161b5-tb-OLD"
    broken_lower = broken.lower()
    tokens = [t for t in re.split(r'[-_./\s]', broken_lower) if len(t) > 2]
    print(f"Tokens extracted: {tokens}\n")
    scored = []
    for el in elements:
        combined = " ".join([el["id"], el["name"], el["aria"], el["data_id"], el["text"]]).lower()
        coverage = sum(1 for t in tokens if t in combined) / max(len(tokens), 1)
        id_sim   = difflib.SequenceMatcher(None, broken_lower, el["id"].lower()).ratio() if el["id"] else 0.0
        score    = max(coverage, id_sim)
        scored.append((score, el["id"] or el["name"] or el["aria"], el["tag"], combined[:60]))
    scored.sort(reverse=True)
    print(f"{'SCORE':<8} {'ELEMENT ID / NAME':<45} {'TAG':<10} COMBINED TEXT")
    print("-" * 115)
    for score, eid, tag, comb in scored[:10]:
        print(f"{score:.3f}    {eid[:44]:<45} {tag:<10} {comb[:50]}")

healer._quit_driver()
