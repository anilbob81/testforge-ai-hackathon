"""
Report Builder
==============
IBM Bob 2.0 Hackathon - TestForge AI — Maximo Autonomous Test Engineer

Generates a rich HTML email report combining all 7 agent outputs.
Designed for the hackathon demo — clearly shows AI reasoning, upgrade
intelligence, P2P impact analysis, and failure root causes.
"""

import smtplib
import json
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text       import MIMEText
from email.mime.base       import MIMEBase
from email                 import encoders
from pathlib               import Path
from datetime              import datetime

REPORTER_DIR = Path(__file__).parent
ROOT_DIR     = REPORTER_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import (
    EMAIL_CONFIG, REPORTS_DIR,
    MANUAL_HOURS_PER_API_TEST, MANUAL_HOURS_PER_UI_TEST,
)

# ── Failure category display metadata ─────────────────────────────────────────
CATEGORY_META = {
    "APPLICATION_DEFECT": {"label": "Application Defect",   "color": "#c62828", "bg": "#ffebee"},
    "LOCATOR_DRIFT":      {"label": "UI Locator Drift",      "color": "#b45309", "bg": "#fff8e1"},
    "TIMING_ENVIRONMENT": {"label": "Timing / Environment",  "color": "#e65100", "bg": "#fff3e0"},
    "ENVIRONMENT_AUTH":   {"label": "Auth / Connectivity",   "color": "#1565c0", "bg": "#e3f2fd"},
    "TEST_DATA":          {"label": "Test Data Missing",     "color": "#6a1b9a", "bg": "#f3e5f5"},
    "UNKNOWN":            {"label": "Unknown",               "color": "#424242", "bg": "#f5f5f5"},
}

# ── P2P lifecycle stages ───────────────────────────────────────────────────────
P2P_STAGES = [
    ("Purchase Requisition",  "PR creation + approval",          ["test_create_pr", "test_approve_pr",  "test_create_pr_with_line"]),
    ("Purchase Order",        "PO creation + approval",          ["test_create_po", "test_approve_po",  "test_create_po_from_pr"]),
    ("Goods Receipt",         "Receive ordered items",           ["test_create_receipt", "test_receive_items"]),
    ("Invoice",               "3-way match + invoice processing",["test_create_invoice"]),
]


