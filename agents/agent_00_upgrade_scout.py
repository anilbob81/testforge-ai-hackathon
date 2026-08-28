"""
Agent 0 - Upgrade Scout
-----------------------
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  Gathers REAL upgrade intelligence from three live sources -- not hardcoded
  assumptions. Replaces mas-change-catalog.md with live data on every run.

  SOURCE 1: IBM Docs Scraper
    Fetches https://www.ibm.com/docs/en/maximo-manage/cd?topic=manage-whats-new-in-maximo-92
    Parses the real What's New page into structured change items.

  SOURCE 2: Live Maximo Schema Diff (MCP)
    Queries OSLC /os/<structure> for each tracked object structure.
    Diffs against stored baseline -- new/removed fields = real API changes.
    First run saves the baseline. Every subsequent run diffs against it.

  SOURCE 3: Domain/Lookup Diff (MCP)
    Compares status code domains (WOSTATUS, PRSTATUS, POSTATUS) before/after.
    New or removed status codes mean test assertions may need updating.

Bob 2.0 Feature Demonstrated:
  MCP Pattern -- live Maximo OSLC schema queries for system intelligence
  Document Understanding -- real IBM docs web page parsing

Output:
  reports/upgrade_scout_report.json consumed by Agent 1 (Requirement Analyser)
"""

import json
import sys
import re
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
    VERIFY_SSL, REQUEST_TIMEOUT,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── IBM Docs URL ──────────────────────────────────────────────────────────────
IBM_DOCS_92_URL = (
    "https://www.ibm.com/docs/en/maximo-manage/cd"
    "?topic=manage-whats-new-in-maximo-92"
)

# ── Object structures to schema-diff ─────────────────────────────────────────
# Note: this Maximo instance exposes MXAPI-prefixed variants for SR and Location
SCHEMA_STRUCTURES = ["mxwo", "mxasset", "mxapisr", "mxapioperloc", "mxinventory"]

# ── Domains to value-diff ─────────────────────────────────────────────────────
DOMAINS_TO_CHECK = ["WOSTATUS", "PRSTATUS", "POSTATUS"]

# ── Baselines folder ─────────────────────────────────────────────────────────
BASELINE_DIR = ROOT_DIR / "baselines"

# ── Change text -> workflow mapping ──────────────────────────────────────────
KEYWORD_WORKFLOW_MAP = {
    "purchase requisition": "pr_to_po",
    "requisition":          "pr_to_po",
    "purchase order":       "pr_to_po",
    "procurement":          "pr_to_po",
    "receiving":            "pr_to_po",
    "receipt":              "pr_to_po",
    "invoice":              "pr_to_po",
    "storeroom":            "pr_to_po",
    "vendor":               "pr_to_po",
    "work order":           "work_order",
    "workorder":            "work_order",
    "preventive":           "pm_maintenance",
    "job plan":             "pm_maintenance",
    "asset":                "asset_management",
    "service request":      "service_request",
}

SCHEMA_WORKFLOW_MAP = {
    "mxwo":        "work_order",
    "mxasset":     "asset_management",
    "mxapisr":     "service_request",
    "mxapioperloc":"asset_management",
    "mxinventory": "pr_to_po",
}


