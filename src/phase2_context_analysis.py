#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ContextPage:
    url: str
    title: str
    fetched_at: float
    status_code: int
    content_path: str


def run_phase2(out_dir: str, max_companies: int = 50) -> None:
    """Phase2 skeleton: context analysis.

    Intended outputs per company:
      - 03_pages_fetched.json
      - 04_extracted_context.md
    """
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])[:max_companies]
    print(f"[phase2] skeleton only: companies={len(company_dirs)}")
    print("[phase2] TODO: fetch pages, extract context, write outputs")
