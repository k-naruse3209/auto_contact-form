import sys
from pathlib import Path

from bs4 import BeautifulSoup

repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from src.phase4_form_automation import map_form_fields


def test_map_form_fields_basic():
    html = """
    <form>
      <label for="company">会社名</label>
      <input id="company" name="company" />
      <label for="name">お名前</label>
      <input id="name" name="name" />
      <label for="email">メール</label>
      <input id="email" type="email" name="email" />
      <label for="message">お問い合わせ内容</label>
      <textarea id="message" name="message"></textarea>
    </form>
    """
    soup = BeautifulSoup(html, "lxml")
    fields = map_form_fields(soup.find("form"))
    assert "company" in fields
    assert "name" in fields
    assert "email" in fields
    assert "message" in fields
