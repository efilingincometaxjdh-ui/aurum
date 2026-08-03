# Contributing — Rahul AI Team

This repository contains safety-critical trading intelligence and evidence infrastructure.
Before contributing, read:

1. `ENGINEERING_RULES.md`
2. `PROJECT_LOG.md`
3. `ROADMAP.md` (if present)
4. `PHASE2_PLAN.md`

## Workflow

- Work on a feature branch and open a Merge Request.
- Keep MRs small, self-contained, and focused.
- Do **not** modify Agent05 or Agent06 unless explicitly instructed.
- Never add broker/execution code or autonomous trade paths.

## Tests and CI

- Local and CI test command:

  ```bash
  python -m unittest discover -s tests -v
  ```

- All tests must pass before merging; do not bypass red CI.
- GitLab CI mirrors the existing GitHub Actions test workflow using Python 3.11.

## Documentation and project log

- Any meaningful change to architecture, contracts, safety behavior, data formats,
  or CI coverage must be recorded in `PROJECT_LOG.md`.
- Keep `PROJECT_LOG.md` synchronized with the current repository state.
- If you add or adjust CI jobs, document the new evidence there.

## Secrets and safety

- Never commit secrets, API keys, or credentials.
- Execution must remain disabled; this repository must not place, modify,
  or close live trades.
