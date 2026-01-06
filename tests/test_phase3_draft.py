import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from src.phase3_outreach_draft import build_prompt, parse_sections


def test_build_prompt_includes_evidence_and_template():
    context = """
# 株式会社サンプル

## 事業概要
- 製造業向けのSaaSを提供しています。

## 強み
- 導入実績500社
    """.strip()
    sections = parse_sections(context)
    prompt = build_prompt("株式会社サンプル", sections)

    assert "テンプレート:" in prompt
    assert "エビデンス:" in prompt
    assert "株式会社サンプル" in prompt
    assert "導入実績500社" in prompt
