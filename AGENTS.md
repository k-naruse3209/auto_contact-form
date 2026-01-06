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
  - normalized_company.json
  - discovered_urls.json
  - extracted_context.md
  - outreach_draft.md
  - form_plan.json
  - run_log.json
