#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FormPlan:
    form_url: str
    fields: dict
    notes: str


def run_phase4(out_dir: str, max_companies: int = 50) -> None:
    """Phase4 skeleton: form automation.

    Intended outputs per company:
      - 06_contact_page_candidates.json
      - 07_form_plan.json
      - 08_ready_to_submit.png
    """
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])[:max_companies]
    print(f"[phase4] skeleton only: companies={len(company_dirs)}")
    print("[phase4] TODO: locate forms, fill, and capture ready-to-submit")
