#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from src.phase1_url_discovery import registrable_domain

USER_AGENT = "DXAI-OutreachBot/0.1 (contact: k-naruse@dxai-sol.co.jp)"

POSITIVE_HINTS = ["会社概要", "企業情報", "事業", "サービス", "プロダクト", "about", "company"]
NEGATIVE_HINTS = ["採用", "求人", "IR", "ニュース", "プレス"]
SALES_REJECTION_HINTS = ["営業お断り", "広告お断り", "営業目的", "勧誘お断り"]


@dataclass
class ContextPage:
    url: str
    title: str
    fetched_at: str
    status_code: int
    content_path: str


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"[。！？\n]", text)
    return [normalize_text(p) for p in parts if normalize_text(p)]


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    for tag in soup(["nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if not getattr(tag, "get", None) or not isinstance(getattr(tag, "attrs", None), dict):
            continue
        classes = " ".join(tag.get("class", []))
        ident = tag.get("id", "") or ""
        needle = f"{classes} {ident}".lower()
        if re.search(r"(nav|menu|header|footer|breadcrumb|sidebar|gnav|global-nav|site-header|site-footer)", needle):
            tag.decompose()
    meta_texts = []
    for key in ("description", "og:description"):
        tag = soup.find("meta", attrs={"name": key}) or soup.find("meta", attrs={"property": key})
        if tag and tag.get("content"):
            meta_texts.append(tag["content"].strip())
    title_text = extract_title(html)
    headings = []
    for h in soup.find_all(["h1", "h2"]):
        text = normalize_text(h.get_text(" ", strip=True))
        if text:
            headings.append(text)
    body_text = soup.get_text(" ", strip=True)
    return " ".join(meta_texts + [title_text] + headings + [body_text]).strip()


def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string if soup.title and soup.title.string else ""
    return normalize_text(title)


def score_link(text: str, url: str) -> int:
    score = 0
    hay = f"{text} {url}".lower()
    for hint in POSITIVE_HINTS:
        if hint.lower() in hay:
            score += 5
    for hint in NEGATIVE_HINTS:
        if hint.lower() in hay:
            score -= 5
    return score


def collect_internal_links(html: str, base_url: str, regdom: str) -> Dict[str, int]:
    soup = BeautifulSoup(html, "lxml")
    scored: Dict[str, int] = {}
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        url = urljoin(base_url, href)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            continue
        if registrable_domain(url) != regdom:
            continue
        url = url.split("#", 1)[0]
        text = a.get_text(" ", strip=True)
        score = score_link(text, url)
        if url not in scored or score > scored[url]:
            scored[url] = score
    return scored


def pick_candidate_urls(home_url: str, html: str, max_extra: int = 2) -> List[str]:
    regdom = registrable_domain(home_url)
    scored = collect_internal_links(html, home_url, regdom)
    ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    extras = [url for url, score in ranked if score > 0][:max_extra]
    base = f"{urlparse(home_url).scheme}://{urlparse(home_url).netloc}/"
    for path in ("/company", "/about", "/service", "/services", "/business", "/company/profile", "/about-us"):
        extras.append(urljoin(base, path))
    # de-dup while preserving order
    seen = set()
    deduped = []
    for url in extras:
        if url not in seen and registrable_domain(url) == regdom:
            seen.add(url)
            deduped.append(url)
    return deduped[:max_extra]


def fetch_page(client: httpx.Client, url: str) -> tuple[int, str]:
    r = client.get(url, timeout=20.0, follow_redirects=True)
    return r.status_code, r.text


def is_good_sentence(sentence: str) -> bool:
    if not sentence:
        return False
    if len(sentence) < 12 or len(sentence) > 200:
        return False
    bad_markers = [
        "©",
        "Copyright",
        "プライバシーポリシー",
        "お問い合わせ",
        "採用情報",
        "ニュースリリース",
        "プレスリリース",
        "メニュー",
        "ホーム",
        "トップ",
        "skip",
    ]
    if any(b in sentence for b in bad_markers):
        return False
    # avoid menu-like strings
    if sentence.count("・") >= 3 or sentence.count("｜") >= 3:
        return False
    if len(sentence.split()) > 18:
        return False
    return True


def truncate_sentence(sentence: str, max_len: int = 90) -> str:
    if len(sentence) <= max_len:
        return sentence
    return sentence[: max_len - 1].rstrip() + "…"


def build_context(company_name: str, texts: Iterable[str]) -> str:
    combined = "\n".join(texts)
    raw_sentences = split_sentences(combined)
    sentences = [s for s in raw_sentences if is_good_sentence(s)]
    fallback = [s for s in raw_sentences if 10 <= len(s) <= 220][:3]

    def collect(keywords: List[str], max_items: int = 2) -> List[str]:
        hits = []
        for s in sentences:
            if any(k in s for k in keywords):
                if s not in hits:
                    hits.append(truncate_sentence(s))
            if len(hits) >= max_items:
                break
        if not hits and fallback:
            hits.append(truncate_sentence(fallback[0]))
        return hits

    sections = {
        "事業概要": collect(["事業", "サービス", "プロダクト", "業務", "ソリューション"]),
        "想定顧客": collect(["顧客", "お客様", "導入", "利用", "対象", "クライアント"]),
        "強み": collect(["強み", "特徴", "優位", "実績", "選ばれる理由"]),
        "IT/AI活用の余地（仮説）": collect(["AI", "データ", "自動化", "DX", "効率化"]),
    }

    lines = [f"# {company_name}", ""]
    for title, items in sections.items():
        lines.append(f"## {title}")
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("- （未抽出）")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def robots_allows(client: httpx.Client, base_url: str) -> bool:
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        r = client.get(robots_url, timeout=10.0)
    except httpx.HTTPError:
        return True
    if r.status_code != 200:
        return True
    lines = [line.strip() for line in r.text.splitlines()]
    current_agent = None
    disallow_all = False
    for line in lines:
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("user-agent:"):
            current_agent = line.split(":", 1)[1].strip()
        elif line.lower().startswith("disallow:") and current_agent in ("*", "DXAI-OutreachBot"):
            path = line.split(":", 1)[1].strip()
            if path == "/":
                disallow_all = True
                break
    return not disallow_all


def run_phase2(
    out_dir: str,
    max_companies: int = 50,
    sleep_min: float = 0.4,
    sleep_max: float = 0.8,
    max_pages: int = 3,
) -> None:
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])[:max_companies]
    print(f"[phase2] start: companies={len(company_dirs)}")

    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
        for company_dir in company_dirs:
            official_path = company_dir / "02_official_url.json"
            pages_dir = company_dir / "03_pages_fetched"
            pages_dir.mkdir(parents=True, exist_ok=True)

            if not official_path.exists():
                write_json(company_dir / "03_pages_fetched.json", {"company_name": company_dir.name, "pages": []})
                (company_dir / "04_extracted_context.md").write_text("# (missing official_url)\n", encoding="utf-8")
                continue

            official = read_json(official_path)
            company_name = official.get("company_name", company_dir.name)
            official_url = official.get("official_url")
            if not official_url:
                write_json(company_dir / "03_pages_fetched.json", {"company_name": company_name, "pages": []})
                (company_dir / "04_extracted_context.md").write_text(f"# {company_name}\n\n- （公式URL未取得）\n", encoding="utf-8")
                continue

            base_url = f"{urlparse(official_url).scheme}://{urlparse(official_url).netloc}/"
            if not robots_allows(client, base_url):
                write_json(company_dir / "03_pages_fetched.json", {
                    "company_name": company_name,
                    "pages": [],
                    "notes": "robots.txt disallow all",
                })
                (company_dir / "04_extracted_context.md").write_text(
                    f"# {company_name}\n\n- （robots.txtにより取得不可）\n",
                    encoding="utf-8",
                )
                continue

            urls = [official_url]
            if base_url not in urls:
                urls.append(base_url)

            pages: List[ContextPage] = []
            texts: List[str] = []
            sales_rejection = False

            # Fetch homepage for link discovery
            try:
                status, html = fetch_page(client, base_url)
                title = extract_title(html)
                page_path = pages_dir / "page_home.html"
                page_path.write_text(html, encoding="utf-8")
                rel_path = str(page_path.relative_to(company_dir))
                pages.append(ContextPage(base_url, title, iso_now(), status, rel_path))
                texts.append(extract_text(html))
                if any(hint in html for hint in SALES_REJECTION_HINTS):
                    sales_rejection = True
                extra_urls = pick_candidate_urls(base_url, html, max_extra=max_pages - 1)
            except Exception:
                extra_urls = []

            for url in extra_urls:
                if url not in urls:
                    urls.append(url)

            # Limit total pages
            urls = urls[:max_pages]

            for idx, url in enumerate(urls, start=1):
                if url == base_url:
                    continue
                try:
                    status, html = fetch_page(client, url)
                    title = extract_title(html)
                    page_path = pages_dir / f"page_{idx}.html"
                    page_path.write_text(html, encoding="utf-8")
                    rel_path = str(page_path.relative_to(company_dir))
                    pages.append(ContextPage(url, title, iso_now(), status, rel_path))
                    texts.append(extract_text(html))
                    if any(hint in html for hint in SALES_REJECTION_HINTS):
                        sales_rejection = True
                except Exception:
                    continue
                time.sleep(random.uniform(sleep_min, sleep_max))

            write_json(company_dir / "03_pages_fetched.json", {
                "company_name": company_name,
                "pages": [p.__dict__ for p in pages],
                "notes": "sales_rejection_detected" if sales_rejection else None,
            })
            (company_dir / "04_extracted_context.md").write_text(build_context(company_name, texts), encoding="utf-8")

    print("[phase2] DONE")


if __name__ == "__main__":
    run_phase2("data/out")
