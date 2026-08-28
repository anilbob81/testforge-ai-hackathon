"""
Report Builder
━━━━━━━━━━━━━━
IBM Bob 2.0 Hackathon - Maximo Autonomous Test Engineer

Responsibility:
  • Combines results from all 5 agents into a final HTML email report
  • Shows: test counts, pass/fail, per-failure root cause + fix, hours saved
  • Sends via SMTP to configured recipients
  • Saves HTML report to reports/ folder

Bob 2.0 Feature Demonstrated: Agent Mode - full report generation + email sending
"""

import smtplib
import json
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

REPORTER_DIR = Path(__file__).parent
ROOT_DIR     = REPORTER_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from config.agent_config import EMAIL_CONFIG, REPORTS_DIR, MANUAL_HOURS_PER_API_TEST, MANUAL_HOURS_PER_UI_TEST

# Category display config
CATEGORY_META = {
    "APPLICATION_DEFECT": {"label": "Application Defect",  "color": "#c62828", "bg": "#ffebee", "icon": "🔴"},
    "LOCATOR_DRIFT":      {"label": "Locator Drift",        "color": "#b45309", "bg": "#fff8e1", "icon": "🟡"},
    "TIMING_ENVIRONMENT": {"label": "Timing / Environment", "color": "#e65100", "bg": "#fff3e0", "icon": "🟠"},
    "ENVIRONMENT_AUTH":   {"label": "Auth / Connectivity",  "color": "#1565c0", "bg": "#e3f2fd", "icon": "🔵"},
    "TEST_DATA":          {"label": "Test Data Missing",    "color": "#6a1b9a", "bg": "#f3e5f5", "icon": "🟣"},
    "UNKNOWN":            {"label": "Unknown - Investigate","color": "#424242", "bg": "#f5f5f5", "icon": "⚪"},
}


