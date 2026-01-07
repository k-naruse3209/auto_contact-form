# Decisions

## 2026-01-07
- Expanded Phase4 field keyword matching to cover "名前/onamae" and "mailadd" and deprioritize email confirmation fields.
- Allowed Phase4 contact overrides to use a different domain when explicitly configured.
- Narrowed Phase4 missing-required checks to name/email/message to avoid false positives when no company field exists.
- Added optional Phase4 company allowlist support for targeted reruns.

## 2026-01-06
- Added `AGENTS.md` and `CLAUDE.md` to capture Codex/Claude project instructions.
- Relaxed pandas pin from `==2.1.4` to `>=2.2.0` in `requirements.txt`.
- Added `src/main.py` as the project entrypoint and aligned README usage with `python -m src.main --dry-run`.
- Added `.env.example` for reproducible setup.
- Aligned `AGENTS.md` output contracts with `docs/spec.md` artifact naming.
- Added Phase2/3/4 skeleton modules and wired them into `src/main.py`.
- Added explicit `greenlet==3.0.1` pin and `pytest==8.3.3` to `requirements.txt`.
- Added `.venv*` to `.gitignore` and a smoke test for dry-run output.
- Documented per-phase output schemas in `docs/spec.md` and allowed `--dry-run` with `--phase1-only`.
- Added sample output templates to `docs/spec.md` and made `tldextract` offline-safe.
- Aligned the Phase3 sample draft in `docs/spec.md` with `prompts/outreach.md` signature requirements.
- Added phase-only run logging and an opt-out line requirement in `prompts/outreach.md`.
- Added opt-out line to the Phase3 sample and documented Phase2-4 implementation plan in `docs/spec.md`.
- Added Phase2 extraction template and Phase4 field-mapping rules in `docs/spec.md`.
- Documented Phase2 page scoring rules and Phase4 input value priorities in `docs/spec.md`.
- Implemented Phase2 fetching/extraction and strengthened Phase1 domain penalties.
- Implemented Phase3 draft generation with signature and opt-out line.
- Updated outreach template to the provided draft and aligned Phase3 generation with it.
- Tightened Phase2 extraction filters and added meta/title fallback for cleaner evidence.
- Switched Phase3 drafting to Gemini API (Gemini 3 Flash) and added API key configuration.
- Updated default Gemini model to `gemini-3-flash-preview`.
- Ensured Phase3 loads `.env` before calling Gemini.
- Implemented Phase4 contact candidate discovery and form plan generation.
- Added a Phase4 dashboard generator for field/value review.
- Added inquiry type mapping to prefer "業務提携/協業" and fallback to "その他".
- Avoided mapping inquiry type/consent to non-select checkbox fields.
- Restricted inquiry_type to fields containing inquiry keywords and safe options only.
- Skipped inquiry_type when no select/radio options are found.
- Added sitemap fallback and form_url fallback when form is not detected.
- Added Phase4 report and summary CSV generators.
- Expanded Phase1 queries with industry hints and consulting keyword for English names.
- Added a Kitamura & Company alias query for better disambiguation.
