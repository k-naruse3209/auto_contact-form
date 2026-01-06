#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


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


def pick_evidence_pair(sections: Dict[str, List[str]]) -> tuple[EvidenceAnchor, EvidenceAnchor]:
    mission = EvidenceAnchor(source_section="", text="")
    strength = EvidenceAnchor(source_section="", text="")

    for key in ("事業概要", "想定顧客", "強み"):
        items = sections.get(key, [])
        if items:
            mission = EvidenceAnchor(source_section=key, text=items[0])
            break

    for key in ("強み", "事業概要"):
        items = sections.get(key, [])
        if items:
            strength = EvidenceAnchor(source_section=key, text=items[0])
            break

    return mission, strength


def clean_evidence(text: str) -> str:
    if not text or "（未抽出）" in text:
        return ""
    bad = ["コーポレートサイト", "会社概要", "採用情報", "お問い合わせ"]
    if any(b in text for b in bad):
        return ""
    return text


def load_template() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "outreach.md"
    return read_text(prompt_path)


def build_prompt(company_name: str, sections: Dict[str, List[str]]) -> str:
    template = load_template()
    mission, strength = pick_evidence_pair(sections)
    mission_text = clean_evidence(mission.text)
    strength_text = clean_evidence(strength.text)

    evidence_block = "\n".join(
        [
            f"- company_name: {company_name}",
            f"- mission_evidence: {mission_text or '（該当なし）'}",
            f"- strength_evidence: {strength_text or '（該当なし）'}",
        ]
    )

    instructions = (
        "あなたは日本語で協業依頼文を作成する担当者です。"
        "以下のテンプレートに沿って、本文のみを出力してください。"
        "テンプレート内の {company_name}, {mission_evidence}, {strength_evidence} を適切に置換し、"
        "不自然な箇所は整えてください。"
        "（該当なし）の場合は抽象表現に言い換えて、長文のコピペは避け、120文字以内の根拠に要約してください。"
        "余計な見出しやコードブロックは出力しないでください。"
    )

    return "\n\n".join(
        [
            instructions,
            "テンプレート:",
            template,
            "エビデンス:",
            evidence_block,
        ]
    )


def generate_draft_llm(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY in .env")
    model = os.getenv("GEMINI_MODEL", "gemini-3.0-flash").strip()
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    if not response or not getattr(response, "text", None):
        raise RuntimeError("Gemini returned empty response")
    return response.text.strip() + "\n"


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
        prompt = build_prompt(company_name, sections)
        draft = generate_draft_llm(prompt)
        (company_dir / "05_outreach_draft.md").write_text(draft, encoding="utf-8")
        time.sleep(0.5)

    print("[phase3] DONE")


if __name__ == "__main__":
    run_phase3("data/out")
