#!/usr/bin/env python3
"""
TestForge AI — Pre-commit Quality Gate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IBM Bob 2.0 Hackathon — IBM TechXchange 2026 Dev Day

Purpose:
  Machine-runnable quality gate that runs before every Git commit.
  Blocks commits that would break the pipeline or violate project rules.

  This is a BOB SENSOR — it observes AFTER Bob acts, providing feedback
  that feeds back into the Explore → Plan → Implement → Verify loop.

Usage:
  python .bob/hooks/pre-commit.py

Exit codes:
  0 — All gates passed, commit allowed
  1 — One or more gates failed, commit blocked
"""

import sys
import json
import subprocess
from pathlib import Path

# Project root is 3 levels up from .bob/hooks/pre-commit.py
ROOT = Path(__file__).parent.parent.parent
ERRORS = []
WARNINGS = []


def check_pass(desc: str) -> None:
    print(f"  [OK]  {desc}")


def check_fail(desc: str, fix: str = "") -> None:
    msg = f"  [FAIL] {desc}"
    if fix:
        msg += f"\n    --> Fix: {fix}"
    ERRORS.append(msg)
    print(msg)


def check_warn(desc: str, fix: str = "") -> None:
    msg = f"  [WARN] {desc}"
    if fix:
        msg += f"\n    --> Tip: {fix}"
    WARNINGS.append(msg)
    print(msg)


print()
print("=" * 58)
print("  [GATE] TestForge AI -- Pre-commit Quality Gate")
print("  IBM Bob 2.0 -- Sensor layer (Feedback)")
print("=" * 58)
print()

# ── Gate 1: workflow_map.json must be valid JSON ──────────────────────────────
print("[ Gate 1 ] workflow_map.json integrity")
wmap_path = ROOT / "workflow_map.json"
try:
    wmap = json.loads(wmap_path.read_text(encoding="utf-8"))
    check_pass("workflow_map.json is valid JSON")

    if "workflows" not in wmap:
        check_fail("workflow_map.json missing 'workflows' key",
                   "Add top-level 'workflows' key to workflow_map.json")
    else:
        check_pass("workflow_map.json has 'workflows' key")

    # Every workflow must have required fields
    required_fields = ["description", "business_process", "api_tests",
                       "ui_tests", "manual_hours_equivalent", "priority"]
    valid_priorities = {"critical", "high", "medium", "low"}
    for wf_name, wf_def in wmap.get("workflows", {}).items():
        missing = [f for f in required_fields if f not in wf_def]
        if missing:
            check_fail(
                f"Workflow '{wf_name}' missing fields: {missing}",
                f"Add required fields to workflow '{wf_name}' in workflow_map.json"
            )
        elif wf_def.get("priority") not in valid_priorities:
            check_fail(
                f"Workflow '{wf_name}' has invalid priority '{wf_def.get('priority')}'",
                f"Priority must be one of: {valid_priorities}"
            )
        else:
            check_pass(f"Workflow '{wf_name}' definition is valid")

except json.JSONDecodeError as e:
    check_fail("workflow_map.json has JSON syntax error", f"Fix JSON: {e}")
except FileNotFoundError:
    check_fail("workflow_map.json not found",
               f"Create workflow_map.json in {ROOT}")

print()

# ── Gate 2: Protection — no maximo-regression-tests/ changes staged ───────────
print("[ Gate 2 ] Existing test suite protection")
try:
    staged_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=ROOT
    )
    staged_files = staged_result.stdout.splitlines()
    regression_changes = [f for f in staged_files if "maximo-regression-tests" in f]

    if regression_changes:
        check_fail(
            f"BLOCKED: {len(regression_changes)} file(s) in maximo-regression-tests/ are staged",
            f"Unstage them: git reset HEAD " + " ".join(regression_changes)
        )
    else:
        check_pass("No changes staged in maximo-regression-tests/ (protected)")
except Exception as e:
    check_warn(f"Could not check staged files: {e}", "Run manually: git diff --cached --name-only")

print()

# ── Gate 3: All agent files must compile ─────────────────────────────────────
print("[ Gate 3 ] Agent syntax check (all agent_0*.py files)")
agents_dir = ROOT / "agents"
agent_files = sorted(agents_dir.glob("agent_0*.py"))

if not agent_files:
    check_warn("No agent files found in agents/", "Verify agents/ directory exists")
else:
    for agent_file in agent_files:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(agent_file)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            check_pass(f"{agent_file.name} — syntax OK")
        else:
            check_fail(
                f"{agent_file.name} — syntax error",
                result.stderr.strip() or "Run: python -m py_compile " + str(agent_file)
            )