class UpgradeScout:
    """
    Agent 0 -- Gathers real upgrade intelligence from IBM Docs + live Maximo
    schema queries (MCP). Replaces hardcoded change catalog with live data.
    """

    def __init__(self):
        self.headers = {
            API_KEY_HEADER: API_KEY,
            "Accept": "application/json",
        }

    # =========================================================================
    # SOURCE 1 -- IBM Docs What's New scraper
    # =========================================================================

    def scrape_ibm_whats_new(self, url: str = IBM_DOCS_92_URL) -> list:
        """
        Fetch the real IBM Maximo 9.2 What's New page and extract change items.
        Returns a list of dicts: {description, functional_area, impacted_workflows, impact}
        """
        print(f"  [Scout] Fetching IBM Docs: {url[:75]}...")
        changes = []

        try:
            resp = requests.get(
                url,
                timeout=20,
                verify=False,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 TestForge-AI/1.0"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            if resp.status_code != 200:
                print(f"  [Scout] IBM Docs HTTP {resp.status_code} -- using offline fallback")
                return self._offline_92_changes()

            # Strip all HTML tags
            raw = re.sub(r'<[^>]+>', ' ', resp.text)
            # Collapse whitespace
            raw = re.sub(r'\s+', ' ', raw)

            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', raw)

            change_triggers = [
                'new', 'added', 'updated', 'changed', 'improved',
                'enhanced', 'deprecated', 'removed', 'support for',
                'now ', 'ability to', 'you can now',
            ]
            skip_phrases = [
                'copyright', 'ibm corporation', 'log in', 'sign in',
                'cookie', 'privacy', 'terms of use', 'feedback',
            ]

            seen = set()
            for sentence in sentences:
                sentence = sentence.strip()
                lower    = sentence.lower()

                if (50 < len(sentence) < 500
                        and any(t in lower for t in change_triggers)
                        and not any(s in lower for s in skip_phrases)
                        and sentence not in seen):
                    seen.add(sentence)
                    area      = self._classify_area(sentence)
                    workflows = self._map_to_workflows(sentence)
                    changes.append({
                        "source":             "IBM_DOCS_92",
                        "description":        sentence[:400],
                        "functional_area":    area,
                        "impacted_workflows": workflows,
                        "impact":             "HIGH" if workflows else "LOW",
                    })
                    if len(changes) >= 40:
                        break

            print(f"  [Scout] IBM Docs: {len(changes)} change item(s) extracted")
            if not changes:
                print("  [Scout] No parseable changes found -- using offline fallback")
                return self._offline_92_changes()
            return changes

        except Exception as e:
            print(f"  [Scout] IBM Docs fetch error: {e} -- using offline fallback")
            return self._offline_92_changes()

    def _offline_92_changes(self) -> list:
        """
        Offline fallback: known MAS 9.2 changes from IBM documentation.
        Used when the IBM Docs page is unreachable.
        """
        return [
            {
                "source":             "OFFLINE_CATALOG_92",
                "description":        "Storeroom validation tightened: storerooms must be ACTIVE and org-linked to create receipts.",
                "functional_area":    "Inventory / Receiving",
                "impacted_workflows": ["pr_to_po"],
                "impact":             "HIGH",
            },
            {
                "source":             "OFFLINE_CATALOG_92",
                "description":        "PO approval now requires organisation-level authorisation in addition to site-level.",
                "functional_area":    "Procurement / P2P",
                "impacted_workflows": ["pr_to_po"],
                "impact":             "HIGH",
            },
            {
                "source":             "OFFLINE_CATALOG_92",
                "description":        "Invoice 3-way match (PO-Receipt-Invoice) is now the default for all purchase orders.",
                "functional_area":    "Finance / Invoice",
                "impacted_workflows": ["pr_to_po"],
                "impact":             "HIGH",
            },
            {
                "source":             "OFFLINE_CATALOG_92",
                "description":        "Work Order approver name now logged in WOAPPROVAL audit table.",
                "functional_area":    "Work Order",
                "impacted_workflows": ["work_order"],
                "impact":             "LOW",
            },
            {
                "source":             "OFFLINE_CATALOG_92",
                "description":        "Asset operating status requires explicit confirmation before DECOMMISSIONED transition.",
                "functional_area":    "Asset Management",
                "impacted_workflows": ["asset_management"],
                "impact":             "LOW",
            },
        ]

    def _classify_area(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["requisition", "purchase order", "procurement", "invoice", "vendor"]):
            return "Procurement / P2P"
        if any(k in t for k in ["receiving", "receipt", "storeroom"]):
            return "Inventory / Receiving"
        if any(k in t for k in ["work order", "workorder", "wappr"]):
            return "Work Order"
        if any(k in t for k in ["preventive", "pm ", "job plan"]):
            return "Preventive Maintenance"
        if any(k in t for k in ["asset", "location", "hierarchy"]):
            return "Asset Management"
        if any(k in t for k in ["service request", "sr ", "ticket"]):
            return "Service Request"
        if any(k in t for k in ["field", "screen", "page", "button", "ui ", "interface"]):
            return "UI / Interface"
        return "General"

    def _map_to_workflows(self, text: str) -> list:
        t = text.lower()
        found = set()
        for kw, wf in KEYWORD_WORKFLOW_MAP.items():
            if kw in t:
                found.add(wf)
        return sorted(found)

    # =========================================================================
    # SOURCE 2 -- Live Maximo Schema Diff (MCP / OSLC)
    # =========================================================================

    def fetch_live_schema(self, object_structure: str) -> Optional[dict]:
        """
        Query the live Maximo OSLC API to get current fields for an object.
        This is the MCP Pattern -- using live system state as intelligence.
        """
        try:
            url = f"{MAXIMO_API_ENDPOINT}/os/{object_structure}"
            resp = requests.get(
                url,
                params={"oslc.pageSize": "1", "lean": "1", "oslc.select": "*"},
                headers=self.headers,
                verify=VERIFY_SSL,
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                members = resp.json().get("member", [])
                if members:
                    fields = sorted([
                        k for k in members[0].keys()
                        if not k.startswith("_") and k != "href"
                    ])
                    return {
                        "object_structure": object_structure.upper(),
                        "fields":           fields,
                        "field_count":      len(fields),
                        "queried_at":       datetime.now().isoformat(),
                    }
        except Exception as e:
            print(f"  [Scout] Schema query failed ({object_structure}): {e}")
        return None

    def diff_schema(self, object_structure: str) -> dict:
        """
        Compare the live schema against the stored baseline.

        First run:  saves baseline, returns status=BASELINE_SAVED
        Later runs: diffs live vs baseline, returns new/removed fields
        """
        BASELINE_DIR.mkdir(parents=True, exist_ok=True)
        baseline_file = BASELINE_DIR / f"{object_structure.lower()}_schema.json"

        live = self.fetch_live_schema(object_structure)
        if not live:
            return {
                "object_structure": object_structure.upper(),
                "status":           "UNREACHABLE",
                "changes":          [],
                "has_breaking_changes": False,
            }

        if baseline_file.exists():
            baseline      = json.loads(baseline_file.read_text(encoding="utf-8"))
            baseline_set  = set(baseline.get("fields", []))
            live_set      = set(live["fields"])

            new_fields     = sorted(live_set - baseline_set)
            removed_fields = sorted(baseline_set - live_set)

            changes = []
            for f in new_fields:
                changes.append({
                    "type":   "NEW_FIELD",
                    "field":  f,
                    "impact": "MEDIUM",
                    "note":   f"New field '{f}' -- add assertions if business-critical",
                })
            for f in removed_fields:
                changes.append({
                    "type":   "REMOVED_FIELD",
                    "field":  f,
                    "impact": "HIGH",
                    "note":   f"Removed field '{f}' -- tests referencing this WILL FAIL",
                })

            result = {
                "object_structure":    object_structure.upper(),
                "status":              "DIFFED",
                "baseline_fields":     len(baseline_set),
                "live_fields":         len(live_set),
                "new_fields":          new_fields,
                "removed_fields":      removed_fields,
                "changes":             changes,
                "has_breaking_changes": bool(removed_fields),
            }

            if new_fields or removed_fields:
                print(f"  [Scout] {object_structure.upper()}: "
                      f"+{len(new_fields)} new field(s), "
                      f"-{len(removed_fields)} removed field(s)")
            else:
                print(f"  [Scout] {object_structure.upper()}: "
                      f"schema unchanged ({len(live_set)} fields)")

            # Refresh baseline to current state
            baseline_file.write_text(json.dumps(live, indent=2), encoding="utf-8")
            return result

        # No baseline yet -- save it now
        baseline_file.write_text(json.dumps(live, indent=2), encoding="utf-8")
        print(f"  [Scout] {object_structure.upper()}: "
              f"baseline saved ({live['field_count']} fields) -- "
              f"diff available on next run")
        return {
            "object_structure": object_structure.upper(),
            "status":           "BASELINE_SAVED",
            "field_count":      live["field_count"],
            "fields":           live["fields"],
            "changes":          [],
            "has_breaking_changes": False,
            "note": "First run -- baseline saved. Run again after upgrade to diff.",
        }

    # =========================================================================
    # SOURCE 3 -- Domain / Lookup Value Diff (MCP)
    # =========================================================================

    def fetch_domain_values(self, domain_id: str) -> list:
        """
        Query MXDOMAIN to get the current valid values for a status domain.
        If values change between runs it signals a new/removed status code.
        """
        try:
            url = f"{MAXIMO_API_ENDPOINT}/os/mxdomain"
            resp = requests.get(
                url,
                params={
                    "oslc.where":    f'domainid="{domain_id}"',
                    "oslc.select":   "domainid,value,description",
                    "oslc.pageSize": "100",
                    "lean":          "1",
                },
                headers=self.headers,
                verify=VERIFY_SSL,
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                members = resp.json().get("member", [])
                return sorted([m.get("value", "") for m in members if m.get("value")])
        except Exception:
            pass
        return []

    def diff_domain(self, domain_id: str) -> dict:
        """Compare live domain values against baseline."""
        BASELINE_DIR.mkdir(parents=True, exist_ok=True)
        baseline_file = BASELINE_DIR / f"domain_{domain_id.lower()}.json"

        live_values = self.fetch_domain_values(domain_id)

        if baseline_file.exists():
            baseline_values = json.loads(baseline_file.read_text(encoding="utf-8"))
            new_values      = sorted(set(live_values) - set(baseline_values))
            removed_values  = sorted(set(baseline_values) - set(live_values))

            if new_values or removed_values:
                print(f"  [Scout] Domain {domain_id}: "
                      f"+{len(new_values)} new value(s), "
                      f"-{len(removed_values)} removed value(s)")
            else:
                print(f"  [Scout] Domain {domain_id}: "
                      f"unchanged ({len(live_values)} values): {live_values}")

            baseline_file.write_text(json.dumps(live_values), encoding="utf-8")
            return {
                "domain_id":      domain_id,
                "live_values":    live_values,
                "new_values":     new_values,
                "removed_values": removed_values,
                "has_changes":    bool(new_values or removed_values),
            }

        baseline_file.write_text(json.dumps(live_values), encoding="utf-8")
        print(f"  [Scout] Domain {domain_id}: baseline saved {live_values or '(empty/unavailable)'}")
        return {
            "domain_id":      domain_id,
            "live_values":    live_values,
            "new_values":     [],
            "removed_values": [],
            "has_changes":    False,
            "note":           "First run -- baseline saved",
        }

    # =========================================================================
    # Main entry point
    # =========================================================================

    def scout(self, ibm_docs_url: str = IBM_DOCS_92_URL) -> dict:
        """
        Run all three intelligence sources and return a unified change report
        that Agent 1 (Requirement Analyser) consumes instead of the hardcoded catalog.
        """
        print(f"\n{'='*60}")
        print(f"  [Agent 0 - Upgrade Scout]")
        print(f"{'='*60}")
        print(f"  Gathering real upgrade intelligence from 3 sources...")

        # Source 1: IBM Docs
        print()
        print("  [1/3] IBM Docs What's New (real URL)...")
        ibm_changes = self.scrape_ibm_whats_new(ibm_docs_url)

        # Source 2: Schema diffs
        print()
        print("  [2/3] Live Maximo schema diff (MCP / OSLC)...")
        schema_diffs = [self.diff_schema(os) for os in SCHEMA_STRUCTURES]

        # Source 3: Domain diffs
        print()
        print("  [3/3] Domain / status code diff (MCP)...")
        domain_diffs = [self.diff_domain(d) for d in DOMAINS_TO_CHECK]

        # Aggregate impacted workflows
        impacted = set()
        for change in ibm_changes:
            impacted.update(change.get("impacted_workflows", []))
        for diff in schema_diffs:
            if diff.get("has_breaking_changes") or diff.get("new_fields"):
                wf = SCHEMA_WORKFLOW_MAP.get(diff["object_structure"].lower())
                if wf:
                    impacted.add(wf)

        report = {
            "success":             True,
            "scouted_at":          datetime.now().isoformat(),
            "ibm_docs_url":        ibm_docs_url,
            "ibm_docs_changes":    ibm_changes,
            "ibm_docs_count":      len(ibm_changes),
            "schema_diffs":        schema_diffs,
            "domain_diffs":        domain_diffs,
            "impacted_workflows":  sorted(impacted),
            "total_change_signals": (
                len(ibm_changes)
                + sum(len(d.get("changes", [])) for d in schema_diffs)
                + sum(1 for d in domain_diffs if d.get("has_changes"))
            ),
        }

        print(f"\n  [Scout] Intelligence summary:")
        print(f"     IBM Docs items    : {len(ibm_changes)}")
        schema_changes = sum(len(d.get("changes", [])) for d in schema_diffs)
        print(f"     Schema changes    : {schema_changes}")
        domain_changes = sum(1 for d in domain_diffs if d.get("has_changes"))
        print(f"     Domain changes    : {domain_changes}")
        print(f"     Impacted workflows: {sorted(impacted) or 'none detected yet'}")

        # Save report for Agent 1 to consume
        out = ROOT_DIR / "reports" / "upgrade_scout_report.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\n  [Scout] Report saved: {out.name}")

        return report


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    scout  = UpgradeScout()
    report = scout.scout()
    # Print summary (not the full IBM docs list)
    summary = {
        k: v for k, v in report.items()
        if k not in ("ibm_docs_changes", "schema_diffs", "domain_diffs")
    }
    print(f"\n  Summary:")
    print(json.dumps(summary, indent=2))

# Made with IBM Bob 2.0
