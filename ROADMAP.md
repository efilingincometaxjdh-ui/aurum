# Rahul AI Team — Roadmap (Phase 2 focus)

This roadmap captures high-level intent only. The authoritative record of
what is actually implemented and its safety evidence is always `PROJECT_LOG.md`.

## Current phase: Phase 2 — Evidence infrastructure

- Maintain deterministic, fail-closed evidence collection for XAUUSD.
- Preserve the separation:
  - Intelligence → Decision → Permission → Alert Gateway (read-only) → Trader View.
- Keep all historical data append-only and timezone-aware.

## Near-term milestones

1. Keep CI and tests green on both GitHub and GitLab.
2. Improve visibility into test and evidence coverage (read-only analytics).
3. Document collection cadence and outcome lateness tolerance once chosen.
4. Harden historical storage/indexing when evidence volume justifies it.

## Non-goals

- No autonomous trade execution.
- No broker integration or order-routing logic.
- No changes to Agent05 or Agent06 without explicit approval and log updates.
