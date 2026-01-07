#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_id(text: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or fallback


def render_dashboard(out_dir: str, output_path: str) -> None:
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])

    rows: List[str] = []
    scripts: List[str] = []
    for idx, company_dir in enumerate(company_dirs, start=1):
        name = company_dir.name
        plan_path = company_dir / "07_form_plan.json"
        candidates_path = company_dir / "06_contact_page_candidates.json"

        candidates = []
        if candidates_path.exists():
            data = read_json(candidates_path)
            candidates = data.get("candidates", [])

        plan = None
        if plan_path.exists():
            plan = read_json(plan_path)

        form_url = plan.get("form_url") if plan else None
        fields = plan.get("fields", {}) if plan else {}
        status = "ok" if form_url and fields else "no_form"

        field_items = []
        preferred = [
            "company",
            "department",
            "name",
            "name_kana",
            "name_hiragana",
            "email",
            "phone",
            "postal_code",
            "address",
            "website",
            "privacy_consent",
            "message",
        ]
        order = [k for k in preferred if k in fields]
        order += [k for k in fields.keys() if k not in order]
        plan_values = {}
        for key in order:
            meta = fields.get(key, {})
            val = meta.get("value")
            sel = meta.get("selector")
            if sel and val is not None:
                plan_values[key] = {"selector": sel, "value": val}
            if key == "message" and val:
                preview = str(val).replace("\n", " ")[:140]
                field_items.append(
                    f"<details><summary><b>{key}</b>: {preview}...</summary><pre>{val}</pre></details>"
                )
            else:
                field_items.append(f"<div><b>{key}</b>: {val}</div>")
        field_html = "".join(field_items) if field_items else "-"

        cand_items = []
        for cand in candidates[:3]:
            cand_items.append(f"<div>{cand.get('url')}</div>")
        cand_html = "".join(cand_items) if cand_items else "-"

        plan_id = safe_id(name, f"company-{idx}")
        scripts.append(
            f"<script type=\"application/json\" id=\"plan-{plan_id}\">{json.dumps(plan_values, ensure_ascii=False)}</script>"
        )
        status_badge = f"<span class='pill{'' if status == 'ok' else ' warn'}'>{status}</span>"
        open_link = (
            f"<a class='action' href='{form_url}' target='_blank' rel='noopener'>Open</a>"
            if form_url
            else "-"
        )
        copy_btn = (
            f"<button class='action ghost' data-plan-id='plan-{plan_id}'>Copy Fill Script</button>"
            if plan_values
            else "-"
        )
        rows.append(
            "<tr>"
            f"<td>{name}</td>"
            f"<td>{status_badge}</td>"
            f"<td class='url'>{form_url or '-'}</td>"
            f"<td class='actions'>{open_link} {copy_btn}</td>"
            f"<td>{cand_html}</td>"
            f"<td>{field_html}</td>"
            "</tr>"
        )

    html = f"""
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Phase4 Form Dashboard</title>
  <style>
    :root {{
      --ink: #121212;
      --muted: #4b5563;
      --accent: #0f766e;
      --accent-2: #c2410c;
      --bg: #f6f5f2;
      --card: #ffffff;
      --line: #e5e7eb;
      --shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Space Grotesk", "Hiragino Sans", "Noto Sans JP", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1200px 600px at 10% -10%, #e9e5dc 0%, transparent 60%),
        radial-gradient(900px 600px at 110% 0%, #e6f2f0 0%, transparent 55%),
        var(--bg);
    }}
    header {{
      padding: 28px 32px 8px;
    }}
    h1 {{
      font-size: 28px;
      margin: 0 0 8px;
      letter-spacing: 0.02em;
    }}
    .sub {{
      color: var(--muted);
      margin: 0 0 16px;
      font-size: 13px;
    }}
    .guide {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px 16px;
      box-shadow: var(--shadow);
      max-width: 720px;
    }}
    .guide-title {{
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .guide ol {{
      margin: 0 0 8px 18px;
      padding: 0;
      color: #1f2937;
      font-size: 13px;
    }}
    .guide li {{
      margin-bottom: 6px;
    }}
    .guide-note {{
      font-size: 12px;
      color: var(--muted);
    }}
    .wrap {{
      padding: 0 32px 32px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      border-radius: 12px;
      overflow: hidden;
    }}
    thead th {{
      position: sticky;
      top: 0;
      background: #f9fafb;
      text-align: left;
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: #6b7280;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }}
    tbody td {{
      padding: 12px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      font-size: 13px;
    }}
    tbody tr:hover {{
      background: #f8fafc;
    }}
    .pill {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 12px;
      background: #e2f3f1;
      color: var(--accent);
    }}
    .pill.warn {{
      background: #ffedd5;
      color: var(--accent-2);
    }}
    .url {{
      color: #1f2937;
      word-break: break-all;
    }}
    .actions {{
      white-space: nowrap;
    }}
    .action {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #ffffff;
      color: #111827;
      text-decoration: none;
      font-size: 12px;
      margin-right: 6px;
      cursor: pointer;
    }}
    .action.ghost {{
      background: #f3f4f6;
    }}
    details {{
      border: 1px dashed #d1d5db;
      border-radius: 10px;
      padding: 8px 10px;
      background: #fbfbfb;
    }}
    details summary {{
      cursor: pointer;
      color: #111827;
      font-weight: 600;
    }}
    pre {{
      white-space: pre-wrap;
      font-family: "IBM Plex Mono", "Menlo", monospace;
      font-size: 12px;
      color: #374151;
    }}
    @media (max-width: 900px) {{
      header, .wrap {{ padding: 16px; }}
      thead th:nth-child(4), thead th:nth-child(5) {{
        display: none;
      }}
      tbody td:nth-child(4), tbody td:nth-child(5) {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Phase4 Form Dashboard</h1>
    <p class="sub">確認用: どの会社に何のフィールドがあり、どの値が入るかを一覧化</p>
    <div class="guide">
      <div class="guide-title">使い方（送信直前まで）</div>
      <ol>
        <li>Actions の <b>Open</b> でフォームを開く</li>
        <li><b>Copy Fill Script</b> を押す</li>
        <li>フォームのタブで開発者ツール → Console に貼り付けて実行</li>
        <li>入力内容を確認して、最後の送信は手動で行う</li>
      </ol>
      <div class="guide-note">注: ダッシュボードから直接入力はできません（ブラウザの制約）。</div>
    </div>
  </header>
  <div class="wrap">
    <table>
      <thead>
        <tr>
          <th>Company</th>
          <th>Status</th>
          <th>Form URL</th>
          <th>Actions</th>
          <th>Contact Candidates (top 3)</th>
          <th>Planned Fields (value)</th>
        </tr>
      </thead>
      <tbody>
        {"".join(rows)}
      </tbody>
    </table>
  </div>
  {"".join(scripts)}
  <script>
    function buildFillScript(plan) {{
      const payload = JSON.stringify(plan || {{}});
      return `(function() {{
  const data = ${{payload}};
  const results = [];
  const trigger = (el) => {{
    try {{
      el.dispatchEvent(new Event('input', {{ bubbles: true }}));
      el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }} catch (e) {{}}
  }};
  Object.entries(data).forEach(([key, item]) => {{
    const el = document.querySelector(item.selector);
    if (!el) {{
      results.push({{ key, selector: item.selector, ok: false }});
      return;
    }}
    if (el.type === 'checkbox' || el.type === 'radio') {{
      el.checked = !!item.value;
    }} else {{
      el.value = item.value;
    }}
    trigger(el);
    results.push({{ key, selector: item.selector, ok: true }});
  }});
  console.table(results);
}})();`;
    }}

    document.addEventListener('click', (event) => {{
      const btn = event.target.closest('button[data-plan-id]');
      if (!btn) return;
      const scriptEl = document.getElementById(btn.dataset.planId);
      if (!scriptEl) return;
      let plan = {{}};
      try {{
        plan = JSON.parse(scriptEl.textContent || '{{}}');
      }} catch (e) {{
        plan = {{}};
      }}
      const payload = buildFillScript(plan);
      navigator.clipboard.writeText(payload).then(() => {{
        btn.textContent = 'Copied';
        setTimeout(() => {{
          btn.textContent = 'Copy Fill Script';
        }}, 1200);
      }});
    }});
  </script>
</body>
</html>
"""

    Path(output_path).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    render_dashboard("data/out", "docs/phase4_dashboard.html")
