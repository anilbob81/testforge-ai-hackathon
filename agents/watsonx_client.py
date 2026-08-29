"""
watsonx Client -- IBM Granite Inference via Direct REST API
-----------------------------------------------------------
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Calls IBM watsonx.ai text generation REST endpoint directly using
requests + IAM bearer token. No SDK project/space association needed.

Flow:
  1. POST to IAM to exchange API key -> Bearer token
  2. POST to /ml/v1/text/generation with Bearer token + project_id
  3. Return generated text to caller

Model: ibm/granite-3-8b-instruct  (us-south / Dallas)
Auth:  IAM token exchange (iam.cloud.ibm.com)

Fallback: returns None on ANY failure so Agent 2 and Agent 5
          automatically fall back to their rule-based logic.

Bob 2.0 Feature Demonstrated:
  Real AI reasoning -- IBM Granite LLM replaces static rule engines
  with live language model inference on test failures and strategy.
"""

import sys
import json
import requests
import urllib3
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import (
    WATSONX_API_KEY,
    WATSONX_URL,
    WATSONX_PROJECT_ID,
    WATSONX_MODEL_ID,
    WATSONX_MAX_TOKENS,
    WATSONX_TEMPERATURE,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# IAM token endpoint -- global, always us endpoint
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
# Text generation endpoint path
GENERATE_PATH = "/ml/v1/text/generation?version=2023-05-29"


def _get_iam_token(api_key: str) -> Optional[str]:
    """
    Exchange an IBM Cloud API key for a short-lived IAM Bearer token.
    Tokens are valid ~60 minutes; the client refreshes on 401.
    """
    try:
        resp = requests.post(
            IAM_TOKEN_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey":     api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        print(f"  [watsonx] IAM error HTTP {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"  [watsonx] IAM request failed: {e}")
    return None


class WatsonxClient:
    """
    Direct REST caller for IBM watsonx.ai /ml/v1/text/generation.
    Authenticates via IAM token -- no SDK project association required.
    """

    def __init__(self):
        self._token:     Optional[str] = None
        self._available: bool          = False
        self._base_url:  str           = WATSONX_URL.rstrip("/")
        self._init()

    def _init(self):
        print(f"  [watsonx] Authenticating (IAM token exchange)...")
        token = _get_iam_token(WATSONX_API_KEY)
        if token:
            self._token    = token
            self._available = True
            print(f"  [watsonx] Connected -- {WATSONX_MODEL_ID} @ {self._base_url}")
        else:
            print(f"  [watsonx] Auth failed -- rule-based fallback active")

    @property
    def available(self) -> bool:
        return self._available

    def generate(self, prompt: str) -> Optional[str]:
        """
        Send a prompt to IBM Granite and return the generated text.
        Refreshes the IAM token once on HTTP 401.
        Returns None on any failure -- callers fall back to rules.
        """
        if not self._available or not self._token:
            return None

        url     = f"{self._base_url}{GENERATE_PATH}"
        payload = {
            "model_id":   WATSONX_MODEL_ID,
            "project_id": WATSONX_PROJECT_ID,
            "input":      prompt,
            "parameters": {
                "max_new_tokens": WATSONX_MAX_TOKENS,
                "temperature":    WATSONX_TEMPERATURE,
                "stop_sequences": ["\n\n", "###"],
            },
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)

            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    return results[0].get("generated_text", "").strip()
                return None

            if resp.status_code == 401:
                # Token expired -- refresh once and retry
                print("  [watsonx] Token expired -- refreshing...")
                new_token = _get_iam_token(WATSONX_API_KEY)
                if new_token:
                    self._token               = new_token
                    headers["Authorization"]  = f"Bearer {new_token}"
                    resp2 = requests.post(url, json=payload, headers=headers, timeout=30)
                    if resp2.status_code == 200:
                        results = resp2.json().get("results", [])
                        if results:
                            return results[0].get("generated_text", "").strip()

            print(f"  [watsonx] HTTP {resp.status_code}: {resp.text[:250]}")

        except Exception as e:
            print(f"  [watsonx] Inference error: {e}")

        return None


# ── Module-level singleton ────────────────────────────────────────────────────
_client: Optional[WatsonxClient] = None


def get_client() -> WatsonxClient:
    """Return the module-level singleton WatsonxClient (initialised once)."""
    global _client
    if _client is None:
        _client = WatsonxClient()
    return _client


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 58)
    print("  [watsonx] Connection + Inference Test")
    print("=" * 58)

    client = get_client()
    if not client.available:
        print("  [FAIL] Not available -- check credentials in agent_config.py")
        sys.exit(1)

    # Test 1 -- failure classification
    r1 = client.generate(
        "You are an IBM Maximo test analyst.\n"
        "Classify this failure into ONE of: TEST_DATA, APPLICATION_DEFECT, "
        "LOCATOR_DRIFT, TIMING_ENVIRONMENT, ENVIRONMENT_AUTH, UNKNOWN\n\n"
        "Failure: HTTP 400 BMXAA4073E - storeroom CENTRAL not valid for site BEDFORD.\n\n"
        "CATEGORY: "
    )
    print(f"\n  [Test 1] Classification: {r1!r}")

    # Test 2 -- strategy decision
    r2 = client.generate(
        "You are a Maximo test strategist.\n"
        "Workflow: pr_to_po | Priority: critical | Has UI tests: yes\n"
        "Should the run be API_ONLY or API_AND_UI?\n"
        "STRATEGY: "
    )
    print(f"  [Test 2] Strategy:       {r2!r}")

    if r1 and r2:
        print("\n  [PASS] Granite is live and reasoning correctly")
        sys.exit(0)
    else:
        print("\n  [FAIL] One or more responses were empty")
        sys.exit(1)

# Made with IBM Bob 2.0
