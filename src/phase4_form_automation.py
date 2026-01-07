#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from src.phase1_url_discovery import registrable_domain
from src.phase2_context_analysis import robots_allows

USER_AGENT = "DXAI-OutreachBot/0.1 (contact: k-naruse@dxai-sol.co.jp)"

CONTACT_KEYWORDS = [
    "お問い合わせ",
    "問合せ",
    "問い合わせ",
    "ご相談",
    "contact",
    "inquiry",
    "support",
]

INTERNAL_HINTS = [
    "会社概要",
    "企業情報",
    "事業",
    "サービス",
    "プロダクト",
    "about",
    "company",
]

FIELD_KEYWORDS = {
    "company": ["会社", "会社名", "法人", "法人名", "貴社", "company", "organization"],
    "name": ["氏名", "担当", "お名前", "名前", "onamae", "name"],
    "name_kana": ["カナ", "フリガナ", "ふりがな", "kana"],
    "name_hiragana": ["ひらがな", "hiragana"],
    "email": ["メール", "mail", "mailadd", "email"],
    "message": ["内容", "お問い合わせ", "問合せ", "本文", "message", "相談"],
    "phone": ["電話", "tel", "phone"],
    "address": ["住所", "所在地", "address"],
    "postal_code": ["郵便番号", "〒", "zip", "postal"],
    "department": ["部署", "department"],
    "role": ["役職", "role", "職種"],
    "website": ["URL", "website", "サイト", "web"],
    "privacy_consent": ["プライバシーポリシー", "個人情報", "privacy", "policy", "同意"],
    "inquiry_type": [
        "お問合せの種類",
        "お問い合わせ項目",
        "問合せ種別",
        "問合せ項目",
        "問い合わせ種別",
        "問い合わせ項目",
        "問合せ",
        "問い合わ",
        "問い合せ",
        "種別",
        "カテゴリ",
        "category",
        "inquiry type",
    ],
}

COMPANY_CONTACT_OVERRIDES = {
    "Booost株式会社": ["https://booost-tech.com/contact/contact-other/"],
}

SENDER_VALUES = {
    "company": "株式会社DXAIソリューションズ",
    "name": "成瀬　恵介",
    "name_kana": "ナルセ ケイスケ",
    "name_hiragana": "なるせ　けいすけ",
    "email": "k-naruse@dxai-sol.co.jp",
    "phone": "05017226417",
    "address": "〒東京都中央区新川1−3−21　Biz Station 茅場町",
    "postal_code": "104-0033",
    "department": "ソリューション事業部",
    "website": "https://dxai-sol.co.jp/",
    "inquiry_type": "業務提携",
}

INQUIRY_PREFER = ["業務提携", "協業", "その他"]


@dataclass
class CandidatePage:
    url: str
    confidence: float
    evidence: List[str]


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_contact_link(text: str, url: str) -> bool:
    hay = f"{text} {url}".lower()
    return any(k.lower() in hay for k in CONTACT_KEYWORDS)


def score_contact_link(text: str, url: str) -> tuple[float, List[str]]:
    score = 0.0
    evidence = []
    hay = f"{text} {url}".lower()
    for k in CONTACT_KEYWORDS:
        if k.lower() in hay:
            score += 1.0
            evidence.append(f"keyword:{k}")
    if any(x in hay for x in ["contact", "inquiry", "otoiawase", "support"]):
        score += 0.5
    return score, evidence


def collect_contact_candidates(html: str, base_url: str) -> List[CandidatePage]:
    soup = BeautifulSoup(html, "lxml")
    candidates: Dict[str, CandidatePage] = {}
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        url = urljoin(base_url, href)
        text = normalize_text(a.get_text(" ", strip=True))
        if not is_contact_link(text, url):
            continue
        score, evidence = score_contact_link(text, url)
        url = url.split("#", 1)[0]
        if url not in candidates:
            candidates[url] = CandidatePage(url=url, confidence=score, evidence=evidence)
        else:
            existing = candidates[url]
            if score > existing.confidence:
                existing.confidence = score
                existing.evidence = evidence
    return sorted(candidates.values(), key=lambda c: c.confidence, reverse=True)


def collect_internal_links(html: str, base_url: str, regdom: str, limit: int = 5) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    links = {}
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        url = urljoin(base_url, href).split("#", 1)[0]
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            continue
        if registrable_domain(url) != regdom:
            continue
        text = normalize_text(a.get_text(" ", strip=True))
        score = 0
        hay = f"{text} {url}".lower()
        for hint in INTERNAL_HINTS:
            if hint.lower() in hay:
                score += 2
        if score > 0:
            links[url] = max(links.get(url, 0), score)
    ranked = sorted(links.items(), key=lambda x: x[1], reverse=True)
    return [url for url, _ in ranked[:limit]]


