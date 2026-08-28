"""
Agent 1 - Requirement Analyser
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  • Reads the MAXIMO_TEST_AUTOMATION_FRAMEWORK.md (Document Understanding)
  • Reads workflow_map.json to resolve the requested workflow
  • Returns a structured analysis: which tests to run, business context, priority
  • Simulates what a Bob subagent does - isolated analysis, returns a summary

Bob 2.0 Feature Demonstrated: Document Understanding + Subagent pattern
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────
AGENT_DIR  = Path(__file__).parent
ROOT_DIR   = AGENT_DIR.parent
CONFIG_DIR = ROOT_DIR / "config"
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import FRAMEWORK_DOC, PROJECT_ROOT


class RequirementAnalyser:
    """
    Agent 1 - Reads framework documentation and maps a workflow name
    to the concrete test files that cover it.

    Demonstrates IBM Bob 2.0 Document Understanding:
    - Reads the 67-page MAXIMO_TEST_AUTOMATION_FRAMEWORK.md
    - Extracts relevant sections for the requested workflow
    - Returns structured analysis for downstream agents
    """

    def __init__(self, workflow_map_path: Path):
        self.workflow_map_path = workflow_map_path
        self._workflow_map = None

    def _load_workflow_map(self) -> dict:
        if self._workflow_map is None:
            with open(self.workflow_map_path) as f:
                self._workflow_map = json.load(f)
        return self._workflow_map

    def _extract_framework_context(self, workflow_name: str) -> str:
        """
        Read the framework document and extract the section most relevant
        to the requested workflow. Demonstrates Document Understanding.
        """
        if not FRAMEWORK_DOC.exists():
            return "Framework document not found - proceeding with workflow map only."

        try:
            content = FRAMEWORK_DOC.read_text(encoding="utf-8")
            lines   = content.split("\n")
            # Extract sections relevant to the workflow keyword
            keywords = {
                "pr_to_po":        ["procurement", "purchase", "P2P", "requisition", "receipt", "invoice"],
                "work_order":      ["work order", "WO", "WAPPR", "APPR", "INPRG", "COMP"],
                "pm_maintenance":  ["preventive", "PM", "job plan", "generate work"],
                "asset_management":["asset", "location", "hierarchy", "operating"],
                "service_request": ["service request", "SR", "affected person"],
                "wo_from_jobplan": ["job plan", "tasks", "WOACTIVITY"],
                "api_only":        ["API", "OSLC", "REST", "object structure"],
                "full_regression": ["regression", "full suite", "all modules"],
            }
            relevant_keywords = keywords.get(workflow_name, [workflow_name])

            excerpts = []
            for i, line in enumerate(lines):
                if any(kw.lower() in line.lower() for kw in relevant_keywords):
                    start = max(0, i - 1)
                    end   = min(len(lines), i + 3)
                    excerpts.append(" | ".join(lines[start:end]).strip())
                if len(excerpts) >= 8:
                    break

            return "\n".join(excerpts) if excerpts else f"Workflow '{workflow_name}' documented in framework."
        except Exception as e:
            return f"Could not read framework doc: {e}"

    def analyse(self, workflow_name: str) -> dict:
        """
        Main entry point - analyse the requested workflow.

        Returns a structured analysis dict consumed by Agent 2 (Strategist).
        """
        print(f"\n{'='*60}")
        print(f"  [Agent 1 - Requirement Analyser]")
        print(f"{'='*60}")
        print(f"  Reading: MAXIMO_TEST_AUTOMATION_FRAMEWORK.md")
        print(f"  Reading: workflow_map.json")
        print(f"  Analysing workflow: '{workflow_name}'")

        wmap = self._load_workflow_map()
        workflows = wmap.get("workflows", {})

        # Validate workflow exists
        if workflow_name not in workflows:
            available = list(workflows.keys())
            print(f"\n  [FAIL] Unknown workflow '{workflow_name}'")
            print(f"  Available: {', '.join(available)}")
            return {
                "success": False,
                "error": f"Unknown workflow '{workflow_name}'. Available: {available}",
                "workflow_name": workflow_name,
            }

        workflow_def = workflows[workflow_name]

        # Extract framework doc context (Document Understanding)
        doc_context = self._extract_framework_context(workflow_name)

        # Resolve full paths relative to the existing regression project
        api_tests = [
            str(PROJECT_ROOT / t)
            for t in workflow_def.get("api_tests", [])
            if (PROJECT_ROOT / t).exists()
        ]
        ui_tests = [
            str(PROJECT_ROOT / t)
            for t in workflow_def.get("ui_tests", [])
            if (PROJECT_ROOT / t).exists()
        ]

        # Warn about any test files not found
        missing_api = [t for t in workflow_def.get("api_tests", []) if not (PROJECT_ROOT / t).exists()]
        missing_ui  = [t for t in workflow_def.get("ui_tests",  []) if not (PROJECT_ROOT / t).exists()]
        if missing_api or missing_ui:
            print(f"  [WARN]️  Missing test files: {missing_api + missing_ui}")

        analysis = {
            "success":              True,
            "workflow_name":        workflow_name,
            "description":          workflow_def["description"],
            "business_process":     workflow_def["business_process"],
            "priority":             workflow_def["priority"],
            "manual_hours_equivalent": workflow_def["manual_hours_equivalent"],
            "api_test_files":       api_tests,
            "ui_test_files":        ui_tests,
            "api_test_count_approx": len(api_tests) * 5,   # ~5 tests per module
            "ui_test_count_approx":  len(ui_tests)  * 6,   # ~6 tests per UI module
            "doc_context_excerpt":  doc_context,
            "analysed_at":          datetime.now().isoformat(),
        }

        print(f"\n  [OK] Analysis complete:")
        print(f"     Business process : {workflow_def['business_process'][:70]}...")
        print(f"     API test files   : {len(api_tests)} modules -> ~{analysis['api_test_count_approx']} tests")
        print(f"     UI test files    : {len(ui_tests)} modules  -> ~{analysis['ui_test_count_approx']} tests")
        print(f"     Manual effort    : {workflow_def['manual_hours_equivalent']}h equivalent")
        print(f"     Priority         : {workflow_def['priority'].upper()}")

        return analysis


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    workflow = sys.argv[1] if len(sys.argv) > 1 else "pr_to_po"
    wmap_path = ROOT_DIR / "workflow_map.json"
    analyser  = RequirementAnalyser(wmap_path)
    result    = analyser.analyse(workflow)
    print(f"\n  Full analysis result:")
    print(json.dumps(result, indent=2))

# Made with IBM Bob 2.0