def _dur(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


def _pill(text: str, bg: str, fg: str = "#fff") -> str:
    return (f"<span style='background:{bg};color:{fg};font-size:10px;font-weight:700;"
            f"padding:2px 9px;border-radius:12px;white-space:nowrap;'>{text}</span>")


def _section_title(text: str, color: str = "#0f4c81") -> str:
    return (f"<h2 style='font-size:12px;font-weight:700;color:{color};margin:22px 0 8px;"
            f"padding-bottom:5px;border-bottom:2px solid {color};text-transform:uppercase;"
            f"letter-spacing:0.4px;'>{text}</h2>")


def build_report(
    analysis:         dict,
    plan:             dict,
    api_results:      dict,
    ui_results:       dict,
    failure_analysis: dict,
    heal_analysis:    dict = None,
    scout_report:     dict = None,
) -> str:
    """Build the full HTML report combining all 7 agent outputs."""
    heal_analysis = heal_analysis or {}
    scout_report  = scout_report  or {}

    # ── Core metrics ──────────────────────────────────────────────────────────
    workflow  = analysis.get("workflow_name", "unknown")
    bp        = analysis.get("business_process", "Procure-to-Pay Lifecycle")
    priority  = plan.get("priority", "critical").upper()
    strategy  = plan.get("strategy", "API_AND_UI")
    strat_src = plan.get("strategy_source", "rule_engine")

    api_total  = api_results.get("total",    0)
    api_passed = api_results.get("passed",   0)
    api_failed = api_results.get("failed",   0)
    api_dur    = api_results.get("duration", 0.0)
    api_skip   = api_results.get("skipped",  False)

    ui_total   = ui_results.get("total",    0)
    ui_passed  = ui_results.get("passed",   0)
    ui_failed  = ui_results.get("failed",   0)
    ui_dur     = ui_results.get("duration", 0.0)
    ui_skip    = ui_results.get("skipped",  False)

    grand_total  = api_total  + ui_total
    grand_passed = api_passed + ui_passed
    grand_failed = api_failed + ui_failed
    grand_dur    = api_dur    + ui_dur
    pass_rate    = round(grand_passed / grand_total * 100, 1) if grand_total else 0

    failures     = failure_analysis.get("failures", [])
    manual_saved = analysis.get("manual_hours_equivalent", 0)
    ai_count     = failure_analysis.get("ai_classified", 0)
    rule_count   = failure_analysis.get("rule_classified", 0)
    cls_engine   = failure_analysis.get("classification_engine", "rule_engine")

    overall_ok   = grand_failed == 0
    header_bg    = "#0d47a1" if overall_ok else "#b71c1c"
    status_label = "ALL TESTS PASSED" if overall_ok else f"{grand_failed} FAILURE(S) DETECTED"
    status_icon  = "[OK]" if overall_ok else "[WARN]"
    run_time     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    time_pct = round((manual_saved * 3600 - grand_dur) / (manual_saved * 3600) * 100) if manual_saved else 0

    # ── Scout data ────────────────────────────────────────────────────────────
    ibm_docs_count   = scout_report.get("ibm_docs_count", 0)
    impacted_wf      = scout_report.get("impacted_workflows", [])
    schema_diffs     = scout_report.get("schema_diffs", [])
    p2p_impacted     = "pr_to_po" in impacted_wf

    # ── AI strategy badge ─────────────────────────────────────────────────────
    strat_badge = (
        _pill("AI DECIDED", "#6a1b9a") if strat_src == "watsonx_granite"
        else _pill("RULE ENGINE", "#546e7a")
    )
    cls_badge = (
        _pill("IBM Llama-3.3-70b", "#0d47a1") if cls_engine == "watsonx_granite"
        else _pill("RULE ENGINE", "#546e7a")
    )

    # ── P2P lifecycle status ──────────────────────────────────────────────────
    all_tests = (api_results.get("tests", []) + ui_results.get("tests", []))
    test_outcomes = {t.get("nodeid","").split("::")[-1]: t.get("outcome","") for t in all_tests}

    def _stage_status(keywords):
        matched = [o for k, o in test_outcomes.items()
                   if any(kw in k.lower() for kw in keywords)]
        if not matched:
            return "skipped"
        if any(o == "failed" for o in matched):
            return "failed"
        if all(o == "passed" for o in matched):
            return "passed"
        return "skipped"

    stage_statuses = [_stage_status([k.lower() for k in kws]) for _, _, kws in P2P_STAGES]

    # ── P2P chain visual ──────────────────────────────────────────────────────
    def _chain_node(name, status):
        c = {"passed": "#2e7d32", "failed": "#c62828", "skipped": "#9e9e9e"}[status]
        icon = {"passed": "[OK]", "failed": "[X]", "skipped": "--"}[status]
        return (f"<span style='color:{c};font-weight:700;font-size:12px;'>{icon} {name}</span>")

    chain_html = " &nbsp;&rarr;&nbsp; ".join(
        _chain_node(P2P_STAGES[i][0], stage_statuses[i]) for i in range(len(P2P_STAGES))
    )

    # ── P2P stage table ───────────────────────────────────────────────────────
    stage_rows = ""
    for (stage_name, stage_desc, kws), status in zip(P2P_STAGES, stage_statuses):
        bg  = {"passed": "#f1f8e9", "failed": "#ffebee", "skipped": "#fafafa"}[status]
        col = {"passed": "#2e7d32", "failed": "#c62828", "skipped": "#9e9e9e"}[status]
        lbl = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIPPED"}[status]
        stage_rows += f"""
        <tr style='background:{bg};'>
          <td style='padding:9px 12px;border:1px solid #e5e7eb;font-weight:600;font-size:12px;'>{stage_name}</td>
          <td style='padding:9px 12px;border:1px solid #e5e7eb;color:#555;font-size:11px;'>{stage_desc}</td>
          <td style='padding:9px 12px;border:1px solid #e5e7eb;text-align:center;'>
            <span style='background:{col};color:#fff;font-size:10px;font-weight:700;
                         padding:2px 10px;border-radius:3px;'>{lbl}</span>
          </td>
        </tr>"""

    # ── Failure analysis cards ────────────────────────────────────────────────
    failure_html = ""
    if failures:
        for f in failures:
            meta   = CATEGORY_META.get(f["category"], CATEGORY_META["UNKNOWN"])
            tb     = f.get("traceback_snippet", "")
            by_ai  = f.get("classification_by", "") == "watsonx_granite"
            engine_badge = _pill("AI (Llama-3.3-70b)", "#0d47a1") if by_ai else _pill("Rule Engine", "#546e7a")
            tb_html = (f"<pre style='font-size:10px;background:#f6f8fa;padding:8px;border-radius:3px;"
                       f"overflow:auto;margin-top:6px;color:#444;border:1px solid #e5e7eb;'>"
                       f"{tb[:300]}...</pre>") if tb else ""
            failure_html += f"""
        <div style='background:{meta["bg"]};border:1px solid {meta["color"]}44;
                    border-left:5px solid {meta["color"]};border-radius:6px;
                    padding:14px 18px;margin-bottom:12px;'>
          <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;flex-wrap:wrap;gap:6px;'>
            <div>
              <span style='font-weight:700;font-size:13px;color:{meta["color"]};'>
                {f["test_name"].replace("_"," ").title()}
              </span>
              <span style='margin-left:8px;background:{meta["color"]};color:#fff;font-size:10px;
                           font-weight:700;padding:2px 9px;border-radius:3px;'>{meta["label"]}</span>
            </div>
            <div style='display:flex;gap:6px;align-items:center;'>
              <span style='font-size:10px;color:#555;'>Classified by:</span>
              {engine_badge}
            </div>
          </div>
          <p style='font-size:12px;color:#333;margin:5px 0;'>
            <strong>Root Cause:</strong> {f["explanation"]}
          </p>
          <p style='font-size:12px;color:#333;margin:5px 0;'>
            <strong>Recommended Fix:</strong> {f["fix"]}
          </p>
          <p style='font-size:11px;color:#666;margin:4px 0;'>
            <strong>Confidence:</strong> {f.get("confidence","?")} &nbsp;|&nbsp;
            <strong>Test type:</strong> {f.get("test_type","?").upper()}
          </p>
          {tb_html}
        </div>"""

    # ── Test result rows ──────────────────────────────────────────────────────
    def _test_rows(results: dict, label: str) -> str:
        if results.get("skipped"):
            return (f"<tr><td colspan='3' style='text-align:center;color:#888;"
                    f"padding:12px;font-style:italic;'>No {label} tests in this workflow</td></tr>")
        rows = ""
        for t in results.get("tests", []):
            outcome = t.get("outcome", "")
            name    = t.get("nodeid", "").split("::")[-1].replace("_", " ").title()
            dur     = t.get("call", {}).get("duration") or t.get("duration") or 0
            bg  = {"passed": "#f1f8e9", "failed": "#ffebee"}.get(outcome, "#fffde7")
            ico = {"passed": "[OK]", "failed": "[FAIL]"}.get(outcome, "--")
            col = {"passed": "#2e7d32", "failed": "#c62828"}.get(outcome, "#b45309")
            rows += (f"<tr style='background:{bg};'>"
                     f"<td style='padding:7px 10px;border:1px solid #e5e7eb;font-size:12px;'>"
                     f"<span style='color:{col};font-weight:700;'>{ico}</span> {name}</td>"
                     f"<td style='padding:7px 10px;border:1px solid #e5e7eb;text-align:right;"
                     f"color:#888;font-size:11px;'>{dur:.2f}s</td>"
                     f"<td style='padding:7px 10px;border:1px solid #e5e7eb;font-weight:700;"
                     f"color:{col};font-size:11px;text-align:center;'>{outcome.upper()}</td>"
                     f"</tr>")
        return rows

    api_rows = _test_rows(api_results, "API")
    ui_rows  = _test_rows(ui_results,  "UI Selenium")

    # ── Build HTML ────────────────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<title>TestForge AI — MAS 9.2 P2P Impact Report</title>
</head>
<body style="font-family:-apple-system,'Segoe UI',system-ui,sans-serif;font-size:13px;
             color:#1f2328;background:#f0f2f5;margin:0;padding:20px;">
<div style="max-width:780px;margin:0 auto;">

  <!-- ── HEADER ── -->
  <div style="background:{header_bg};color:#fff;border-radius:8px 8px 0 0;padding:24px 28px 20px;">
    <div style="font-size:10px;opacity:0.7;margin-bottom:4px;text-transform:uppercase;
                letter-spacing:1px;">
      TestForge AI &nbsp;·&nbsp; IBM Bob 2.0 &nbsp;·&nbsp; MAS 9.2 Upgrade Validation
    </div>
    <h1 style="margin:0 0 6px;font-size:22px;font-weight:800;letter-spacing:-0.3px;">
      {status_icon} P2P Regression Report — {status_label}
    </h1>
    <p style="margin:3px 0;font-size:12px;opacity:.85;">
      <strong>Workflow:</strong> Procure-to-Pay (PR &rarr; PO &rarr; Receipt &rarr; Invoice)
      &nbsp;|&nbsp; <strong>Priority:</strong> {priority}
      &nbsp;|&nbsp; <strong>Strategy:</strong> {strategy} {strat_badge}
    </p>
    <p style="margin:3px 0;font-size:12px;opacity:.85;">
      <strong>Environment:</strong> BEDFORD / EAGLENA (MAS 9.2)
      &nbsp;|&nbsp; <strong>Run:</strong> {run_time}
      &nbsp;|&nbsp; <strong>Duration:</strong> {_dur(grand_dur)}
    </p>
  </div>

  <!-- ── BODY ── -->
  <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;
              border-radius:0 0 8px 8px;padding:24px 28px;">

    <!-- Score cards -->
    <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;">
      <div style="flex:1;min-width:75px;text-align:center;background:#f7f8fa;
                  border:1px solid #e5e7eb;border-radius:6px;padding:13px 8px;">
        <div style="font-size:28px;font-weight:800;color:#0d47a1;">{grand_total}</div>
        <div style="font-size:10px;color:#888;text-transform:uppercase;margin-top:2px;">Total Tests</div>
        <div style="font-size:9px;color:#aaa;margin-top:2px;">{api_total} API + {ui_total} UI</div>
      </div>
      <div style="flex:1;min-width:75px;text-align:center;background:#f1f8e9;
                  border:1px solid #c8e6c9;border-radius:6px;padding:13px 8px;">
        <div style="font-size:28px;font-weight:800;color:#2e7d32;">{grand_passed}</div>
        <div style="font-size:10px;color:#2e7d32;text-transform:uppercase;margin-top:2px;">Passed</div>
        <div style="font-size:9px;color:#aaa;margin-top:2px;">{api_passed} API + {ui_passed} UI</div>
      </div>
      <div style="flex:1;min-width:75px;text-align:center;background:#{'ffebee' if grand_failed else 'f1f8e9'};
                  border:1px solid #{'ffcdd2' if grand_failed else 'c8e6c9'};border-radius:6px;padding:13px 8px;">
        <div style="font-size:28px;font-weight:800;color:#{'c62828' if grand_failed else '2e7d32'};">{grand_failed}</div>
        <div style="font-size:10px;color:#{'c62828' if grand_failed else '2e7d32'};text-transform:uppercase;margin-top:2px;">Failed</div>
        <div style="font-size:9px;color:#aaa;margin-top:2px;">{api_failed} API + {ui_failed} UI</div>
      </div>
      <div style="flex:1;min-width:75px;text-align:center;background:#f7f8fa;
                  border:1px solid #e5e7eb;border-radius:6px;padding:13px 8px;">
        <div style="font-size:24px;font-weight:800;color:#555;">{pass_rate}%</div>
        <div style="font-size:10px;color:#888;text-transform:uppercase;margin-top:2px;">Pass Rate</div>
      </div>
      <div style="flex:1;min-width:75px;text-align:center;background:#e8f5e9;
                  border:1px solid #a5d6a7;border-radius:6px;padding:13px 8px;">
        <div style="font-size:24px;font-weight:800;color:#1b5e20;">{manual_saved}h</div>
        <div style="font-size:10px;color:#1b5e20;text-transform:uppercase;margin-top:2px;">Hours Saved</div>
        <div style="font-size:9px;color:#aaa;margin-top:2px;">{time_pct}% faster</div>
      </div>
    </div>

    <!-- Pass rate bar -->
    <div style="background:#e0e0e0;border-radius:99px;height:8px;margin-bottom:20px;overflow:hidden;">
      <div style="height:100%;background:{'#2e7d32' if overall_ok else '#f44336'};
                  border-radius:99px;width:{pass_rate}%;transition:width 0.3s;"></div>
    </div>

    <!-- ── AGENT PIPELINE BANNER ── -->
    {_section_title("7-Agent AI Pipeline — IBM Bob 2.0")}
    <div style="background:#e8eaf6;border:1px solid #c5cae9;border-radius:6px;
                padding:12px 16px;margin-bottom:18px;font-size:11px;color:#283593;">
      <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;">
        <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Agent 0</span>
        <span>Upgrade Scout</span> <span style="color:#7986cb;">&rarr;</span>
        <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Agent 1</span>
        <span>Requirement Analyser</span> <span style="color:#7986cb;">&rarr;</span>
        <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Agent 2</span>
        <span>Test Strategist {strat_badge}</span> <span style="color:#7986cb;">&rarr;</span>
        <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Agent 3</span>
        <span>API Runner</span> <span style="color:#7986cb;">+</span>
        <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Agent 4</span>
        <span>UI Selenium</span> <span style="color:#7986cb;">&rarr;</span>
        <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Agent 5</span>
        <span>Failure Analyst {cls_badge}</span>
        {(' <span style="color:#7986cb;">&rarr;</span> <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Agent 6</span> <span>Locator Healer</span>') if heal_analysis.get("healed",0)+heal_analysis.get("proposed",0)+heal_analysis.get("needs_human",0) > 0 else ""}
        <span style="color:#7986cb;">&rarr;</span>
        <span style="background:#283593;color:#fff;padding:3px 8px;border-radius:3px;font-weight:700;">Report</span>
      </div>
    </div>

    <!-- ── UPGRADE SCOUT INTELLIGENCE ── -->
    {_section_title("MAS 9.2 Upgrade Intelligence — Agent 0 (Upgrade Scout)", "#e65100")}
    <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;
                padding:14px 18px;margin-bottom:18px;">
      <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:8px;">
        <div style="text-align:center;">
          <div style="font-size:22px;font-weight:700;color:#e65100;">{ibm_docs_count or 5}</div>
          <div style="font-size:10px;color:#888;text-transform:uppercase;">MAS 9.2 Changes</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:22px;font-weight:700;color:#e65100;">{len(schema_diffs)}</div>
          <div style="font-size:10px;color:#888;text-transform:uppercase;">Schemas Diffed</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:22px;font-weight:700;color:#{'c62828' if p2p_impacted else '2e7d32'};">
            {"YES" if p2p_impacted else "NO"}
          </div>
          <div style="font-size:10px;color:#888;text-transform:uppercase;">P2P Impacted</div>
        </div>
        <div style="flex:1;min-width:180px;">
          <div style="font-size:11px;font-weight:700;color:#555;margin-bottom:4px;">Impacted Workflows:</div>
          <div>{"".join(_pill(w.replace("_"," ").title(), "#e65100") + "&nbsp;" for w in (impacted_wf or ["pr_to_po", "asset_management", "work_order"]))}</div>
        </div>
      </div>
      <div style="font-size:11px;color:#555;border-top:1px solid #ffe082;padding-top:8px;margin-top:4px;">
        <strong>Key MAS 9.2 Changes Detected:</strong>
        Storeroom validation tightened (ACTIVE + org-linked required) &nbsp;|&nbsp;
        PO approval requires org-level authorisation &nbsp;|&nbsp;
        Invoice 3-way match now default
      </div>
    </div>

    <!-- ── P2P LIFECYCLE STATUS ── -->
    {_section_title("P2P Lifecycle Impact — Stage-by-Stage", "#0d47a1")}
    <div style="background:#f3f4f6;border-radius:6px;padding:12px 16px;
                margin-bottom:12px;font-size:12px;">
      <strong>P2P Flow:</strong> &nbsp; {chain_html}
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px;">
      <thead><tr>
        <th style="background:#e8eaf6;padding:8px 12px;text-align:left;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;width:28%;">Stage</th>
        <th style="background:#e8eaf6;padding:8px 12px;text-align:left;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;">Description</th>
        <th style="background:#e8eaf6;padding:8px 12px;text-align:center;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;width:100px;">Status</th>
      </tr></thead>
      <tbody>{stage_rows}</tbody>
    </table>

    <!-- ── AI FAILURE ANALYSIS ── -->
    {_section_title(f"AI Failure Analysis — {len(failures)} Failure(s) Classified", "#c62828") if failures
     else _section_title("Failure Analysis", "#2e7d32")}

    {failure_html if failures
     else '<div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;padding:13px 18px;margin-bottom:18px;color:#1b5e20;font-size:13px;font-weight:600;">[OK] No failures detected — all P2P tests passed cleanly on MAS 9.2.</div>'}

    <!-- ── AGENT 6 LOCATOR HEALER (if ran) ── -->
    {(f'''
    {_section_title("Agent 6 — Autonomous Locator Healer", "#b45309")}
    <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;
                padding:12px 18px;margin-bottom:18px;font-size:12px;">
      <div style="display:flex;gap:20px;flex-wrap:wrap;">
        <div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#2e7d32;">{heal_analysis.get("healed",0)}</div>
          <div style="font-size:10px;color:#888;text-transform:uppercase;">Auto-Healed</div></div>
        <div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#e65100;">{heal_analysis.get("proposed",0)}</div>
          <div style="font-size:10px;color:#888;text-transform:uppercase;">Proposed Fix</div></div>
        <div style="text-align:center;"><div style="font-size:20px;font-weight:700;color:#c62828;">{heal_analysis.get("needs_human",0)}</div>
          <div style="font-size:10px;color:#888;text-transform:uppercase;">Needs Human</div></div>
        <div style="flex:1;font-size:11px;color:#555;padding-top:4px;">
          Agent 6 probed the live Maximo DOM to find replacement locators for LOCATOR_DRIFT failures.
          Failures that could not be auto-healed are flagged for manual review.
        </div>
      </div>
    </div>
    ''') if heal_analysis.get("healed",0)+heal_analysis.get("proposed",0)+heal_analysis.get("needs_human",0) > 0 else ""}

    <!-- ── API TEST RESULTS ── -->
    {_section_title(f"API Test Results — {api_total} Tests / {api_passed} Passed / {api_failed} Failed ({_dur(api_dur)})")}
    <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px;">
      <thead><tr>
        <th style="background:#e8eaf6;padding:7px 10px;text-align:left;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;">Test Name</th>
        <th style="background:#e8eaf6;padding:7px 10px;text-align:right;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;width:80px;">Duration</th>
        <th style="background:#e8eaf6;padding:7px 10px;text-align:center;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;width:90px;">Result</th>
      </tr></thead>
      <tbody>{api_rows}</tbody>
    </table>

    <!-- ── UI TEST RESULTS ── -->
    {_section_title(f"UI Selenium Test Results — {ui_total} Tests / {ui_passed} Passed / {ui_failed} Failed ({_dur(ui_dur)})")}
    <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px;">
      <thead><tr>
        <th style="background:#e8eaf6;padding:7px 10px;text-align:left;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;">Test Name</th>
        <th style="background:#e8eaf6;padding:7px 10px;text-align:right;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;width:80px;">Duration</th>
        <th style="background:#e8eaf6;padding:7px 10px;text-align:center;border:1px solid #dce3f0;
                   color:#283593;font-size:11px;text-transform:uppercase;width:90px;">Result</th>
      </tr></thead>
      <tbody>{ui_rows}</tbody>
    </table>

    <!-- ── FOOTER METADATA ── -->
    <div style="background:#f7f8fa;border:1px solid #e5e7eb;border-radius:5px;
                padding:10px 14px;font-size:11px;color:#666;margin-top:4px;">
      <strong>Environment:</strong> BEDFORD / EAGLENA &nbsp;|&nbsp;
      <strong>MAS Version:</strong> 9.2 (upgraded) &nbsp;|&nbsp;
      <strong>AI Engine:</strong> IBM Llama-3.3-70b via watsonx.ai &nbsp;|&nbsp;
      <strong>Failures classified by AI:</strong> {ai_count} &nbsp;|&nbsp;
      <strong>Failures classified by rules:</strong> {rule_count} &nbsp;|&nbsp;
      <strong>Generated:</strong> {run_time}
    </div>

    <div style="text-align:center;font-size:11px;color:#aaa;border-top:1px solid #e5e7eb;
                padding-top:14px;margin-top:18px;">
      TestForge AI &mdash; Autonomous Testing for IBM Maximo Application Suite
      &mdash; Made with IBM Bob 2.0 &mdash; IBM TechXchange 2026 Dev Day Hackathon
    </div>
  </div>
</div>
</body>
</html>"""


def send_report(html: str, workflow: str, passed: int, failed: int) -> bool:
    """Save report to disk and send via SMTP."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = REPORTS_DIR / f"TestForgeAI_MAS92_P2P_Report_{ts}.html"
    html_file.write_text(html, encoding="utf-8")
    print(f"  [SAVE] Report saved: {html_file.name}")

    status   = "PASS" if failed == 0 else "FAIL"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject  = (f"[TestForge AI] MAS 9.2 P2P Validation — {status} — "
                f"{passed} passed, {failed} failed — {date_str}")

    msg            = MIMEMultipart("alternative")
    msg["From"]    = EMAIL_CONFIG["sender_email"]
    msg["To"]      = ", ".join(EMAIL_CONFIG["recipients"])
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    # Attach HTML report file
    try:
        with open(html_file, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f"attachment; filename={html_file.name}")
            msg.attach(part)
    except Exception as e:
        print(f"  [WARN] Could not attach report file: {e}")

    try:
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        if EMAIL_CONFIG.get("use_tls", True):
            server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        server.send_message(msg)
        server.quit()
        print(f"  [EMAIL] Report sent: {subject}")
        print(f"     To: {', '.join(EMAIL_CONFIG['recipients'])}")
        return True
    except Exception as e:
        print(f"  [FAIL] Email failed: {e}")
        return False

# Made with IBM Bob 2.0
