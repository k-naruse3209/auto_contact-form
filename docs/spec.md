# docs/spec.md — Web Research & Outreach (JP, Form-only, Human-submit)

## Goal
企業名CSVから、公式URL特定→事業分析→協業依頼文作成→問い合わせフォーム自動入力（送信直前で停止）まで一気通貫で行う。

## Scope (MVP)
- 日本企業のみ
- 送信チャネル：問い合わせフォームのみ（公開メール送信は対象外）
- 文面：日本語のみ
- 最終送信：人間がクリック（自動クリックしない）
- 1日最大：2000社

## Inputs
- data/company_names.csv
  - company_name (必須)
  - optional: hint_industry, notes

## Outputs (per company)
- data/out/{company_slug}/
  - 01_search_results.json
  - 02_official_url.json
  - 03_pages_fetched.json
  - 04_extracted_context.md
  - 05_outreach_draft.md
  - 06_contact_page_candidates.json
  - 07_form_plan.json
  - 08_ready_to_submit.png
  - 99_run_log.json

## Phase 1: URL discovery
- Use Search API (Google CSE / Tavily) to find official domain
- Produce top candidates with evidence and confidence score
### Outputs
- 01_search_results.json
- 02_official_url.json
- 02_official_url_candidates_scored.json
### Sample
```json
{
  "company_name": "株式会社サンプル",
  "items": [
    {
      "link": "https://example.co.jp/",
      "title": "株式会社サンプル",
      "snippet": "事業概要の説明...",
      "displayLink": "example.co.jp"
    }
  ]
}
```

## Phase 2: Context analysis
- Fetch: Top / 会社概要 / サービス(事業)紹介
- Extract: 事業概要, 想定顧客, 強み, IT/AI活用の余地（仮説）
### Outputs
- 03_pages_fetched.json
- 04_extracted_context.md
### Sample
```json
{
  "pages": [
    {
      "url": "https://example.co.jp/company",
      "title": "会社概要",
      "status_code": 200,
      "fetched_at": "2026-01-06T12:00:00Z",
      "content_path": "data/out/sample/03_pages_fetched/company.html"
    }
  ]
}
```
```markdown
# 株式会社サンプル

## 事業概要
- B2B向けのSaaSを提供

## 想定顧客
- 中堅製造業

## 強み
- 導入実績500社

## IT/AI活用の余地（仮説）
- 問い合わせ対応の自動化
```

## Phase 3: Outreach drafting
- Must include:
  - なぜ貴社か（根拠1〜2点：ページから引用要約）
  - 提案（1つのCTA）
  - 署名（DXAIの連絡先）
- Must avoid:
  - 誇大広告
  - 不要な個人情報の保存
### Outputs
- 05_outreach_draft.md
### Sample
```markdown
件名: 問い合わせ業務の自動化ご提案

株式会社サンプル ご担当者様

貴社の「導入実績500社」という実績に触発され、
問い合わせ対応の自動化について伴走支援をご提案したくご連絡しました。

ご興味あれば15分だけオンラインでお話できれば幸いです。

株式会社DXAIソリューションズ
担当：成瀬
https://dxai-sol.co.jp/
k-naruse@dxai-sol.co.jp

不要でしたら本メールは破棄してください。
```

## Phase 4: Form automation (Human-in-the-loop)
- Detect contact page(s)
- Use Playwright to open and fill the form fields
- Stop at "ready to submit" and take screenshot for human approval
### Outputs
- 06_contact_page_candidates.json
- 07_form_plan.json
- 08_ready_to_submit.png

## Implementation plan (Phase2-4)
### Phase 2
- Inputs: 02_official_url.json, site pages
- Steps: fetch Top/会社概要/サービス, sanitize HTML, extract key facts
- Outputs: 03_pages_fetched.json, 04_extracted_context.md

### Phase 3
- Inputs: 04_extracted_context.md, prompts/outreach.md
- Steps: draft outreach with evidence anchors and opt-out line
- Outputs: 05_outreach_draft.md

### Phase 4
- Inputs: 06_contact_page_candidates.json, 05_outreach_draft.md
- Steps: open contact page, map fields, fill, stop before submit, take screenshot
- Outputs: 07_form_plan.json, 08_ready_to_submit.png
### Sample
```json
{
  "candidates": [
    {
      "url": "https://example.co.jp/contact",
      "confidence": 0.82,
      "evidence": ["link text contains 問い合わせ"]
    }
  ]
}
```
```json
{
  "form_url": "https://example.co.jp/contact",
  "fields": {
    "name": "DXAI",
    "email": "contact@dxai.example"
  },
  "notes": "送信直前で停止"
}
```

## Rate limiting & Compliance
- Per-domain throttle + random jitter
- If page says "営業お断り" / "広告禁止" etc => skip and record
- If CAPTCHA / bot protection appears => stop and record
