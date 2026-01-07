#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def required_missing(plan: Dict) -> List[str]:
    required = ["company", "name", "email", "message"]
    fields = plan.get("fields", {}) or {}
    missing = [k for k in required if k not in fields]
    return missing


def run_report(out_dir: str) -> None:
    base = Path(out_dir)
    results = []
    for d in sorted([p for p in base.iterdir() if p.is_dir()]):
        plan_path = d / "07_form_plan.json"
        candidates_path = d / "06_contact_page_candidates.json"
        item = {
            "company": d.name,
            "status": "no_plan",
            "form_url": "",
            "missing_required": [],
            "notes": "",
        }
        if candidates_path.exists():
            try:
                c = read_json(candidates_path)
                if c.get("candidates"):
                    item["form_url"] = c["candidates"][0].get("url", "")
            except Exception:
                pass
        if plan_path.exists():
            plan = read_json(plan_path)
            item["form_url"] = plan.get("form_url", item["form_url"]) or ""
            item["notes"] = plan.get("notes", "")
            missing = required_missing(plan)
            item["missing_required"] = missing
            item["status"] = "ok" if not missing and plan.get("fields") else "missing_required"
            if plan.get("notes") and not plan.get("fields"):
                item["status"] = "no_form"
        results.append(item)

    write_json(base / "phase4_report.json", {"results": results})


if __name__ == "__main__":
    run_report("data/out")
