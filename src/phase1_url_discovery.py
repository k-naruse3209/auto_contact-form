#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import os
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd
import tldextract
from dotenv import load_dotenv
from rich.console import Console
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

console = Console()
TLD_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=None)

DEFAULT_NEGATIVE_DOMAINS = {
    "wikipedia.org", "ja.wikipedia.org",
    "maps.google.", "google.com",
    "prtimes.jp",
    "onecareer.jp", "biz.ne.jp", "sakura.ne.jp",
    "brandcloud.co.jp", "kenkatsu10.jp",
    "xn--",  # punycode heuristic (not block, just lower score)
    "tiktok.com", "facebook.com", "x.com", "twitter.com", "instagram.com",
    "wantedly.com", "en-gage.net", "doda.jp", "rikunabi.com", "mynavi.jp", "indeed.com",
    "note.com", "ameblo.jp",
}

CONTACTISH_HINTS = ["会社概要", "企業情報", "公式", "コーポレート", "サービス", "事業", "product", "company", "about"]

@dataclass
class Candidate:
    link: str
    title: str
    snippet: str
    displayLink: str
    rank: int
    score: int
    evidence: List[str]
    registrable_domain: str

def slugify_jp(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[　\s]+", "-", text)  # spaces -> hyphen
    text = re.sub(r"[^\w\-ぁ-んァ-ン一-龥]", "", text)  # keep jp chars, word, hyphen
    return text[:80] if text else "unknown"

def normalize_company(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "", name)
    name = name.replace("株式会社", "").replace("(株)", "").replace("（株）", "")
    name = name.replace("有限会社", "").replace("(有)", "").replace("（有）", "")
    return name

def registrable_domain(url: str) -> str:
    # Avoid network fetches for PSL; rely on bundled snapshot.
    ext = TLD_EXTRACTOR(url)
    # ext.domain + ext.suffix is registrable-ish, e.g., "example.co.jp"
    if not ext.domain or not ext.suffix:
        return ""
    return f"{ext.domain}.{ext.suffix}"

def is_jp_domain(domain: str) -> bool:
    return domain.endswith(".jp") or domain.endswith(".co.jp") or domain.endswith(".ne.jp") or domain.endswith(".or.jp") or domain.endswith(".go.jp")

def score_candidate(company_norm: str, cand: Dict[str, Any], rank: int) -> Candidate:
    link = cand.get("link", "") or ""
    title = cand.get("title", "") or ""
    snippet = cand.get("snippet", "") or ""
    display = cand.get("displayLink", "") or ""
    regdom = registrable_domain(link) or registrable_domain("https://" + display)
    evidence = []
    score = 0

    # Base: higher rank => slightly higher score
    score += max(0, 30 - rank * 3)
    evidence.append(f"rank={rank}")

    hay = (title + " " + snippet + " " + display).lower()

    # Company name presence
    if company_norm and company_norm.lower() in re.sub(r"\s+", "", hay):
        score += 40
        evidence.append("company_name_match(+40)")

    # JP domain preference
    if regdom and is_jp_domain(regdom):
        score += 25
        evidence.append("jp_domain(+25)")

    # HTTPS preference
    if link.startswith("https://"):
        score += 5
        evidence.append("https(+5)")

    # About/company-ish hints
    for h in CONTACTISH_HINTS:
        if h.lower() in hay:
            score += 5
            evidence.append(f"hint:{h}(+5)")
            break

    # Negative domains (soft penalty)
    for bad in DEFAULT_NEGATIVE_DOMAINS:
        if bad in display or bad in link:
            score -= 80
            evidence.append(f"negative_domain:{bad}(-80)")
            break

    # Company-specific domain hints
    if company_norm and "kitamura&company" in company_norm.lower():
        if "ykaci.com" in link or "ykaci.com" in display:
            score += 60
            evidence.append("preferred_domain:ykaci.com(+60)")
        if "kitamura.co.jp" in link or "kitamura.co.jp" in display:
            score -= 40
            evidence.append("deprioritize_domain:kitamura.co.jp(-40)")

    # If no registrable domain, penalize
    if not regdom:
        score -= 30
        evidence.append("no_reg_domain(-30)")

    # Prefer top-level pages over deep paths
    try:
        path_depth = len([p for p in re.split(r"/+", re.sub(r"^https?://[^/]+", "", link)) if p])
        if path_depth > 2:
            score -= 5
            evidence.append("deep_path(-5)")
    except Exception:
        pass

    return Candidate(
        link=link,
        title=title,
        snippet=snippet,
        displayLink=display,
        rank=rank,
        score=score,
        evidence=evidence,
        registrable_domain=regdom or "",
    )

@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=20),
)
def google_cse_search(client: httpx.Client, api_key: str, cx: str, q: str, num: int = 5) -> Dict[str, Any]:
    # Endpoint & required params per Google docs:
    # https://www.googleapis.com/customsearch/v1?key=...&cx=...&q=...
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cx, "q": q, "num": str(num)}
    r = client.get(url, params=params, timeout=20.0)
    if r.status_code in (429, 500, 502, 503, 504):
        # Let tenacity handle retry for transient errors by raising
        raise httpx.TransportError(f"retryable status={r.status_code}")
    r.raise_for_status()
    return r.json()

