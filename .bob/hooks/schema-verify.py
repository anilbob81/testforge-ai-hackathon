#!/usr/bin/env python3
"""
TestForge AI — Maximo Schema Verifier
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IBM Bob 2.0 Hackathon — IBM TechXchange 2026 Dev Day

Purpose:
  Verify that the Maximo instance is reachable and the key API schemas
  are responding correctly before running the full test pipeline.

  This is a SENSOR — it observes system state AFTER config changes
  and before committing to a test run.

Usage:
  python .bob/hooks/schema-verify.py

Exit codes:
  0 — Maximo reachable, schemas available, GO for test run
  1 — Connection failed or schemas unavailable, NO-GO
"""

import sys
import json
import urllib3
from pathlib import Path

# Suppress SSL warnings for self-signed certs (common in Maximo demo environments)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

ERRORS = []
WARNINGS = []

def check_pass(desc: str) -> None:
    print(f"  [OK]  {desc}")

def check_fail(desc: str, detail: str = "") -> None:
    msg = f"  [FAIL] {desc}"
    if detail:
        msg += f"\n    --> {detail}"
    ERRORS.append(msg)
    print(msg)

def check_warn(desc: str, detail: str = "") -> None:
    msg = f"  [WARN] {desc}"
    if detail:
        msg += f"\n    --> {detail}"
    WARNINGS.append(msg)
    print(msg)


print()
print("=" * 58)
print("  [PROBE] TestForge AI -- Maximo Schema Verifier")
print("  IBM Bob 2.0 -- Pre-run connectivity probe")
print("=" * 58)
print()

# ── Load config ───────────────────────────────────────────────────────────────
try:
    from config.agent_config import (
        MAXIMO_API_ENDPOINT, API_KEY, API_KEY_HEADER,
        SITE_ID, ORGANIZATION, VERIFY_SSL, REQUEST_TIMEOUT,
    )
    check_pass(f"Config loaded -- SITE={SITE_ID}, ORG={ORGANIZATION}")
except Exception as e:
    check_fail(f"Cannot load config: {e}", "Check config/agent_config.py")
    sys.exit(1)

print()

# ── Try importing requests ────────────────────────────────────────────────────
try:
    import requests
    check_pass("requests library available")
except ImportError:
    check_fail("requests library not installed",
               "Run: pip install requests")
    sys.exit(1)

print()

# ── Check 1: Basic connectivity (schema endpoint) ────────────────────────────
print("[ Check 1 ] Maximo API basic connectivity")
HEADERS = {API_KEY_HEADER: API_KEY, "Accept": "application/json"}

try:
    url = f"{MAXIMO_API_ENDPOINT}/os/mxwo"
    params = {
        "oslc.select": "wonum,status",
        "oslc.pageSize": "1",
        "lean": "1",
    }
    resp = requests.get(
        url, params=params, headers=HEADERS,
        verify=VERIFY_SSL, timeout=REQUEST_TIMEOUT
    )

    if resp.status_code == 200:
        check_pass(f"Maximo API reachable — HTTP 200 ({url[:60]}...)")
    elif resp.status_code == 401:
        check_fail("Maximo returned HTTP 401 — authentication failed",
                   "Verify API_KEY in config/agent_config.py is current")
    elif resp.status_code == 403:
        check_fail("Maximo returned HTTP 403 — authorisation denied",
                   "Check API key permissions in Maximo user profile")
    else:
        check_warn(f"Maximo returned HTTP {resp.status_code}",
                   "Unexpected status — pipeline may still work, proceed with caution")

except requests.exceptions.ConnectionError as e:
    check_fail("Cannot connect to Maximo",
               f"Check network/VPN and MAXIMO_API_ENDPOINT in config. Error: {str(e)[:80]}")
except requests.exceptions.Timeout:
    check_fail(f"Maximo connection timed out after {REQUEST_TIMEOUT}s",
               "Maximo may be under load. Try again or increase REQUEST_TIMEOUT.")
except Exception as e:
    check_fail(f"Unexpected error: {str(e)[:80]}")

print()

# ── Check 2: Key object structures respond ────────────────────────────────────
print("[ Check 2 ] Object structure availability")

SCHEMAS_TO_CHECK = [
    ("mxwo",             "wonum",      "Work Order"),
    ("mxasset",          "assetnum",   "Asset"),
    ("mxpr",             "prnum",      "Purchase Requisition"),
    ("mxpo",             "ponum",      "Purchase Order"),
    ("mxsr",             "ticketid",   "Service Request"),
]

for os_name, select_field, label in SCHEMAS_TO_CHECK:
    try:
        url = f"{MAXIMO_API_ENDPOINT}/os/{os_name}"
        params = {
            "oslc.select": select_field,
            "oslc.pageSize": "1",
            f"oslc.where": f'siteid="{SITE_ID}"',
            "lean": "1",
        }
        resp = requests.get(
            url, params=params, headers=HEADERS,
            verify=VERIFY_SSL, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 200:
            data = resp.json()
            count = len(data.get("member", []))
            check_pass(f"{os_name} ({label}) -- available, {count} record(s) in BEDFORD")
        elif resp.status_code == 404:
            check_warn(f"{os_name} ({label}) -- object structure not found",
                       "Ensure the object structure is enabled in Maximo")
        else:
            check_warn(f"{os_name} ({label}) -- HTTP {resp.status_code}",
                       "Non-200 response, may indicate config issue")
    except Exception as e:
        check_warn(f"{os_name} ({label}) -- check failed: {str(e)[:60]}")

print()

# ── Check 3: Site and Org exist ───────────────────────────────────────────────
print("[ Check 3 ] Site and Organisation configuration")

try:
    # Check site
    url = f"{MAXIMO_API_ENDPOINT}/os/mxsite"
    params = {"oslc.where": f'siteid="{SITE_ID}"', "oslc.select": "siteid,description",
              "lean": "1", "oslc.pageSize": "1"}
    resp = requests.get(url, params=params, headers=HEADERS,
                        verify=VERIFY_SSL, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 200 and resp.json().get("member"):
        site = resp.json()["member"][0]
        check_pass(f"Site '{SITE_ID}' found -- {site.get('description', '')}")
    elif resp.status_code == 200:
        check_warn(f"Site '{SITE_ID}' not found in Maximo",
                   "Verify SITE_ID in config/agent_config.py matches your Maximo environment")
    else:
        check_warn(f"Could not check site (HTTP {resp.status_code})")
except Exception as e:
    check_warn(f"Site check failed: {str(e)[:60]}")

print()

# ── Summary ───────────────────────────────────────────────────────────────────
print("=" * 58)
if ERRORS:
    print(f"\n  [FAIL] Schema verification FAILED -- {len(ERRORS)} error(s)")
    print("  NO-GO: Fix connection/auth issues before running tests.\n")
    sys.exit(1)
elif WARNINGS:
    print(f"\n  [WARN] Schema verification passed with {len(WARNINGS)} warning(s)")
    print("  PROCEED WITH CAUTION: Some checks were inconclusive.")
    print("  Run: python orchestrator.py --workflow api_only --no-email\n")
    sys.exit(0)
else:
    print(f"\n  [PASS] Maximo schema verification PASSED")
    print(f"  GO: Maximo is reachable and key schemas are responding.")
    print(f"  Safe to run: python orchestrator.py --workflow <name>\n")
    sys.exit(0)
