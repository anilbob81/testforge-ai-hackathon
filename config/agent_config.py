"""
Maximo AI Agent — Configuration
Points to the existing regression project for test execution.
Does NOT import from the existing project — paths are resolved at runtime.
"""

import os
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────
# Locate the existing regression project (sibling folder)
THIS_DIR       = Path(__file__).parent.parent           # maximo-ai-agent/
PROJECT_ROOT   = THIS_DIR.parent / "maximo-regression-tests"
TESTS_API_DIR  = PROJECT_ROOT / "tests" / "api"
TESTS_UI_DIR   = PROJECT_ROOT / "tests" / "ui"
FRAMEWORK_DOC  = PROJECT_ROOT / "MAXIMO_TEST_AUTOMATION_FRAMEWORK.md"
REPORTS_DIR    = THIS_DIR / "reports"
LOGS_DIR       = THIS_DIR / "logs"

# ── Maximo connection (mirrors existing config — no import needed) ─────────────
MAXIMO_BASE_URL      = "https://nexersno.manage.nexersno.apps.demo1.nexersaas.com/maximo"
MAXIMO_API_ENDPOINT  = "https://nexersno-all.manage.nexersno.apps.demo1.nexersaas.com/maximo/api"
API_KEY              = "93j95oinsg888u6loq6s9j42fopjvr7m9v2emuvb"
API_KEY_HEADER       = "apikey"
SITE_ID              = "BEDFORD"
ORGANIZATION         = "EAGLENA"
VERIFY_SSL           = False
REQUEST_TIMEOUT      = 30

# ── Email (mirrors existing scheduler/email_config.py) ────────────────────────
EMAIL_CONFIG = {
    "smtp_server":      "smtp.gmail.com",
    "smtp_port":        587,
    "use_tls":          True,
    "sender_email":     "anilbob80@gmail.com",
    "sender_password":  "kqqnkoexpwpnrbbr",
    "recipients":       ["anil.dontaraju@nexergroup.com"],
}

# ── Agent behaviour ───────────────────────────────────────────────────────────
# Average manual testing time (hours) saved per test type — used in report
MANUAL_HOURS_PER_API_TEST = 0.25   # 15 min manual effort per API test
MANUAL_HOURS_PER_UI_TEST  = 0.75   # 45 min manual effort per UI test

# ── watsonx.ai (IBM Granite) ──────────────────────────────────────────────────
# Credentials from the IBM TechXchange Hackathon watsonx challenge account
# Account: watsonx (557f160a7c2d4b739a1fa02315d6fb85b) — Frankfurt region
WATSONX_API_KEY    = "xYxhLsnl8fHOpMJgG-AwV-iIxVohSM_pTD-L75HM7x_i"
WATSONX_URL        = "https://us-south.ml.cloud.ibm.com"   # watsonx-Hackathon WML is Dallas
WATSONX_PROJECT_ID = "b4fae006-1edf-4d97-92e5-2f156c99adc7"  # TestForgeAI-Dallas (us-south)

# Model to use — IBM Granite instruct (best for classification + structured output)
# Fallback order: granite-3-8b-instruct → granite-13b-instruct-v2
WATSONX_MODEL_ID   = "ibm/granite-3-8b-instruct"

# Inference parameters
WATSONX_MAX_TOKENS = 400
WATSONX_TEMPERATURE = 0.0   # Deterministic — classification must be consistent

# Made with IBM Bob 2.0