def add_common_contact_paths(base_url: str) -> List[str]:
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/"
    paths = ["contact", "contact/", "inquiry", "inquiry/", "otoiawase", "support", "form"]
    return [urljoin(base, p) for p in paths]


def find_contact_from_sitemap(client: httpx.Client, base_url: str) -> List[str]:
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    try:
        resp = client.get(sitemap_url, timeout=15.0)
        if resp.status_code != 200:
            return []
        text = resp.text
    except Exception:
        return []
    urls = re.findall(r"<loc>([^<]+)</loc>", text)
    hits = []
    for u in urls:
        if any(k in u.lower() for k in ["contact", "inquiry", "otoiawase", "support"]):
            hits.append(u)
    return hits[:5]


def get_label_text(el) -> str:
    if el.has_attr("id"):
        label = el.find_parent().find("label", attrs={"for": el["id"]}) if el.find_parent() else None
        if label:
            return normalize_text(label.get_text(" ", strip=True))
    if el.find_parent("label"):
        return normalize_text(el.find_parent("label").get_text(" ", strip=True))
    return ""


def build_selector(el, soup: BeautifulSoup) -> Optional[str]:
    if el.has_attr("id") and el["id"]:
        return f"#{el['id']}"
    if el.has_attr("name") and el["name"]:
        return f"[name='{el['name']}']"
    return None


def extract_select_options(el: BeautifulSoup) -> List[str]:
    options = []
    for opt in el.find_all("option"):
        text = normalize_text(opt.get_text(" ", strip=True))
        if text:
            options.append(text)
    return options


def extract_radio_options(form: BeautifulSoup, name: str) -> List[str]:
    options = []
    inputs = form.find_all("input", attrs={"name": name, "type": "radio"})
    for inp in inputs:
        label = get_label_text(inp)
        value = normalize_text(label or inp.get("value", ""))
        if value:
            options.append(value)
    return options


def choose_inquiry_option(options: List[str]) -> str:
    blacklist = {"---", "--", "選択してください", "選択", "未選択", "項目を選択"}
    filtered = [opt for opt in options if opt not in blacklist]
    for pref in INQUIRY_PREFER:
        for opt in filtered:
            if pref in opt:
                return opt
    if "その他" in filtered:
        return "その他"
    return ""


def score_field(text: str, field_key: str, el_type: str) -> int:
    score = 0
    for kw in FIELD_KEYWORDS[field_key]:
        if kw.lower() in text.lower():
            score += 3
    if field_key == "email" and el_type == "email":
        score += 2
    if field_key == "email":
        lowered = text.lower()
        if any(tag in lowered for tag in ["confirm", "conf", "再入力", "確認"]):
            score -= 5
    if field_key == "phone" and el_type in ("tel", "phone"):
        score += 2
    if el_type in ("textarea",) and field_key == "message":
        score += 2
    if field_key == "inquiry_type" and el_type in ("select", "radio"):
        score += 2
    return score


def map_form_fields(form: BeautifulSoup) -> Dict[str, Dict[str, str]]:
    fields = {}
    elements = form.find_all(["input", "textarea", "select"])
    for key in FIELD_KEYWORDS.keys():
        best = (0, None)
        for el in elements:
            el_type = el.get("type", "text") if el.name == "input" else el.name
            if key == "privacy_consent" and el_type not in ("checkbox", "radio"):
                continue
            if key == "inquiry_type" and el_type not in ("select", "radio"):
                continue
            label = get_label_text(el)
            placeholder = el.get("placeholder", "")
            name = el.get("name", "")
            ident = el.get("id", "")
            text = " ".join([label, placeholder, name, ident])
            if key == "inquiry_type" and not any(k in text for k in FIELD_KEYWORDS["inquiry_type"]):
                continue
            score = score_field(text, key, el_type)
            if score > best[0]:
                best = (score, el)
        if best[1] is not None and best[0] > 0:
            selector = build_selector(best[1], form)
            if selector:
                entry = {"selector": selector}
                if key == "inquiry_type":
                    el = best[1]
                    if el.name == "select":
                        entry["options"] = extract_select_options(el)
                    elif el.name == "input" and el.get("type") == "radio":
                        entry["options"] = extract_radio_options(form, el.get("name", ""))
                    else:
                        continue
                fields[key] = entry
    # If inquiry_type collides with message field, drop it.
    if "inquiry_type" in fields and "message" in fields:
        if fields["inquiry_type"].get("selector") == fields["message"].get("selector"):
            fields.pop("inquiry_type", None)
    return fields


