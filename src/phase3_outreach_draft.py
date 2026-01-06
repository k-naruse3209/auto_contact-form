#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class EvidenceAnchor:
    source_section: str
    text: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_sections(md: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current = None
    for line in md.splitlines():
        if line.startswith("## "):
            current = line.replace("## ", "").strip()
            sections[current] = []
            continue
        if current and line.startswith("- "):
            sections[current].append(line.replace("- ", "").strip())
    return sections


def extract_company_name(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line.replace("# ", "").strip()
    return fallback


def pick_evidence(sections: Dict[str, List[str]]) -> EvidenceAnchor:
    for key in ("強み", "事業概要", "想定顧客"):
        items = sections.get(key, [])
        if items:
            return EvidenceAnchor(source_section=key, text=items[0])
    return EvidenceAnchor(source_section="", text="")


def load_signature() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "outreach.md"
    text = read_text(prompt_path)
    if "署名情報:" not in text:
        return ""
    signature = text.split("署名情報:", 1)[1].strip()
    # Normalize bullet markers if present
    lines = [line.strip("- ") for line in signature.splitlines() if line.strip()]
    return "\n".join(lines)


def build_draft(company_name: str, sections: Dict[str, List[str]]) -> str:
    evidence = pick_evidence(sections)
    if evidence.text:
        why_you = f"貴社の「{evidence.text}」に触れ、"
    else:
        why_you = "貴社の事業内容を拝見し、"

    value = "当社では要件整理から開発・運用まで伴走し、問い合わせ対応の自動化や業務改善をご支援しています。"
    cta = "ご興味があれば15分だけオンラインでお話できれば幸いです。"
    opt_out = "不要でしたら本メールは破棄してください。"

    signature = load_signature()
    lines = [
        "件名: 問い合わせ業務の自動化ご提案",
        "",
        f"{company_name} ご担当者様",
        "",
        f"{why_you}問い合わせ対応の自動化についてご提案したくご連絡しました。",
        value,
        "",
        cta,
        "",
    ]
    if signature:
        lines.append(signature)
        lines.append("")
    lines.append(opt_out)
    return "\n".join(lines).rstrip() + "\n"


def run_phase3(out_dir: str, max_companies: int = 50) -> None:
    """Phase3 implementation: outreach drafting.

    Intended output per company:
      - 05_outreach_draft.md
    """
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])[:max_companies]
    print(f"[phase3] start: companies={len(company_dirs)}")

    for company_dir in company_dirs:
        context_path = company_dir / "04_extracted_context.md"
        if not context_path.exists():
            (company_dir / "05_outreach_draft.md").write_text("# (missing context)\n", encoding="utf-8")
            continue

        md = read_text(context_path)
        sections = parse_sections(md)
        company_name = extract_company_name(md, company_dir.name)
        draft = build_draft(company_name, sections)
        (company_dir / "05_outreach_draft.md").write_text(draft, encoding="utf-8")

    print("[phase3] DONE")


if __name__ == "__main__":
    run_phase3("data/out")
