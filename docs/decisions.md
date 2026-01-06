# Decisions

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