print()

# ── Gate 4: Additional Python files must compile ──────────────────────────────
print("[ Gate 4 ] Core module syntax check")
for pyfile in [
    ROOT / "orchestrator.py",
    ROOT / "reporter" / "report_builder.py",
    ROOT / "config" / "agent_config.py",
]:
    if not pyfile.exists():
        check_warn(f"{pyfile.name} — not found (skipping)")
        continue
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(pyfile)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        check_pass(f"{pyfile.name} — syntax OK")
    else:
        check_fail(
            f"{pyfile.name} — syntax error",
            result.stderr.strip()
        )

print()

# ── Gate 5: config/agent_config.py must define required keys ──────────────────
print("[ Gate 5 ] Configuration completeness")
try:
    sys.path.insert(0, str(ROOT))
    # Import fresh to avoid cached module
    import importlib
    import config.agent_config as _cfg
    importlib.reload(_cfg)

    required_config = {
        "MAXIMO_BASE_URL": str,
        "API_KEY": str,
        "SITE_ID": str,
        "ORGANIZATION": str,
        "EMAIL_CONFIG": dict,
        "REPORTS_DIR": object,
        "LOGS_DIR": object,
    }

    for key, expected_type in required_config.items():
        value = getattr(_cfg, key, None)
        if value is None:
            check_fail(f"agent_config.py missing: {key}",
                       f"Add {key} to config/agent_config.py")
        elif not isinstance(value, expected_type):
            check_fail(f"agent_config.py: {key} has wrong type (expected {expected_type.__name__})")
        elif not value:
            check_warn(f"agent_config.py: {key} is empty",
                       f"Set a value for {key} in config/agent_config.py")
        else:
            check_pass(f"agent_config.py: {key} — configured")

    # Check EMAIL_CONFIG sub-keys
    email_cfg = getattr(_cfg, "EMAIL_CONFIG", {})
    for sub_key in ["smtp_server", "sender_email", "recipients"]:
        if not email_cfg.get(sub_key):
            check_warn(f"EMAIL_CONFIG.{sub_key} is empty",
                       f"Set {sub_key} in EMAIL_CONFIG dict")

except Exception as e:
    check_fail(f"config/agent_config.py is not importable: {e}")

print()

# ── Gate 6: Bob layer files exist ─────────────────────────────────────────────
print("[ Gate 6 ] Bob layer integrity (.bob/ files)")
bob_files = {
    ".bob/custom_modes.yaml": "4 custom modes",
    ".bob/rules.md": "project rules and quality gates",
    ".bob/skills/requirement-analyser/SKILL.md": "requirement analyser skill",
    ".bob/skills/test-planner/SKILL.md": "test planner skill",
    ".bob/skills/failure-investigator/SKILL.md": "failure investigator skill",
    ".bob/skills/regression-impact/SKILL.md": "regression impact skill",
    ".bob/skills/test-data-validator/SKILL.md": "test data validator skill",
}
for rel_path, desc in bob_files.items():
    full_path = ROOT / rel_path
    if full_path.exists():
        check_pass(f"{rel_path} — present ({desc})")
    else:
        check_warn(f"{rel_path} — missing",
                   f"Create {rel_path} to enable {desc}")

print()

# ── Gate 7: hackathon/ submission folder ─────────────────────────────────────
print("[ Gate 7 ] Hackathon submission folder")
hackathon_files = [
    "hackathon/ONBOARDING.md",
    "hackathon/AGENTS.md",
    "hackathon/PLAN.md",
    "hackathon/github-issue-P2P-001.md",
    "hackathon/demo-script.md",
]
for rel_path in hackathon_files:
    full_path = ROOT / rel_path
    if full_path.exists():
        check_pass(f"{rel_path} -- present")
    else:
        check_warn(f"{rel_path} -- missing (required for submission)")

print()

# ── Final Result ──────────────────────────────────────────────────────────────
print("=" * 58)
if ERRORS:
    print(f"\n  [FAIL] Quality gate FAILED -- {len(ERRORS)} error(s) found")
    print("  Commit BLOCKED. Fix the errors above before committing.\n")
    if WARNINGS:
        print(f"  [WARN] {len(WARNINGS)} warning(s) -- review when possible\n")
    sys.exit(1)
else:
    if WARNINGS:
        print(f"\n  [WARN] {len(WARNINGS)} warning(s) -- not blocking, review when possible")
    print(f"\n  [PASS] All quality gates passed -- commit allowed!")
    print(f"  TestForge AI pipeline integrity confirmed.\n")
    sys.exit(0)
