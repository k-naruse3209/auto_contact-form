# CLAUDE.md — Project Memory (Web Research & Outreach)

## Single source of truth
- Specs live in docs/spec.md and docs/acceptance.md.
- Architecture lives in docs/architecture.md.
- Decisions live in docs/decisions.md.

## Safety & compliance (non-negotiable)
- Human approval required before final submission.
- No CAPTCHA bypass; if CAPTCHA appears, stop and record.
- Rate limit + random jitter; per-domain quota.
- Collect only necessary public info; do not store sensitive PII beyond what is needed.

## Writing style for outreach
- Polite, specific, short.
- Always include why-us/why-you based on extracted evidence.
- Provide an opt-out line when appropriate.

## Deliverables per phase
- Phase1: URL candidates with confidence + evidence
- Phase2: business summary + pain points + synergy hypotheses
- Phase3: outreach draft with evidence anchors
- Phase4: form-fill plan + screenshot + ready-to-submit
