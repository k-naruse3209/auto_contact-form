import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from src.phase2_context_analysis import build_context, extract_text


def test_build_context_extracts_keywords():
    html = """
    <html><head><title>会社概要</title></head>
    <body>
      <p>当社は製造業向けのサービスを提供しています。</p>
      <p>お客様は中堅製造業が中心です。</p>
      <p>強みは導入実績500社です。</p>
    </body></html>
    """
    text = extract_text(html)
    md = build_context("サンプル株式会社", [text])

    assert "事業概要" in md
    assert "サービスを提供" in md
    assert "想定顧客" in md
    assert "お客様は中堅製造業" in md
    assert "強み" in md
    assert "導入実績500社" in md
