# Rahul AI Team — Project Log

Last audited: 2026-08-15
Branch: `main`
Phase: **Phase 2 — live observation infrastructure**

This file is the canonical project status. Historical milestones are summarized once; current runtime blockers are tracked separately.

## Engineering rules

- Repository evidence beats assumptions.
- Deterministic safety gates beat model opinions.
- Missing, malformed, failed, stale or future-dated upstream state reduces authority and never increases it.
- Agent 05 remains fail-closed permission authority.
- Agent 06 remains read-only and always exposes `execution_enabled: false`.
- No broker order placement or trade-modification path belongs in this V1 runtime.
- Historical and analytics infrastructure is evidence-only.

## Architecture

`Agent 02 Technical` + `Agent 03 Macro/News` → `Agent 04 Decision` → `Agent 05 Permission` → `Agent 06 Alert Gateway (read-only)` → Trader View / historical evidence.

Agent 01 remains isolated legacy code. Keltner Bot 2.0 is a separate project.

## Integrated milestones

- PR #5: Deterministic V1 integrated.
- PR #6: Immutable historical prediction snapshots and append-only observations.
- PR #7: Outcome integrity and fail-closed corrupt-history handling.
- PR #8: Historical predictions require valid read-only Trader View input.
- PR #9: Outcome/source linkage and minimum horizon timing validation.
- PR #10: Agent 04 multi-timeframe alignment/conflict intelligence.
- PR #11: Trader View multi-timeframe presentation.
- PR #12: MTF intelligence persisted in historical prediction snapshots.
- PR #13: Read-only observation collector.
- PR #15: Provider-neutral XAUUSD reference-price evidence contract.
- PR #16: Gold API transport-free reference adapter.
- PR #17: Transport-free outcome collector.
- PR #18: Persisted outcome-history semantic integrity hardening.
- PR #19: Read-only evidence coverage analytics.
- PR #20: Deterministic per-horizon coverage and EMPTY/PARTIAL/COMPLETE status.
- Replay Engine foundation integrated; replay is advisory-only and keeps `execution_enabled: false`.
- Windows console compatibility fixed; deterministic local suite passed 100/100 on 2026-08-05.
- GitLab CI added as a duplicate deterministic test runner for push/merge-request validation.
- cTrader trendbar normalization hardened: the Open API fixed 1e-5 relative scale is explicit, broker symbol digits control final rounding, and deterministic tests cover 5-digit, non-default precision, timestamp, and invalid-input behavior. Merged to `main` as PR #5 on 2026-08-15 after exact-head GitHub Actions test success.

## Agent 02 runtime provider

### Current production path

Agent 02 now uses `get_default_provider()` rather than directly constructing Twelve Data.

The production provider is **Spotware's official `ctrader-open-api` Python SDK**. Runtime authentication requires:

- `CTRADER_CLIENT_ID`
- `CTRADER_CLIENT_SECRET`
- `CTRADER_ACCESS_TOKEN`

Optional runtime settings:

- `CTRADER_ACCOUNT_ID` — pin a specific authorized account.
- `CTRADER_ENV` — `demo` by default, or `live`.
- `CTRADER_SYMBOL` — `XAU/USD` by default.
- `CTRADER_REQUEST_COUNT` — 250 bars by default.

The provider discovers the authorized account, resolves the broker-specific XAU/USD symbol, obtains symbol precision, requests M5/M15/H1/H4 trendbars through `ProtoOAGetTrendbarsReq`, and normalizes them to the repository candle contract.

### Legacy provider

`TwelveDataProvider` remains only as an explicit test/migration shim. It is **not** a runtime fallback. A missing cTrader configuration now fails clearly instead of silently reaching the unimplemented Twelve Data shim.

## Current smoke workflow

`.github/workflows/ctrader-integration.yml` is a manual workflow.

It:

1. Checks out the selected branch.
2. Installs the pinned cTrader SDK.
3. Verifies the three required secrets are present without printing values.
4. Runs `python -u agent02.py` against the demo endpoint.

No `CTRADER_TOKEN_URL` or `CTRADER_CANDLES_URL` secret is required.

## Current Phase 2 gate

**Goal:** obtain the first trustworthy live observation sample.

Required evidence:

1. Successful cTrader demo authentication.
2. Authorized account discovery or explicit `CTRADER_ACCOUNT_ID` selection.
3. Broker-specific XAU/USD symbol resolution.
4. Non-empty M5/M15/H1/H4 trendbar responses.
5. Successful `data/current/agent02.json` generation.
6. Repeated observations sufficient to derive empirical freshness/timing tolerance.

Until those conditions are met, downstream analytics must not be treated as operational evidence.

## Remaining technical debt

1. Add refresh-token persistence only if the runtime needs automatic access-token renewal; the current smoke path intentionally uses the provisioned access token.
2. Add recorded real-response fixtures after the first successful demo smoke run.
3. Harden historical indexing only when evidence volume justifies it.
4. Validate observation/outcome lateness empirically from actual scheduled collection cadence.
5. Add directional/performance analytics only after trustworthy observation-time reference prices exist.

## Safety status

Agent 05 and Agent 06 remain unchanged by the cTrader runtime integration. The cTrader provider is read-only market-data infrastructure and does not place, modify or close trades.
