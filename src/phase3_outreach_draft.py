#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
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


def build_draft(company_name: str, sections: Dict[str, List[str]]) -> str:
    mission, strength = pick_evidence_pair(sections)
    mission_text = mission.text or "貴社の取り組み"
    strength_text = strength.text or "現場に根ざした支援"

    template = f"""件名： 【ご提案】{company_name}における「AI実装・オフショア連携」について

本文：

{company_name} ご担当者様

突然のご連絡失礼いたします。 株式会社DXAIソリューションズ（DXAI Sol）の成瀬と申します。

貴社のWebサイトを拝見し、「{mission_text}」という点に深く感銘を受けております。 特に、貴社が強みとされる「{strength_text}」といった領域や、DX推進現場において、「システム実装」や「AI開発」を担う技術パートナーとしてお力添えできればと思いご連絡いたしました。

弊社は、東京とベトナム（ハノイ・ダナン）に拠点を置く開発会社です。 グループ全体で約30名規模の少数精鋭体制ながら、「日本品質×オフショアの機動力」を強みとしており、貴社の事業に以下のシナジーを生み出せると考えております。

貴社PMO・コンサルティング案件の「実装パートナー」 貴社が支援されるDXプロジェクトやPMO支援の現場において、戦略を実行に移すための「開発実働部隊」として機能します。弊社のベトナム拠点を活用いただくことで、国内相場よりも適正なコストで高品質なリソースを提供し、プロジェクトの利益率向上に貢献します。

「AIソリューション」における技術連携 貴社が注力される領域において、弊社の生成AI（LLM・マルチモーダルAI）技術がお役に立てる可能性があります。OCRや画像解析とLLMを組み合わせた高度なデータ処理エンジンの共同開発や、RAG（検索拡張生成）を用いたナレッジ活用システムの構築など、技術面での壁打ち相手としてもご活用いただけます。

プラットフォーム事業への「オフショアチーム」提供 貴社のIT人材プラットフォームにおけるリソースの選択肢の一つとして、弊社の「ラボ型開発チーム（ベトナム）」を組み込んでいただくご提案です。個人のフリーランス人材だけでなく、まとまった開発チームを柔軟に提供できるパートナーとして連携させていただくことで、クライアントへの提案の幅を広げます。

【弊社の実績一例】 ・金融・建設業界向けクラウドシステム構築 ・多言語対応AIソリューション（自社開発：Lingua Flow） ・ユニクロ様、楽天様、Sansan様など大手企業様向け開発実績多数

貴社の理念に、弊社の「実装力」と「オフショアのメリット」を加えていただき、共にクライアント様の現場変革を加速させられれば幸いです。

まずは会社概要や開発事例をお送りするだけでも構いませんし、オンラインでの情報交換（15〜30分程度）の機会をいただけますと幸いです。

ご検討のほど、何卒よろしくお願い申し上げます。

Mail: k-naruse@dxai-sol.co.jp
Tel: 050-1722-6417
株式会社DXAIソリューションズ (DXAI Solutions Co., Ltd.)
URL: https://dxai-sol.co.jp/
【東京本社】 〒104-0033 東京都中央区新川1-3-21 BIZSMART 4階 【開発拠点】 ベトナム（ハノイ・ダナン）、大分県（姫島サテライト）
"""
    return template.rstrip() + "\n"


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
