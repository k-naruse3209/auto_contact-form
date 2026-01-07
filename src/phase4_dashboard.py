#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_dashboard(out_dir: str, output_path: str) -> None:
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])

    rows: List[str] = []
    for company_dir in company_dirs:
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
        for key in order:
            meta = fields.get(key, {})
            val = meta.get("value")
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

        rows.append(
            "<tr>"
            f"<td>{name}</td>"
            f"<td>{status}</td>"
            f"<td>{form_url or '-'}</td>"
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
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; color: #222; }}
    h1 {{ font-size: 20px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #f5f5f5; text-align: left; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .status-ok {{ color: #0a7a2f; font-weight: 600; }}
    .status-no_form {{ color: #b45309; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Phase4 Form Dashboard</h1>
  <table>
    <thead>
      <tr>
        <th>Company</th>
        <th>Status</th>
        <th>Form URL</th>
        <th>Contact Candidates (top 3)</th>
        <th>Planned Fields (value)</th>
      </tr>
    </thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>
"""

    Path(output_path).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    render_dashboard("data/out", "docs/phase4_dashboard.html")
