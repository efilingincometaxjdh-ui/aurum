# Aurum Engineering Rules

This repository contains safety-critical trading intelligence and evidence infrastructure. These rules are **permanent**, **authoritative**, and apply to all contributors, including AI-assisted changes.

## Core authority and documentation

1. **PROJECT_LOG.md is the authoritative engineering record.**  
   Always consult and update `PROJECT_LOG.md` for architecture, contracts, safety decisions, CI evidence, and milestones.

2. **PHASE2_PLAN.md documents original intent only.**  
   Use `PHASE2_PLAN.md` to understand initial design goals. If it disagrees with `PROJECT_LOG.md`, the log wins.

3. **Update PROJECT_LOG.md after every meaningful engineering milestone.**  
   Any change to architecture, contracts, safety behavior, data format, or CI/test coverage must be reflected in `PROJECT_LOG.md`.

4. **Preserve backward compatibility unless explicitly approved.**  
   Schema changes, contract changes, or public API changes require an explicit decision in `PROJECT_LOG.md` and a clear migration story.

5. **Minimize architecture drift and document any intentional design changes.**  
   Do not introduce new patterns, layers, or cross-cutting concerns without recording the rationale and impact in `PROJECT_LOG.md`.

## Code reuse and module design

6. **Reuse existing code before creating new modules.**  
   Prefer extending or refactoring existing helpers, providers, and contracts instead of adding new, overlapping modules.

7. **Do not duplicate implementations.**  
   If the same behavior exists elsewhere (e.g., validation, normalization, time handling, provider abstraction), factor it into shared code instead of copying.

8. **Preserve and respect existing contracts.**  
   Changes to data envelopes, provider contracts, or agent interfaces must be additive or explicitly documented as breaking in `PROJECT_LOG.md`.

## Authority, safety, and execution

9. **Agent05 is always the final fail-closed authority.**  
   All permission decisions must flow through Agent05. Invalid, stale, unknown, or degraded upstream state must fail closed.

10. **Agent06 is always read-only.**  
    Agent06 may expose alerts, status, and trader-facing views, but must never hold or exercise execution authority.

11. **Never enable autonomous trade execution.**  
    This repository must not place, modify, or close live trades. No broker API clients or order-routing logic are allowed.

12. **Historical, replay, analytics, and ML layers are advisory only and must never increase trading authority.**  
    These layers may inform human decisions or enrich evidence but cannot upgrade permissions, bypass Agent05, or introduce new execution paths.

13. **Do not modify Agent05 or Agent06 unless explicitly instructed.**  
    Changes to these agents require explicit approval and must be carefully documented in `PROJECT_LOG.md` with tests that prove fail-closed behavior.

## Historical data and evidence

14. **Historical data must be append-only.**  
    Do not rewrite or delete historical JSONL lines. Corrections must be represented as new evidence, not in-place edits.

15. **Store one candle per JSONL line with UTC timestamps.**  
    Historical and replay data must:
    - Use one logical record per line.  
    - Use timezone-aware UTC timestamps (ISO-8601).  
    - Avoid ambiguous local times.

16. **Historical, replay, and analytics code must remain evidence-first.**  
    These paths may reject or downgrade authority, but must not introduce execution or upgrade permissions.

## Market data providers

17. **Prefer provider abstraction (`IMarketDataProvider`) for all market data sources.**  
    Access to external or simulated market data must go through the provider interface, not ad-hoc HTTP clients or SDKs.

18. **Reuse the existing Twelve Data integration before adding new providers.**  
    If Twelve Data already satisfies the need, extend or configure it rather than creating an additional equivalent integration.

19. **Future providers (cTrader, replay, others) must implement the same provider interface.**  
    All providers must:
    - Implement the shared provider contract.  
    - Return normalized, validated data envelopes.  
    - Respect existing safety and freshness rules.

## Testing, CI, and secrets

20. **Write deterministic, offline-capable tests using mocks or fake providers.**  
    Tests must not depend on live network calls, real-time market conditions, or external services.

21. **Never bypass failing tests.**  
    Do not disable tests, ignore failures, or merge with red CI for convenience. Fix the underlying issue or explicitly document why a test is being changed.

22. **Never commit secrets or API keys.**  
    All credentials must live outside the repository (e.g., CI variables, local env vars). If a secret is accidentally committed, rotate it immediately and record the incident in `PROJECT_LOG.md`.

## Merge Request expectations

23. **Every Merge Request must include the following in its description:**

    - **Summary** — What changed and why.  
    - **Tests executed** — Exact commands or CI jobs and their results.  
    - **Safety review** — Impact on permissions, agents, data contracts, and execution invariants.  
    - **Files changed** — High-level list of key modules/contracts affected.  
    - **Remaining technical debt** — Known follow-ups that were intentionally deferred.

24. **MRs must be clean and self-contained.**  
    Avoid drive-by refactors in unrelated areas. Each MR should be reviewable without guessing intent.

## Repository workflow

All contributors (including AI tooling) must follow this workflow when making changes:

1. **Read in this order:**
   1. `ENGINEERING_RULES.md` (this file)  
   2. `PROJECT_LOG.md`  
   3. `ROADMAP.md` (if present)  
   4. `PHASE2_PLAN.md`

2. **Inspect the repository.**  
   Understand the current implementation, existing providers, contracts, and tests. Prefer reading code and tests over guessing.

3. **Implement only the next unfinished milestone.**  
   Do not skip ahead in the roadmap or invent new milestones. Choose the smallest meaningful next step consistent with `PROJECT_LOG.md` and these rules.

4. **Run tests and fix failures.**  
   Use the existing test suite (and any new targeted tests) to validate your changes. Do not merge while tests are red.

5. **Update `PROJECT_LOG.md`.**  
   After a meaningful engineering milestone, record the change, its CI evidence, and any contract/safety updates in `PROJECT_LOG.md`.

6. **Prepare a clean Merge Request.**  
   Ensure the MR description satisfies the template above, the diff is focused, tests are passing, and safety invariants are preserved.

## Non-negotiable safety rule

- **Do not modify Agent05 or Agent06 unless explicitly instructed.**  
- **Never enable autonomous trade execution.**  

Any change that risks these invariants must be rejected or escalated and clearly documented in `PROJECT_LOG.md`.
