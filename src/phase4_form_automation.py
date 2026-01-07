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

FIELD_KEYWORDS = {
    "company": ["会社", "法人", "法人名", "貴社", "company", "organization"],
    "name": ["氏名", "担当", "お名前", "name"],
    "name_kana": ["カナ", "フリガナ", "ふりがな", "kana"],
    "name_hiragana": ["ひらがな", "hiragana"],
    "email": ["メール", "mail", "email"],
    "message": ["内容", "お問い合わせ", "問合せ", "本文", "message", "相談"],
    "phone": ["電話", "tel", "phone"],
    "address": ["住所", "所在地", "address"],
    "postal_code": ["郵便番号", "〒", "zip", "postal"],
    "department": ["部署", "department"],
    "role": ["役職", "role", "職種"],
    "website": ["URL", "website", "サイト", "web"],
    "privacy_consent": ["プライバシーポリシー", "個人情報", "privacy", "policy", "同意"],
    "inquiry_type": ["お問合せの種類", "お問い合わせ項目", "問合せ種別", "問合せ項目", "問い合わせ種別", "問い合わせ項目", "種別", "カテゴリ", "category", "inquiry type"],
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


def add_common_contact_paths(base_url: str) -> List[str]:
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/"
    paths = ["contact", "contact/", "inquiry", "inquiry/", "otoiawase", "support", "form"]
    return [urljoin(base, p) for p in paths]


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


def score_field(text: str, field_key: str, el_type: str) -> int:
    score = 0
    for kw in FIELD_KEYWORDS[field_key]:
        if kw.lower() in text.lower():
            score += 3
    if field_key == "email" and el_type == "email":
        score += 2
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
            label = get_label_text(el)
            placeholder = el.get("placeholder", "")
            name = el.get("name", "")
            ident = el.get("id", "")
            text = " ".join([label, placeholder, name, ident])
            score = score_field(text, key, el_type)
            if key == "privacy_consent" and el_type in ("checkbox", "radio"):
                score += 2
            if score > best[0]:
                best = (score, el)
        if best[1] is not None and best[0] > 0:
            selector = build_selector(best[1], form)
            if selector:
                fields[key] = {"selector": selector}
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
            value = SENDER_VALUES.get("inquiry_type")
        else:
            value = SENDER_VALUES.get(key)
        if value:
            plan_fields[key] = {"selector": meta["selector"], "value": value}
    return {
        "form_url": form_url,
        "fields": plan_fields,
        "notes": "ready-to-submit screenshot not implemented",
    }


def run_phase4(out_dir: str, max_companies: int = 50) -> None:
    """Phase4 implementation: form plan generation.

    Intended outputs per company:
      - 06_contact_page_candidates.json
      - 07_form_plan.json
      - 08_ready_to_submit.png (not generated)
    """
    base = Path(out_dir)
    company_dirs = sorted([p for p in base.iterdir() if p.is_dir()])[:max_companies]
    print(f"[phase4] start: companies={len(company_dirs)}")

    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
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

            try:
                home_resp = client.get(base_url, timeout=20.0)
                home_resp.raise_for_status()
                home_html = home_resp.text
            except Exception:
                write_json(company_dir / "06_contact_page_candidates.json", {"candidates": []})
                write_json(company_dir / "07_form_plan.json", {"notes": "failed to fetch home"})
                continue

            candidates = collect_contact_candidates(home_html, base_url)
            for url in add_common_contact_paths(base_url):
                candidates.append(CandidatePage(url=url, confidence=0.5, evidence=["common_path"]))
            for url in COMPANY_CONTACT_OVERRIDES.get(company_name, []):
                candidates.append(CandidatePage(url=url, confidence=2.0, evidence=["override"]))

            # de-dup and keep same domain
            uniq = {}
            regdom = registrable_domain(base_url)
            for c in candidates:
                if registrable_domain(c.url) != regdom:
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

            if not plan_written:
                write_json(company_dir / "07_form_plan.json", {"notes": "no form detected"})

            time.sleep(random.uniform(0.3, 0.7))

    print("[phase4] DONE")


if __name__ == "__main__":
    run_phase4("data/out")
