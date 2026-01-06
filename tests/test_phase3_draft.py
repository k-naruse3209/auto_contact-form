import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from src.phase3_outreach_draft import run_phase3


def test_phase3_writes_draft_with_signature_and_optout(tmp_path):
    out_dir = tmp_path / "out"
    company_dir = out_dir / "SampleCo"
    company_dir.mkdir(parents=True)

    context = """
# 株式会社サンプル

## 事業概要
- 製造業向けのSaaSを提供しています。

## 強み
- 導入実績500社
    """.strip()
    (company_dir / "04_extracted_context.md").write_text(context, encoding="utf-8")

    run_phase3(str(out_dir), max_companies=10)

    draft = (company_dir / "05_outreach_draft.md").read_text(encoding="utf-8")
    assert "株式会社サンプル" in draft
    assert "導入実績500社" in draft
    assert "株式会社DXAIソリューションズ" in draft
    assert "不要でしたら本メールは破棄してください。" in draft
