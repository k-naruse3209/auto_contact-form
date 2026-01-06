# AGENTS.md — Codex Instructions (Project: Web Research & Outreach)

## Operating rules (must)
- Default language: Japanese.
- Do not bypass CAPTCHAs, paywalls, login walls, or anti-bot protections.
- Do not click the final "Submit/Send" button in MVP. Stop at "ready-to-submit" state.
- Respect target site terms/robots; keep request rate low and include backoff.
- Store all decisions in docs/decisions.md.
- Every PR must include: tests (where applicable), logs schema update, and docs updates.

## Project commands
- Install: `uv sync` or `pip install -r requirements.txt`
- Run (dev): `python -m src.main --dry-run`
- Test: `pytest -q`

## Output contracts
- Persist per-company artifacts:
  - 01_search_results.json
  - 02_official_url.json
  - 03_pages_fetched.json
  - 04_extracted_context.md
  - 05_outreach_draft.md
  - 06_contact_page_candidates.json
  - 07_form_plan.json
  - 08_ready_to_submit.png
  - 99_run_log.json
