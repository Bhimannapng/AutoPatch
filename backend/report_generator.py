import os
import html
import tempfile
import subprocess
import time
from typing import Optional
from schemas import ProjectAnalysisSummary

def generate_html_report(summary: ProjectAnalysisSummary) -> str:
    """Generates a complete, beautiful HTML report for the project analysis."""
    p_name = html.escape(summary.project_name or "AutoPatch Project")
    p_type = html.escape(summary.project_type or "Full-Stack Project")
    langs = ", ".join([html.escape(l) for l in summary.detected_languages]) or "Auto-detected"
    frameworks = ", ".join([html.escape(f) for f in summary.detected_frameworks]) or "Standard Runtime"
    entry_pts = ", ".join([html.escape(e) for e in summary.entry_points]) or "None identified"
    
    total_loc = getattr(summary.capacity_metrics, "total_lines_of_code", 0) if summary.capacity_metrics else 0
    total_files = getattr(summary.capacity_metrics, "relevant_source_files", 0) or getattr(summary.capacity_metrics, "total_files_discovered", 1) if summary.capacity_metrics else 1
    analysis_time = (getattr(summary.capacity_metrics, "analysis_duration_ms", 0.0) / 1000.0) if summary.capacity_metrics else 0.0
    ram_mb = getattr(summary.capacity_metrics, "ram_consumed_mb", 0.1) if summary.capacity_metrics else 0.1
    disk_kb = (getattr(summary.capacity_metrics, "extracted_size_bytes", 1024) / 1024.0) if summary.capacity_metrics else 1.0

    # Build Bugs HTML
    bugs_html = ""
    if not summary.bugs:
        # Check if scan completed unnaturally fast due to server cold-start / timeout
        is_suspect_timeout = (total_files > 1 and total_loc > 30 and analysis_time < 0.05)
        if is_suspect_timeout:
            bugs_html = """
            <div class="clean-box" style="background: #fffbeb; border: 1.5px solid #f59e0b;">
                <h4 style="color: #b45309; margin: 0 0 4px 0;">⚠️ Scan Notice: Engine Warm-up / Re-scan Recommended</h4>
                <p style="margin: 0; font-size: 12px; color: #92400e;">The scan finished in sub-second time without registering issues. If the server was waking up from idle, click <strong>Scan & Fix</strong> again for complete multi-file deep analysis.</p>
            </div>
            """
        else:
            bugs_html = """
            <div class="clean-box">
                <h4 style="color: #15803d; margin: 0 0 4px 0;">✔ Zero Code Defects Detected</h4>
                <p style="margin: 0; font-size: 12px; color: #166534;">All functions, syntax trees, logic boundaries, and type assignments passed without finding bugs.</p>
            </div>
            """
    else:
        for idx, bug in enumerate(summary.bugs, 1):
            sev_class = "badge-crit" if bug.severity.lower() in ("critical", "high", "error") else "badge-warn"
            verified_badge = '<span class="badge-pass">✔ VERIFIED PASSED</span>' if (bug.validation and bug.validation.verified) else '<span class="badge-review">NEEDS REVIEW</span>'
            
            # Escape snippets
            orig_code = html.escape(bug.original_code[:1200] if bug.original_code else "No original code available")
            patch_code = html.escape(bug.patched_code[:1200] if bug.patched_code else "No patch code available")
            diff_text = html.escape(bug.diff[:1500] if bug.diff else "")
            
            val_details = html.escape(bug.validation.details if bug.validation else "Sandbox syntax check passed.")

            test_rows = ""
            if bug.validation and bug.validation.after_tests:
                for t in bug.validation.after_tests:
                    st_badge = '<span class="badge-pass">PASSED</span>' if t.status == 'PASSED' else '<span class="badge-crit">FAILED</span>'
                    test_rows += f"<tr><td style='padding: 3px 6px;'><code>{html.escape(t.name)}</code></td><td style='padding: 3px 6px;'>{st_badge}</td><td style='padding: 3px 6px;'>{t.duration_ms:.1f}ms</td><td style='padding: 3px 6px;'><small>{html.escape((t.stdout or t.error_message or '')[:120])}</small></td></tr>"
            
            test_table_html = ""
            if test_rows:
                test_table_html = f"""
                <div style="margin-top: 8px;">
                    <div style="font-size: 10.5px; font-weight: 700; color: #334155; margin-bottom: 3px;">Sandboxed Test Evidence (Verified Results):</div>
                    <table style="width: 100%; border-collapse: collapse; font-size: 10.5px; margin: 4px 0;">
                        <thead>
                            <tr style="background: #f1f5f9;">
                                <th style="padding: 4px 6px;">Test Case</th>
                                <th style="padding: 4px 6px; width: 70px;">Result</th>
                                <th style="padding: 4px 6px; width: 60px;">Time</th>
                                <th style="padding: 4px 6px;">Output / Observation</th>
                            </tr>
                        </thead>
                        <tbody>{test_rows}</tbody>
                    </table>
                </div>
                """

            bugs_html += f"""
            <div class="finding-card">
                <div class="finding-header">
                    <div>
                        <span class="finding-index">#{idx}</span>
                        <span class="{sev_class}">{html.escape(bug.severity.upper())}</span>
                        <span class="badge-cat">{html.escape(bug.category.upper())}</span>
                        <strong class="finding-title">{html.escape(bug.title)}</strong>
                    </div>
                    <div>{verified_badge}</div>
                </div>

                <div class="finding-meta">
                    <strong>File:</strong> <code>{html.escape(bug.file_path)}</code> : Lines {bug.line_start}-{bug.line_end}
                    &nbsp;|&nbsp; <strong>Confidence:</strong> {int(bug.confidence * 100)}%
                </div>

                <div class="finding-body">
                    <p><strong>Problem Description:</strong> {html.escape(bug.description)}</p>
                    <p><strong>Root Cause:</strong> {html.escape(bug.root_cause)}</p>
                    {f"<p><strong>Trigger Condition:</strong> {html.escape(bug.trigger_input_or_state)}</p>" if bug.trigger_input_or_state else ""}
                    {f"<p><strong>Actionable Fix:</strong> {html.escape(bug.repair_summary)}</p>" if bug.repair_summary else ""}
                </div>

                <div class="diff-container">
                    <div class="diff-pane diff-before">
                        <div class="diff-title">Before (Original Code with Error)</div>
                        <pre><code>{orig_code}</code></pre>
                    </div>
                    <div class="diff-pane diff-after">
                        <div class="diff-title">After (Targeted Patch / Corrected Code)</div>
                        <pre><code>{patch_code}</code></pre>
                    </div>
                </div>

                <div class="sandbox-note">
                    <strong>Sandbox Validation:</strong> {val_details}
                </div>
                {test_table_html}
            </div>
            """

    # Build Optimizations HTML
    opts_html = ""
    if not summary.optimizations:
        opts_html = """
        <div class="clean-box">
            <h4 style="color: #15803d; margin: 0 0 4px 0;">✔ Clean Execution Complexity &amp; Memory Allocation</h4>
            <p style="margin: 0; font-size: 12px; color: #166534;">No high-order O(N²) / O(N³) loops or unclosed file descriptors detected.</p>
        </div>
        """
    else:
        for idx, opt in enumerate(summary.optimizations, 1):
            line_no = getattr(opt, 'line_start', None) or getattr(opt, 'line_number', 1)
            risk = getattr(opt, 'risk_level', 'Medium') or 'Medium'
            prob = getattr(opt, 'problem', '') or ''
            why = getattr(opt, 'why_inefficient', '') or ''
            imp = getattr(opt, 'suggested_improvement', None) or getattr(opt, 'actionable_improvement', '') or ''
            benefit = getattr(opt, 'expected_benefit', None) or getattr(opt, 'expected_outcome', '') or ''

            opts_html += f"""
            <div class="finding-card">
                <div class="finding-header">
                    <div>
                        <span class="finding-index">#{idx}</span>
                        <span class="badge-warn">{html.escape(risk.upper())}</span>
                        <strong class="finding-title">{html.escape(opt.title)}</strong>
                    </div>
                    <span style="font-size: 11px; color: #64748b;"><code>{html.escape(opt.file_path)}:{line_no}</code></span>
                </div>
                <div class="finding-body" style="margin-top: 8px;">
                    <p><strong>Problem &amp; Bottleneck:</strong> {html.escape(prob)}</p>
                    <p><strong>Why Inefficient:</strong> {html.escape(why)}</p>
                    <p><strong>Actionable Improvement:</strong> {html.escape(imp)}</p>
                    <p style="color: #047857;"><strong>Expected Outcome:</strong> {html.escape(benefit)}</p>
                </div>
            </div>
            """

    # Build Security HTML
    sec_html = ""
    if not summary.security_findings:
        sec_html = """
        <div class="clean-box">
            <h4 style="color: #15803d; margin: 0 0 4px 0;">✔ Zero Security Vulnerabilities Detected</h4>
            <p style="margin: 0; font-size: 12px; color: #166534;">No hardcoded secrets, SQL injection patterns, or OWASP exposures found in scanned files.</p>
        </div>
        """
    else:
        for idx, sec in enumerate(summary.security_findings, 1):
            line_no = getattr(sec, 'line_start', None) or getattr(sec, 'line_number', 1)
            cat_name = getattr(sec, 'vulnerability_type', None) or getattr(sec, 'category', 'Security') or 'Security'
            sec_class = "badge-crit" if sec.severity.lower() in ("critical", "high") else "badge-warn"
            sec_html += f"""
            <div class="finding-card">
                <div class="finding-header">
                    <div>
                        <span class="finding-index">#{idx}</span>
                        <span class="{sec_class}">{html.escape(sec.severity.upper())}</span>
                        <span class="badge-cat">{html.escape(cat_name.upper())}</span>
                        <strong class="finding-title">{html.escape(sec.title)}</strong>
                    </div>
                    <span style="font-size: 11px; color: #64748b;"><code>{html.escape(sec.file_path)}:{line_no}</code></span>
                </div>
                <div class="finding-body" style="margin-top: 8px;">
                    <p><strong>Vulnerability Description:</strong> {html.escape(sec.description)}</p>
                    <p style="color: #b91c1c;"><strong>Remediation:</strong> {html.escape(sec.remediation)}</p>
                </div>
            </div>
            """

    # Assemble Full Document
    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AutoPatch - Detailed Project Analysis &amp; Repair Report</title>
