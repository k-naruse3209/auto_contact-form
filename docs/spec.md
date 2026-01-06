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

## Phase 2: Context analysis
- Fetch: Top / 会社概要 / サービス(事業)紹介
- Extract: 事業概要, 想定顧客, 強み, IT/AI活用の余地（仮説）

## Phase 3: Outreach drafting
- Must include:
  - なぜ貴社か（根拠1〜2点：ページから引用要約）
  - 提案（1つのCTA）
  - 署名（DXAIの連絡先）
- Must avoid:
  - 誇大広告
  - 不要な個人情報の保存

## Phase 4: Form automation (Human-in-the-loop)
- Detect contact page(s)
- Use Playwright to open and fill the form fields
- Stop at "ready to submit" and take screenshot for human approval

## Rate limiting & Compliance
- Per-domain throttle + random jitter
- If page says "営業お断り" / "広告禁止" etc => skip and record
- If CAPTCHA / bot protection appears => stop and record