def build_plan(company_name: str, draft: str, form_url: str, fields: Dict[str, Dict[str, str]]) -> Dict:
    plan_fields = {}
    for key, meta in fields.items():
        value = None
        if key == "company":
            value = company_name
        elif key == "message":
            value = draft
        elif key == "privacy_consent":
            value = True
        elif key == "inquiry_type":
            options = meta.get("options", [])
            value = choose_inquiry_option(options) if options else SENDER_VALUES.get("inquiry_type")
        else:
            value = SENDER_VALUES.get(key)
        if value:
            plan_fields[key] = {"selector": meta["selector"], "value": value}
    return {
        "form_url": form_url,
        "fields": plan_fields,
        "notes": "ready-to-submit screenshot not implemented",
    }


def run_phase4(out_dir: str, max_companies: int = 50, companies: Optional[List[str]] = None) -> None:
    """Phase4 implementation: form plan generation.

    Intended outputs per company:
      - 06_contact_page_candidates.json
      - 07_form_plan.json
      - 08_ready_to_submit.png (not generated)
    """
    base = Path(out_dir)
    all_dirs = [p for p in base.iterdir() if p.is_dir()]
    if companies:
        dir_map = {p.name: p for p in all_dirs}
        company_dirs = [dir_map[name] for name in companies if name in dir_map]
    else:
        company_dirs = sorted(all_dirs)[:max_companies]
    print(f"[phase4] start: companies={len(company_dirs)}")

    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
        playwright = None
        browser = None
        try:
            from playwright.sync_api import sync_playwright

            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
        except Exception:
            playwright = None
            browser = None
        for company_dir in company_dirs:
            official_path = company_dir / "02_official_url.json"
            draft_path = company_dir / "05_outreach_draft.md"
            if not official_path.exists() or not draft_path.exists():
                write_json(company_dir / "06_contact_page_candidates.json", {"candidates": []})
                write_json(company_dir / "07_form_plan.json", {"notes": "missing inputs"})
                continue

            official = read_json(official_path)
            company_name = official.get("company_name", company_dir.name)
            official_url = official.get("official_url")
            if not official_url:
                write_json(company_dir / "06_contact_page_candidates.json", {"candidates": []})
                write_json(company_dir / "07_form_plan.json", {"notes": "missing official_url"})
                continue

            base_url = f"{urlparse(official_url).scheme}://{urlparse(official_url).netloc}/"
            if not robots_allows(client, base_url):
                write_json(company_dir / "06_contact_page_candidates.json", {"candidates": [], "notes": "robots disallow"})
                write_json(company_dir / "07_form_plan.json", {"notes": "robots disallow"})
                continue

            home_html = None
            try:
                home_resp = client.get(base_url, timeout=20.0)
                home_resp.raise_for_status()
                home_html = home_resp.text
            except Exception:
                # fall back to official_url if different
                try:
                    if official_url != base_url:
                        alt_resp = client.get(official_url, timeout=20.0)
                        alt_resp.raise_for_status()
                        home_html = alt_resp.text
                except Exception:
                    home_html = None

            candidates = []
            regdom = registrable_domain(base_url)
            if home_html:
                candidates.extend(collect_contact_candidates(home_html, base_url))
                internal_pages = collect_internal_links(home_html, base_url, regdom)
                for page_url in internal_pages:
                    try:
                        resp = client.get(page_url, timeout=20.0)
                        resp.raise_for_status()
                    except Exception:
                        continue
                    candidates.extend(collect_contact_candidates(resp.text, page_url))
                    time.sleep(random.uniform(0.2, 0.5))
            for url in add_common_contact_paths(base_url):
                candidates.append(CandidatePage(url=url, confidence=0.5, evidence=["common_path"]))
            for url in find_contact_from_sitemap(client, base_url):
                candidates.append(CandidatePage(url=url, confidence=1.0, evidence=["sitemap"]))
            for url in COMPANY_CONTACT_OVERRIDES.get(company_name, []):
                candidates.append(CandidatePage(url=url, confidence=2.0, evidence=["override"]))

            # de-dup and keep same domain (allow explicit overrides)
            uniq = {}
            for c in candidates:
                if "override" not in c.evidence and registrable_domain(c.url) != regdom:
                    continue
                if c.url not in uniq or c.confidence > uniq[c.url].confidence:
                    uniq[c.url] = c
            ranked = sorted(uniq.values(), key=lambda c: c.confidence, reverse=True)[:5]

            write_json(
                company_dir / "06_contact_page_candidates.json",
                {"candidates": [c.__dict__ for c in ranked]},
            )

            draft = draft_path.read_text(encoding="utf-8")
            plan_written = False
            for cand in ranked:
                try:
                    resp = client.get(cand.url, timeout=20.0)
                    resp.raise_for_status()
                except Exception:
                    continue
                soup = BeautifulSoup(resp.text, "lxml")
                form = soup.find("form")
                if not form:
                    continue
                fields = map_form_fields(form)
                if not fields:
                    continue
                plan = build_plan(company_name, draft, cand.url, fields)
                write_json(company_dir / "07_form_plan.json", plan)
                plan_written = True
                break

            if not plan_written and ranked and browser:
                for cand in ranked:
                    try:
                        page = browser.new_page()
                        page.goto(cand.url, wait_until="networkidle", timeout=45000)
                        page.wait_for_timeout(1500)
                        html = page.content()
                    except Exception:
                        try:
                            page.close()
                        except Exception:
                            pass
                        continue
                    soup = BeautifulSoup(html, "lxml")
                    form = soup.find("form")
                    if not form:
                        # iframe fallback
                        try:
                            for frame in page.frames:
                                if frame == page.main_frame:
                                    continue
                                html = frame.content()
                                soup = BeautifulSoup(html, "lxml")
                                form = soup.find("form")
                                if form:
                                    break
                        except Exception:
                            form = None
                    try:
                        page.close()
                    except Exception:
                        pass
                    if not form:
                        continue
                    fields = map_form_fields(form)
                    if not fields:
                        continue
                    plan = build_plan(company_name, draft, cand.url, fields)
                    write_json(company_dir / "07_form_plan.json", plan)
                    plan_written = True
                    break

            if not plan_written and ranked:
                # deep crawl: two-level internal link exploration
                deep_candidates = []
                first_level = []
                for cand in ranked[:3]:
                    try:
                        resp = client.get(cand.url, timeout=20.0)
                        resp.raise_for_status()
                    except Exception:
                        continue
                    deep_candidates.extend(collect_contact_candidates(resp.text, cand.url))
                    level_links = collect_internal_links(resp.text, cand.url, regdom, limit=3)
                    first_level.extend(level_links)
                    deep_candidates.extend([CandidatePage(url=u, confidence=0.6, evidence=["deep"]) for u in level_links])

                second_level = []
                for url in first_level[:6]:
                    try:
                        resp = client.get(url, timeout=20.0)
                        resp.raise_for_status()
                    except Exception:
                        continue
                    deep_candidates.extend(collect_contact_candidates(resp.text, url))
                    level_links = collect_internal_links(resp.text, url, regdom, limit=2)
                    second_level.extend(level_links)
                    deep_candidates.extend([CandidatePage(url=u, confidence=0.5, evidence=["deep2"]) for u in level_links])

                if deep_candidates:
                    uniq2 = {}
                    for c in deep_candidates:
                        if registrable_domain(c.url) != regdom:
                            continue
                        if c.url not in uniq2 or c.confidence > uniq2[c.url].confidence:
                            uniq2[c.url] = c
                    ranked = sorted(uniq2.values(), key=lambda c: c.confidence, reverse=True)[:5]
                if ranked and browser:
                    for cand in ranked:
                        try:
                            page = browser.new_page()
                            page.goto(cand.url, wait_until="networkidle", timeout=45000)
                            page.wait_for_timeout(1500)
                            html = page.content()
                        except Exception:
                            try:
                                page.close()
                            except Exception:
                                pass
                            continue
                        soup = BeautifulSoup(html, "lxml")
                        form = soup.find("form")
                        if not form:
                            try:
                                for frame in page.frames:
                                    if frame == page.main_frame:
                                        continue
                                    html = frame.content()
                                    soup = BeautifulSoup(html, "lxml")
                                    form = soup.find("form")
                                    if form:
                                        break
                            except Exception:
                                form = None
                        try:
                            page.close()
                        except Exception:
                            pass
                        if not form:
                            continue
                        fields = map_form_fields(form)
                        if not fields:
                            continue
                        plan = build_plan(company_name, draft, cand.url, fields)
                        write_json(company_dir / "07_form_plan.json", plan)
                        plan_written = True
                        break

            if not plan_written and ranked:
                write_json(
                    company_dir / "07_form_plan.json",
                    {"form_url": ranked[0].url, "fields": {}, "notes": "form not detected"},
                )
            if not plan_written and not ranked:
                write_json(company_dir / "07_form_plan.json", {"notes": "no form detected"})

            time.sleep(random.uniform(0.3, 0.7))

        if browser:
            browser.close()
        if playwright:
            playwright.stop()
    print("[phase4] DONE")


if __name__ == "__main__":
    run_phase4("data/out")
