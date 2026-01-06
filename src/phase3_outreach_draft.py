#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class EvidenceAnchor:
    source_url: str
    summary: str


def run_phase3(out_dir: str, max_companies: int = 50) -> None:
    """Phase3 skeleton: outreach drafting.

    Intended output per company:
      - 05_outreach_draft.md
    """
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])[:max_companies]
    print(f"[phase3] skeleton only: companies={len(company_dirs)}")
    print("[phase3] TODO: draft outreach with evidence anchors")