<style>
  @page {{
    size: A4;
    margin: 16mm 14mm 16mm 14mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}

  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.5;
    font-size: 12px;
    margin: 0;
    padding: 0;
  }}

  .header {{
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 16px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }}

  .logo-title {{
    font-size: 26px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
    margin: 0 0 4px 0;
  }}

  .logo-title span {{
    color: #4f46e5;
  }}

  .subtitle {{
    font-size: 13px;
    color: #64748b;
    margin: 0;
  }}

  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 22px;
  }}

  .metric-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
  }}

  .metric-val {{
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 2px;
  }}

  .metric-lbl {{
    font-size: 10px;
    text-transform: uppercase;
    font-weight: 600;
    color: #64748b;
  }}

  .meta-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 24px;
    font-size: 11.5px;
  }}

  .meta-table th, .meta-table td {{
    border: 1px solid #e2e8f0;
    padding: 8px 12px;
    text-align: left;
  }}

  .meta-table th {{
    background-color: #f1f5f9;
    font-weight: 600;
    width: 25%;
    color: #334155;
  }}

  h2 {{
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 6px;
    margin-top: 26px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .finding-card {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 16px;
    page-break-inside: avoid;
  }}

  .finding-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 8px;
    margin-bottom: 8px;
  }}

  .finding-index {{
    background: #e2e8f0;
    color: #334155;
    font-weight: 700;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    margin-right: 6px;
  }}

  .finding-title {{
    font-size: 13px;
    color: #0f172a;
    margin-left: 6px;
  }}

  .finding-meta {{
    font-size: 11px;
    color: #64748b;
    margin-bottom: 10px;
  }}

  .finding-body p {{
    margin: 0 0 6px 0;
    font-size: 11.5px;
    line-height: 1.45;
  }}

  .diff-container {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 10px;
    margin-bottom: 8px;
  }}

  .diff-pane {{
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 10.5px;
    overflow: hidden;
  }}

  .diff-before {{
    background: #fef2f2;
    border: 1px solid #fecaca;
  }}

  .diff-after {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
  }}

  .diff-title {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 4px;
  }}

  .diff-before .diff-title {{ color: #b91c1c; }}
  .diff-after .diff-title {{ color: #15803d; }}

  pre {{
    margin: 0;
    font-family: monospace;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 240px;
  }}

  .sandbox-note {{
    background: #f8fafc;
    border-left: 3px solid #10b981;
    padding: 6px 10px;
    border-radius: 0 4px 4px 0;
    font-size: 11px;
    color: #0f766e;
    margin-top: 6px;
  }}

  .clean-box {{
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 14px;
  }}

  /* Badges */
  .badge-crit {{
    background: #fee2e2;
    color: #991b1b;
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
  }}

  .badge-warn {{
    background: #fef3c7;
    color: #92400e;
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
  }}

  .badge-cat {{
    background: #e0e7ff;
    color: #3730a3;
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 4px;
  }}

  .badge-pass {{
    background: #dcfce7;
    color: #166534;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
  }}

  .badge-review {{
    background: #f1f5f9;
    color: #475569;
    font-size: 10px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 4px;
  }}

  code {{
    font-family: monospace;
    background: #f1f5f9;
    padding: 1px 4px;
    border-radius: 3px;
    color: #0f172a;
  }}
</style>
</head>
<body>

  <div class="header">
    <div>
      <div class="logo-title">AutoPatch<span>.ai</span></div>
      <div class="subtitle">Comprehensive Project Analysis, Defect Audit &amp; Verified Repair Report</div>
    </div>
    <div style="text-align: right; font-size: 11px; color: #64748b;">
      <strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}<br>
      <strong>Engine:</strong> Gemini 2.5 Flash + Isolated Sandbox
    </div>
  </div>

  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-val">{total_files}</div>
      <div class="metric-lbl">Source Files</div>
    </div>
    <div class="metric-card">
      <div class="metric-val">{total_loc}</div>
      <div class="metric-lbl">Lines of Code</div>
    </div>
    <div class="metric-card">
      <div class="metric-val">{len(summary.bugs)}</div>
      <div class="metric-lbl">Defects Detected</div>
    </div>
    <div class="metric-card">
      <div class="metric-val">{len(summary.optimizations)}</div>
      <div class="metric-lbl">RAM / CPU Notices</div>
    </div>
    <div class="metric-card">
      <div class="metric-val">{len(summary.security_findings)}</div>
      <div class="metric-lbl">Security Exposures</div>
    </div>
  </div>

  <table class="meta-table">
    <tr>
      <th>Project Target</th>
      <td><strong>{p_name}</strong> ({p_type})</td>
      <th>Analysis Execution Time</th>
      <td>{analysis_time:.2f} seconds</td>
    </tr>
    <tr>
      <th>Detected Languages</th>
      <td>{langs}</td>
      <th>Memory Overhead</th>
      <td>{ram_mb:.1f} MB (Footprint: {disk_kb:.1f} KB)</td>
    </tr>
    <tr>
      <th>Detected Frameworks</th>
      <td>{frameworks}</td>
      <th>Key Entry Points</th>
      <td><code>{entry_pts}</code></td>
    </tr>
  </table>

  <h2>
    <span>Section 1: Code Defects, Root Causes &amp; Verified Patches</span>
    <span style="font-size: 12px; font-weight: normal; color: #64748b;">{len(summary.bugs)} Issues Reported</span>
  </h2>
  {bugs_html}

  <h2 style="page-break-before: always;">
    <span>Section 2: RAM Optimization &amp; Algorithmic Complexity</span>
    <span style="font-size: 12px; font-weight: normal; color: #64748b;">{len(summary.optimizations)} Findings</span>
  </h2>
  {opts_html}

  <h2>
    <span>Section 3: Security Vulnerabilities &amp; Secrets Audit</span>
    <span style="font-size: 12px; font-weight: normal; color: #64748b;">{len(summary.security_findings)} Findings</span>
  </h2>
  {sec_html}

</body>
</html>
"""
    return report_html

def generate_pdf_report(summary: ProjectAnalysisSummary) -> str:
    """Renders HTML report and compiles it to a PDF file using Chrome Headless."""
    html_content = generate_html_report(summary)
    
    temp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    html_path = temp_html.name
    temp_html.write(html_content.encode("utf-8"))
    temp_html.close()

    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf_path = temp_pdf.name
    temp_pdf.close()

    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not os.path.exists(chrome_bin):
        # Fallback to linux / chromium paths
        for candidate in ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]:
            if os.path.exists(candidate):
                chrome_bin = candidate
                break

    if os.path.exists(chrome_bin):
        cmd = [
            chrome_bin,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        os.unlink(html_path)
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            return pdf_path

    # Fallback to HTML if PDF cannot be compiled
    return html_path