def _hours(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


def build_report(
    analysis:         dict,
    plan:             dict,
    api_results:      dict,
    ui_results:       dict,
    failure_analysis: dict,
) -> str:
    """Build the full HTML email report combining all agent outputs."""

    workflow   = analysis.get("workflow_name", "unknown")
    bp         = analysis.get("business_process", "")
    priority   = plan.get("priority", "").upper()

    api_total   = api_results.get("total",   0)
    api_passed  = api_results.get("passed",  0)
    api_failed  = api_results.get("failed",  0)
    api_dur     = api_results.get("duration",0.0)
    api_skip    = api_results.get("skipped", False)

    ui_total    = ui_results.get("total",   0)
    ui_passed   = ui_results.get("passed",  0)
    ui_failed   = ui_results.get("failed",  0)
    ui_dur      = ui_results.get("duration",0.0)
    ui_skip     = ui_results.get("skipped", False)

    grand_total  = api_total  + ui_total
    grand_passed = api_passed + ui_passed
    grand_failed = api_failed + ui_failed
    grand_dur    = api_dur    + ui_dur
    pass_rate    = round(grand_passed / grand_total * 100, 1) if grand_total else 0

    failures     = failure_analysis.get("failures", [])
    manual_saved = analysis.get("manual_hours_equivalent", 0)

    overall_ok   = grand_failed == 0
    header_bg    = "#0f4c81" if overall_ok else "#b71c1c"
    status_label = "ALL TESTS PASSED [OK]" if overall_ok else f"[WARN]️ {grand_failed} FAILURE(S) DETECTED"
    run_time     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Failure cards HTML ────────────────────────────────────────────────────
    failure_html = ""
    if failures:
        failure_html = """
        <h2 style='font-size:13px;font-weight:700;color:#c62828;margin:20px 0 10px;
                   padding-bottom:5px;border-bottom:2px solid #c62828;'>
          [ANALYSE] Failure Analysis - Root Cause per Test
        </h2>"""
        for f in failures:
            meta  = CATEGORY_META.get(f["category"], CATEGORY_META["UNKNOWN"])
            tb    = f.get("traceback_snippet", "")
            tb_html = f"<pre style='font-size:10px;background:#f6f8fa;padding:6px 8px;border-radius:3px;overflow:auto;margin-top:4px;color:#333;'>{tb[:200]}...</pre>" if tb else ""
            failure_html += f"""
        <div style='background:{meta["bg"]};border:1px solid {meta["color"]}33;
                    border-left:4px solid {meta["color"]};border-radius:6px;
                    padding:12px 16px;margin-bottom:10px;'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
            <span style='font-weight:700;font-size:13px;color:{meta["color"]};'>
              {meta["icon"]} {f["test_name"].replace("_"," ").title()}
            </span>
            <span style='background:{meta["color"]};color:#fff;font-size:10px;font-weight:700;
                         padding:2px 10px;border-radius:4px;'>{meta["label"]}</span>
          </div>
          <p style='font-size:12px;color:#333;margin:4px 0;'><strong>Root Cause:</strong> {f["explanation"]}</p>
          <p style='font-size:12px;color:#333;margin:4px 0;'><strong>Suggested Fix:</strong> {f["fix"]}</p>
          {tb_html}
        </div>"""

    # ── Test results rows ─────────────────────────────────────────────────────
    def _test_rows(results: dict, label: str) -> str:
        if results.get("skipped"):
            return f"<tr><td colspan='3' style='text-align:center;color:#888;padding:10px;'>No {label} tests in this workflow</td></tr>"
        rows = ""
        for t in results.get("tests", []):
            outcome = t.get("outcome", "")
            name    = t.get("nodeid", "").split("::")[-1].replace("_", " ").title()
            dur     = t.get("call", {}).get("duration") or t.get("duration") or 0
            bg      = "#f6fff7" if outcome == "passed" else "#fff5f5" if outcome == "failed" else "#fffbf0"
            ico     = "[OK]" if outcome == "passed" else "[FAIL]" if outcome == "failed" else "⏭️"
            col     = "#2e7d32" if outcome == "passed" else "#c62828" if outcome == "failed" else "#b45309"
            rows += (f"<tr style='background:{bg};'>"
                     f"<td style='padding:6px 10px;border:1px solid #e5e7eb;font-size:12px;'>{ico} {name}</td>"
                     f"<td style='padding:6px 10px;border:1px solid #e5e7eb;text-align:right;color:#888;font-size:11px;'>{dur:.2f}s</td>"
                     f"<td style='padding:6px 10px;border:1px solid #e5e7eb;font-weight:600;color:{col};font-size:11px;'>{outcome.upper()}</td>"
                     f"</tr>")
        return rows

    api_rows = _test_rows(api_results, "API")
    ui_rows  = _test_rows(ui_results,  "UI")

    # ── Category summary pills ────────────────────────────────────────────────
    cat_summary = failure_analysis.get("category_summary", {})
    cat_pills   = ""
    for cat, count in cat_summary.items():
        meta      = CATEGORY_META.get(cat, CATEGORY_META["UNKNOWN"])
        cat_pills += (f"<span style='background:{meta['color']};color:#fff;font-size:11px;"
                      f"font-weight:600;padding:3px 10px;border-radius:4px;margin-right:6px;'>"
                      f"{meta['icon']} {meta['label']}: {count}</span>")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,'Segoe UI',system-ui,sans-serif;font-size:13px;
             color:#1f2328;background:#f4f4f4;margin:0;padding:24px;">
<div style="max-width:760px;margin:0 auto;">

  <!-- Header -->
  <div style="background:{header_bg};color:#fff;border-radius:6px 6px 0 0;padding:24px 28px;">
    <div style="font-size:11px;opacity:0.75;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;">
      IBM Bob 2.0 · Maximo Autonomous Test Engineer · Hackathon Demo
    </div>
    <h1 style="margin:0 0 4px;font-size:20px;font-weight:800;">{status_label}</h1>
    <p style="margin:3px 0;font-size:12px;opacity:.85;">
      Workflow: <strong>{workflow.replace("_"," ").title()}</strong>
      &nbsp;|&nbsp; {bp[:60]}...
    </p>
    <p style="margin:3px 0;font-size:12px;opacity:.85;">
      Priority: {priority} &nbsp;|&nbsp; Run: {run_time} &nbsp;|&nbsp; Duration: {_hours(grand_dur)}
    </p>
  </div>

  <!-- Body -->
  <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;
              border-radius:0 0 6px 6px;padding:24px 28px;">

    <!-- Score cards -->
    <div style="display:flex;gap:10px;margin-bottom:18px;flex-wrap:wrap;">
      <div style="flex:1;min-width:70px;text-align:center;background:#f7f8fa;border:1px solid #e5e7eb;border-radius:6px;padding:12px 8px;">
        <div style="font-size:26px;font-weight:700;color:#0f4c81;">{grand_total}</div>
        <div style="font-size:10px;color:#888;text-transform:uppercase;">Total</div>
      </div>
      <div style="flex:1;min-width:70px;text-align:center;background:#f7f8fa;border:1px solid #e5e7eb;border-radius:6px;padding:12px 8px;">
        <div style="font-size:26px;font-weight:700;color:#2e7d32;">{grand_passed}</div>
        <div style="font-size:10px;color:#888;text-transform:uppercase;">Passed</div>
      </div>
      <div style="flex:1;min-width:70px;text-align:center;background:#f7f8fa;border:1px solid #e5e7eb;border-radius:6px;padding:12px 8px;">
        <div style="font-size:26px;font-weight:700;color:#c62828;">{grand_failed}</div>
        <div style="font-size:10px;color:#888;text-transform:uppercase;">Failed</div>
      </div>
      <div style="flex:1;min-width:70px;text-align:center;background:#f7f8fa;border:1px solid #e5e7eb;border-radius:6px;padding:12px 8px;">
        <div style="font-size:22px;font-weight:700;color:#555;">{pass_rate}%</div>
        <div style="font-size:10px;color:#888;text-transform:uppercase;">Pass Rate</div>
      </div>
      <div style="flex:1;min-width:70px;text-align:center;background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;padding:12px 8px;">
        <div style="font-size:22px;font-weight:700;color:#2e7d32;">{manual_saved}h</div>
        <div style="font-size:10px;color:#2e7d32;text-transform:uppercase;">Hours Saved</div>
      </div>
    </div>

    <!-- Pass rate bar -->
    <div style="background:#e0e0e0;border-radius:99px;height:8px;margin-bottom:22px;overflow:hidden;">
      <div style="height:100%;background:#2e7d32;border-radius:99px;width:{pass_rate}%;"></div>
    </div>

    <!-- Agent pipeline banner -->
    <div style="background:#f0f4ff;border:1px solid #dce3f0;border-radius:5px;
                padding:10px 16px;margin-bottom:20px;font-size:12px;color:#0f4c81;">
      <strong>🤖 IBM Bob 2.0 Agent Pipeline:</strong>
      &nbsp; Agent 1 Analyse &rarr; Agent 2 Plan &rarr;
      Agent 3 API Tests &rarr; Agent 4 UI Tests &rarr; Agent 5 Classify &rarr; Report
    </div>

    <!-- Failure analysis -->
    {failure_html if failures else
     '<div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:5px;padding:12px 16px;margin-bottom:20px;color:#1b5e20;font-size:13px;font-weight:600;">[OK] No failures detected - all tests passed cleanly.</div>'}

    {'<div style="margin-bottom:16px;">' + cat_pills + '</div>' if cat_pills else ''}

    <!-- API Test Results -->
    <h2 style="font-size:13px;font-weight:700;color:#0f4c81;margin:20px 0 8px;
               padding-bottom:5px;border-bottom:2px solid #0f4c81;">
      [API] API Test Results
      {'- ' + str(api_total) + ' tests in ' + _hours(api_dur) if not api_skip else '- Not included in this workflow'}
    </h2>
    <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px;">
      <thead><tr>
        <th style="background:#f0f4ff;padding:7px 10px;text-align:left;border:1px solid #dce3f0;color:#0f4c81;font-size:11px;text-transform:uppercase;">Test</th>
        <th style="background:#f0f4ff;padding:7px 10px;text-align:right;border:1px solid #dce3f0;color:#0f4c81;font-size:11px;text-transform:uppercase;">Duration</th>
        <th style="background:#f0f4ff;padding:7px 10px;text-align:left;border:1px solid #dce3f0;color:#0f4c81;font-size:11px;text-transform:uppercase;">Result</th>
      </tr></thead>
      <tbody>{api_rows}</tbody>
    </table>

    <!-- UI Test Results -->
    <h2 style="font-size:13px;font-weight:700;color:#0f4c81;margin:20px 0 8px;
               padding-bottom:5px;border-bottom:2px solid #0f4c81;">
      [UI]️ UI Selenium Test Results
      {'- ' + str(ui_total) + ' tests in ' + _hours(ui_dur) if not ui_skip else '- Not included in this workflow'}
    </h2>
    <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px;">
      <thead><tr>
        <th style="background:#f0f4ff;padding:7px 10px;text-align:left;border:1px solid #dce3f0;color:#0f4c81;font-size:11px;text-transform:uppercase;">Test</th>
        <th style="background:#f0f4ff;padding:7px 10px;text-align:right;border:1px solid #dce3f0;color:#0f4c81;font-size:11px;text-transform:uppercase;">Duration</th>
        <th style="background:#f0f4ff;padding:7px 10px;text-align:left;border:1px solid #dce3f0;color:#0f4c81;font-size:11px;text-transform:uppercase;">Result</th>
      </tr></thead>
      <tbody>{ui_rows}</tbody>
    </table>

    <p style="font-size:11px;color:#888;margin-top:8px;">
      Maximo instance: BEDFORD / EAGLENA &bull;
      Automated by IBM Bob 2.0 &bull; {run_time}
    </p>

    <div style="text-align:center;font-size:11px;color:#888;border-top:1px solid #e5e7eb;
                padding-top:12px;margin-top:16px;">
      IBM Maximo Application Suite &mdash; Autonomous Test Engineer &mdash; Made with IBM Bob 2.0
    </div>
  </div>
</div>
</body>
</html>"""


def send_report(html: str, workflow: str, passed: int, failed: int) -> bool:
    """Send the HTML report via email."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = REPORTS_DIR / f"agent_report_{workflow}_{ts}.html"
    html_file.write_text(html, encoding="utf-8")
    print(f"  [SAVE] Report saved: {html_file.name}")

    status   = "SUCCESS" if failed == 0 else "FAILURE"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject  = f"[Maximo AI Agent] {workflow.replace('_',' ').title()} - {status} - {date_str}"

    msg            = MIMEMultipart()
    msg["From"]    = EMAIL_CONFIG["sender_email"]
    msg["To"]      = ", ".join(EMAIL_CONFIG["recipients"])
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    # Attach HTML report
    try:
        with open(html_file, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={html_file.name}")
            msg.attach(part)
    except Exception as e:
        print(f"  [WARN]️  Could not attach report: {e}")

    try:
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        if EMAIL_CONFIG.get("use_tls", True):
            server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        server.send_message(msg)
        server.quit()
        print(f"  [EMAIL] Email sent to: {', '.join(EMAIL_CONFIG['recipients'])}")
        print(f"     Subject: {subject}")
        return True
    except Exception as e:
        print(f"  [FAIL] Email failed: {e}")
        return False

# Made with IBM Bob 2.0
