#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_summary(out_dir: str, output_csv: str) -> None:
    base = Path(out_dir)
    rows = []
    for d in sorted([p for p in base.iterdir() if p.is_dir()]):
        plan_path = d / "07_form_plan.json"
        if not plan_path.exists():
            rows.append({"company": d.name, "form_url": "", "status": "no_plan"})
            continue
        plan = read_json(plan_path)
        fields = plan.get("fields", {}) or {}
        missing = [k for k in ["name", "email", "message"] if k not in fields]
        status = "ok" if not missing and fields else "missing_required"
        if plan.get("notes") and not fields:
            status = "no_form"
        rows.append(
            {
                "company": d.name,
                "form_url": plan.get("form_url", ""),
                "status": status,
                "missing_required": ";".join(missing),
            }
        )

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "form_url", "status", "missing_required"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    run_summary("data/out", "docs/phase4_summary.csv")