def build_queries(company_name: str, hint_industry: Optional[str] = None) -> List[str]:
    # Minimal set: keep cost controlled; expand later if needed
    queries = [
        f"{company_name} 公式サイト",
        f"{company_name} 会社概要",
        f"{company_name} 事業内容",
    ]
    if company_name == "Kitamura & Company":
        queries.append("株式会社Kitamura&Company 公式サイト")
    if hint_industry:
        queries.append(f"{company_name} {hint_industry}")
    # Add a generic consulting hint for ambiguous English names
    if re.search(r"[A-Za-z&]", company_name):
        queries.append(f"{company_name} コンサル会社")
    # de-dup
    seen = set()
    deduped = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped

def pick_best(company_name: str, items: List[Dict[str, Any]]) -> Tuple[Optional[Candidate], List[Candidate]]:
    company_norm = normalize_company(company_name)
    scored: List[Candidate] = []
    for i, it in enumerate(items, start=1):
        scored.append(score_candidate(company_norm, it, rank=i))
    scored.sort(key=lambda c: c.score, reverse=True)
    best = scored[0] if scored else None
    return best, scored

def ensure_out_dir(base: Path, company_name: str) -> Path:
    slug = slugify_jp(company_name)
    out = base / slug
    out.mkdir(parents=True, exist_ok=True)
    return out

def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def run_phase1(
    csv_path: str,
    out_dir: str,
    max_companies: int = 50,
    sleep_min: float = 0.2,
    sleep_max: float = 0.6,
    num: int = 5,
    api_key: Optional[str] = None,
    cx: Optional[str] = None,
) -> None:
    load_dotenv()
    api_key = (api_key or os.getenv("GOOGLE_CSE_API_KEY", "")).strip()
    cx = (cx or os.getenv("GOOGLE_CSE_CX", "")).strip()
    if not api_key or not cx:
        console.print("[red]Missing GOOGLE_CSE_API_KEY or GOOGLE_CSE_CX in .env[/red]")
        raise SystemExit(1)

    in_path = Path(csv_path)
    out_base = Path(out_dir)
    out_base.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_path)
    if "company_name" not in df.columns:
        raise SystemExit("CSV must contain column: company_name")

    companies = df["company_name"].dropna().astype(str).tolist()[: max_companies]
    console.print(f"[cyan]Phase1 URL discovery start: companies={len(companies)}[/cyan]")

    summary = {"total": len(companies), "success": 0, "fail": 0, "items": []}

    with httpx.Client(headers={"User-Agent": "DXAI-OutreachBot/0.1 (contact: k-naruse@dxai-sol.co.jp)"}) as client:
        for idx, name in enumerate(companies, start=1):
            out_dir = ensure_out_dir(out_base, name)
            run_log = {"company_name": name, "started_at": time.time(), "queries": [], "status": "unknown"}

            try:
                all_items: List[Dict[str, Any]] = []
                hint = None
                if "hint_industry" in df.columns:
                    try:
                        hint = df.loc[df["company_name"] == name, "hint_industry"].dropna().astype(str).iloc[0]
                    except Exception:
                        hint = None
                queries = build_queries(name, hint_industry=hint)
                for q in queries:
                    data = google_cse_search(client, api_key, cx, q, num=num)
                    items = data.get("items", []) or []
                    run_log["queries"].append({"q": q, "returned": len(items)})
                    all_items.extend(items)

                    # jittered sleep to be polite + reduce burst
                    time.sleep(random.uniform(sleep_min, sleep_max))

                # Save raw results (dedupe lightly by link)
                seen = set()
                deduped = []
                for it in all_items:
                    link = it.get("link", "")
                    if link and link not in seen:
                        seen.add(link)
                        deduped.append(it)

                write_json(out_dir / "01_search_results.json", {"company_name": name, "items": deduped})

                best, scored = pick_best(name, deduped)
                write_json(out_dir / "02_official_url.json", {
                    "company_name": name,
                    "official_url": best.link if best else None,
                    "registrable_domain": best.registrable_domain if best else None,
                    "confidence_score": best.score if best else None,
                    "evidence": best.evidence if best else None,
                })
                write_json(out_dir / "02_official_url_candidates_scored.json", [c.__dict__ for c in scored[:20]])

                run_log["status"] = "success" if best else "no_candidate"
                summary["success"] += 1 if best else 0
                summary["fail"] += 0 if best else 1
                summary["items"].append({"company_name": name, "official_url": best.link if best else None})

                console.print(f"[green]{idx}/{len(companies)} OK[/green] {name} -> {best.link if best else 'None'}")

            except Exception as e:
                run_log["status"] = "fail"
                run_log["error"] = repr(e)
                summary["fail"] += 1
                summary["items"].append({"company_name": name, "official_url": None, "error": repr(e)})
                console.print(f"[red]{idx}/{len(companies)} FAIL[/red] {name} :: {e}")

            finally:
                run_log["ended_at"] = time.time()
                write_json(out_dir / "99_run_log.json", run_log)

    write_json(out_base / "phase1_summary.json", summary)
    console.print("[cyan]DONE[/cyan] -> data/out/phase1_summary.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/company_names.csv")
    ap.add_argument("--out", default="data/out")
    ap.add_argument("--max-companies", type=int, default=50)
    ap.add_argument("--sleep-min", type=float, default=0.2)
    ap.add_argument("--sleep-max", type=float, default=0.6)
    ap.add_argument("--num", type=int, default=5, help="Results per query")
    args = ap.parse_args()

    run_phase1(
        csv_path=args.csv,
        out_dir=args.out,
        max_companies=args.max_companies,
        sleep_min=args.sleep_min,
        sleep_max=args.sleep_max,
        num=args.num,
    )

if __name__ == "__main__":
    main()
