# Rahul AI Team — Project Log

Last audited: 2026-08-05
Branch: `phase2/evidence-coverage-readability`
Phase: **Phase 2 — evidence infrastructure**

This file is the persistent source of truth for architecture, recovery evidence, current health, contracts, safety policy and next work.

## Loop Engineering protocol

**Inspect → Plan → Build → Test → Observe → Critique → Fix → Retest → Integrate → Monitor → Repeat**.

Rules:
- Repository evidence beats assumptions.
- Deterministic safety gates beat model opinions.
- Generated state uses the normalized atomic `utils/json_writer.py` envelope.
- Missing, malformed, failed, stale, future-dated or degraded upstream state reduces authority, never increases it.
- No autonomous execution/broker integration.
- Agent 05 fails closed on `NO_TRADE`, invalid input, unknown decision/risk states, invalid confidence, EXTREME risk and stale Agent 04 state.
- Agent 06 is read-only and always exposes `execution_enabled: false`.
- Historical/analytics infrastructure is evidence-only and must never increase trading authority.

## Architecture

`Agent 02 Technical` + `Agent 03 Macro/News` → **Agent 04 Decision** → **Agent 05 Permission** → **Agent 06 Alert Gateway (read-only)** → **Trader View / historical evidence**.

Agent 01 remains isolated. Keltner Bot 2.0 is a separate next project.

## Deterministic V1 status

PR #5 merged to `main` on 2026-07-30 after clean effective-HEAD CI (Tests #75). Deterministic V1 is integrated.

### Agent 02 — XAUUSD Technical Intelligence
Status: BUILT.

Produces normalized M5/M15/H1/H4 state with EMA20, EMA50, RSI14, ATR14, ADX14 and structure.

### Agent 03 — XAUUSD Macro/News Intelligence
Status: BUILT v0.2.

Explicit observed-headline `news_risk`: LOW with no high-impact headlines, MEDIUM for 1–2, HIGH for 3+. RSS scoring cannot emit EXTREME; future validated event-calendar evidence is required for [...]

### Agent 04 — Decision Engine
Status: INTEGRATED v0.4.

Multi-timeframe fusion weights H4=4, H1=3, M15=2, M5=1. Agent 02 max age 20 minutes; Agent 03 max age 6 hours. Invalid/stale intelligence fails to `NO_TRADE`, confidence 0, EXTREME risk and FAILED[...]

### Agent 05 — Permission Engine
Status: INTEGRATED v0.2.

Final deterministic safety gate. Agent 04 max age 15 minutes. Invalid, failed, unknown, stale or unsafe decision state fails closed. Degraded state produces CAUTION only.

### Agent 06 — Alert Gateway
Status: INTEGRATED v0.1.

Read-only downstream boundary consuming `permission.json`. Agent 05 state max age 15 minutes. Missing/malformed/failed/stale/future-dated/unknown permission state emits `BLOCK_TRADING` and FAILED [...]

### Trader View
Status: INTEGRATED v0.2.

Trader View exposes Agent04 `ALIGNED / CONFLICT / NEUTRAL`, per-timeframe trends, higher-timeframe conflict, lower-timeframe conflict and higher-vs-lower conflict directly to the trader-readable r[...]

### Agent 01 — Legacy LLM Macro Analyst
Status: ISOLATED / LEGACY.

It overlaps Agent 03 and contains a legacy bot-action path that conflicts with intelligence → decision → permission separation. Do not integrate without a deliberate overlap-resolution decisio[...]

## CI / test evidence

- `.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on push and pull request using Python 3.11.
- Recovery HEAD `bdb0e7e`: Tests #43 SUCCESS.
- Multi-timeframe/fail-closed HEAD `1f988e98`: Tests #53 SUCCESS.
- Freshness/risk/end-to-end HEAD `06d79b5d`: Tests #67 SUCCESS.
- Deterministic V1 effective HEAD `8501a1d0`: Tests #75 SUCCESS; PR #5 merged.
- Phase 2 historical observation HEAD `27f54dca`: Tests #86 SUCCESS; PR #6 merged.
- Outcome-integrity HEAD `7289267b`: Tests #93 SUCCESS; PR #7 merged.
- Trader View boundary HEAD `893fd357`: Tests #100 SUCCESS; PR #8 merged.
- Outcome-timing HEAD `726dcdbc`: Tests #107 SUCCESS; PR #9 merged.
- Agent04 MTF intelligence HEAD `78ade145`: Tests #112 SUCCESS; PR #10 merged after clean exact-HEAD CI, mergeability check and zero unresolved review threads.
- Trader View MTF presentation HEAD `7e242bbd`: Tests #119 SUCCESS; PR #11 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads.
- Historical MTF evidence HEAD `7720bc5b`: Tests #127 SUCCESS; PR #12 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads.
- Safe observation orchestration HEAD `ab1d70d9`: Tests #134 SUCCESS; PR #13 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads.
- Reference-price evidence contract HEAD `100465d5`: Tests #146 SUCCESS; PR #15 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads. PR #14 was deliberately c[...]
- Gold API reference adapter HEAD `feae6fbb`: Tests #152 SUCCESS; PR #16 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads. Adapter is transport-free and re[...]
- Outcome orchestration HEAD `53cbeee7`: Tests #158 SUCCESS; PR #17 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads. Collector remains transport-free and [...]
- Existing outcome-history semantic-integrity final HEAD `0bba99ba`: Tests #168 SUCCESS; PR #18 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads.
- Evidence coverage analytics initial code/test HEAD `c84b2b9f`: PR #19 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads.
- Evidence coverage readability HEAD `720e05e`: PR #20 merged to `main`; it provides deterministic per-horizon missing counts and EMPTY/PARTIAL/COMPLETE status while remaining read-only and fail-c[...]
- Replay Engine foundation HEAD `4efd22d`: integrated to `main`. Advisory-only replay of append-only UTC candles from JSONL via `history/replay.py` and `tests/test_replay.py` supports play, pause,[...]
- Evidence coverage readability HEAD `720e05e`: PR #20 merged to `main`; it provides deterministic per-horizon missing counts and EMPTY/PARTIAL/COMPLETE status while remaining read-only and fail-closed.
- Replay Engine foundation HEAD `4efd22d`: integrated to `main`. Advisory-only replay of append-only UTC candles from JSONL via `history/replay.py` and `tests/test_replay.py` supports play, pause, resume and step, emits `mode: REPLAY` with `execution_enabled: false`, and does not modify Agent05 or Agent06.
- Windows console compatibility: Agent02 success diagnostics use ASCII-only `[OK]` output. The complete local suite passed: 100 tests, 0 failures (2026-08-05).
- GitLab CI added: `.gitlab-ci.yml` mirrors `.github/workflows/tests.yml` and runs
  `python -m unittest discover -s tests -v` using Python 3.11 on push and merge request.
- Infrastructure docs added: `requirements.txt` (placeholder), `.gitignore`, `CONTRIBUTING.md`,
  and `ROADMAP.md` (Phase 2 aligned) for contributor guidance; these do not change runtime
  behavior or trading authority.

## Contract snapshot

Agent 02 → Agent 04:
- health SUCCESS or DEGRADED;
- valid `generated_at` ≤20 minutes old;
- usable timeframe has non-null `ema20`, `ema50`, `rsi`, `adx`, `trend`.

Agent 03 → Agent 04:
- health SUCCESS or DEGRADED;
- valid `generated_at` ≤6 hours old;
- `gold_bias` + `news_risk`;
- RSS risk LOW/MEDIUM/HIGH only.

Agent 04 → Agent 05:
- valid normalized decision state ≤15 minutes old;
- failed/stale/invalid means BLOCK_TRADING downstream;
- degraded means CAUTION downstream;
- alignment/conflict metadata is intelligence only and does not increase authority.

Agent 05 → Agent 06:
- valid normalized permission state ≤15 minutes old;
- known permissions only: ALLOW_BUYS, ALLOW_SELLS, ALLOW_BOTH, CAUTION, BLOCK_TRADING;
- invalid/stale/unknown fails to BLOCK_TRADING;
- degraded authority cannot pass through as ALLOW_*.

Agent 06 → Trader View → historical evidence:
- Agent 06 remains the permission authority and is informational/read-only;
- Trader View must explicitly identify `mode: READ_ONLY`, `symbol: XAUUSD`, and `execution_enabled: false` before becoming a prediction snapshot;
- Trader View v0.2 presents Agent04 alignment/conflict intelligence without modifying permission;
- historical observation rejects unknown decisions/permissions/risks/conflict states, invalid confidence/freshness, execution authority, stale ALLOW states, and decision/permission mismatches;
- prediction snapshots persist validated `timeframe_alignment`, `timeframe_trends`, and higher/lower/cross-group conflict fields while preserving schema v1 compatibility; legacy Trader View input[...]
- blocked/NO_TRADE snapshots remain valid evidence when safely blocked;
- observation collector accepts only normalized TraderView envelopes with SUCCESS/DEGRADED health, delegates data safety checks to the existing observation contract, and only appends evidence; FA[...]

Reference-price evidence → outcome collector → analytics:
- must explicitly identify `symbol: XAUUSD`, `market: SPOT`, `quote_currency: USD`;
- provider identity is mandatory and `requires_credentials` must be exactly false;
- price must be finite and positive and `observed_at` must be timezone-aware ISO-8601;
- futures, ETFs, proxies, malformed evidence and credential-requiring sources fail closed before outcome use;
- Gold API adapter accepts only XAU payloads, requires provider `updatedAt`, and delegates validation to the provider-neutral contract;
- adapter is transport-free: no network, scheduling, broker or execution path;
- outcome collector consumes already-fetched validated reference evidence, uses the provider timestamp as `measured_at`, and delegates source-observation, supported horizons and idempotency to existing validation logic.

## Phase 2 historical evidence — ACTIVE

PR #6 introduced immutable prediction snapshots, deterministic observation IDs, append-only JSONL storage, separate outcomes and explicit `15m`, `1h`, `4h` horizons.

PR #7 hardened outcome integrity with one outcome per `(observation_id, horizon)`, orphan rejection, timezone-aware timestamp/schema validation, finite positive-price validation and fail-closed c[...]

PR #8 requires historical predictions to originate from a valid read-only XAUUSD Trader View and rejects unsafe execution-bearing or contradictory inputs.

PR #9 joins every appended outcome to exactly one source observation and enforces `measured_at >= observed_at + horizon`. Source history is mandatory, duplicate source IDs fail closed, malformed [...]

PR #10 adds explicit Agent04 multi-timeframe alignment/conflict intelligence while preserving deterministic weighted fusion and downstream safety authority.

PR #11 carries that intelligence into Trader View while retaining the Agent06 permission boundary and `execution_enabled: false` invariant.

PR #12 carries explicit MTF intelligence into immutable historical prediction snapshots, validates malformed metadata fail-closed, and preserves compatibility with existing schema-v1 history. Int[...]

PR #13 integrates an explicit evidence-only collector from normalized `trader_view.json` envelopes into append-only observations. It does not schedule itself, invoke upstream agents, write permis[...]

PR #15 adds a provider-neutral fail-closed reference-price evidence contract. It requires explicit credential-free spot XAUUSD/USD evidence and rejects futures/ETF/proxy substitutions. Integrated[...]

PR #16 validates gold-api.com as the first reference-evidence candidate through a transport-free normalization adapter. It maps already-fetched XAU payloads to the integrated reference contract, [...]

PR #17 integrates a transport-free outcome collector for already-fetched validated reference evidence. It uses the provider timestamp as `measured_at`, then delegates source-observation, supporte[...]

PR #18 hardens existing persisted outcome history before idempotency admission. Every prior record is semantically rebuilt and validated, must link to a valid source observation, must satisfy its[...]

PR #19 now integrates the read-only evidence coverage report. It validates persisted observations and outcomes before counting them, exposes per-horizon coverage plus complete/incomplete observat[...]

PR #20 is integrated: it extends evidence coverage with deterministic per-horizon missing counts and EMPTY/PARTIAL/COMPLETE status while remaining read-only and fail-closed.

This layer still does **not** run continuous collection, calculate directional/performance statistics, or create trading authority.

## Remaining risks / technical debt

1. Agent 03 lacks a validated scheduled-event calendar, so EXTREME event windows remain intentionally unavailable.
2. Freshness thresholds need later empirical validation against workflow cadence/session behavior.
3. Agent 01 remains monolithic and credential-dependent but isolated.
4. Operational orchestration must not accidentally become autonomous execution.
5. Historical JSONL duplicate checks still scan existing records; adequate initially, but indexing should be hardened before large datasets.
6. Gold API has passed the transport-free evidence adapter contract, but live network collection is not yet integrated or operationally validated.
7. Outcome timing enforces a minimum horizon but does not impose a maximum lateness/tolerance window; choose that only with collection-cadence evidence.
8. Observation/outcome collection cadence is not yet scheduled; cadence should be chosen only after evidence-volume/freshness implications and reference-price sourcing are reviewed.
9. Coverage analytics currently reports evidence completeness only; directional/performance statistics require an explicit source/reference-price-at-observation contract before they can be trustw[...]

## Active Phase 2 loop

1. Define evidence-supported outcome lateness tolerance only once collection cadence is known.
2. Add directional/performance analytics only after a trustworthy observation-time reference-price contract exists; analytics failures must never increase authority.
3. Harden historical indexing only when evidence volume justifies it.


## Recent change: cTrader provider (feature/ctrader-provider)

- Problem: When the repository was configured to use cTrader, the previous provider model required a token endpoint URL (CTRADER_TOKEN_URL) or CTRADER_CANDLES_URL. Some deployments instead supply a pre-provisioned access token and API base only. In addition, the provider import failures were being silently swallowed by the factory which caused a confusing fallback to the TwelveDataProvider.

- Fix implemented on branch `feature/ctrader-provider` (PR #3):
  - Agent02 now uses `get_default_provider()` so the runtime provider selection is configurable via environment variables.
  - The cTrader provider was updated to prefer a pre-provisioned access token (`CTRADER_ACCESS_TOKEN`) and to construct a sensible default candles endpoint from `CTRADER_API_BASE` (defaults to `https://api.ctrader.com`). This removes the hard dependency on `CTRADER_TOKEN_URL` and an explicit `CTRADER_CANDLES_URL` in common deployments.
  - `market/provider.py` import handling was hardened to surface import/configuration errors when cTrader is explicitly requested or when credentials/tokens are present, avoiding silent fallback to the TwelveDataProvider.
  - Tests updated: `tests/test_ctrader_provider.py` added/updated to cover instantiation modes and configuration errors.
  - CI workflow `.github/workflows/ctrader-integration.yml` was added/updated as a manual gated smoke test that uses `CTRADER_ACCESS_TOKEN`.

- Files changed: `agent02.py`, `market/ctrader_provider.py`, `market/provider.py`, `tests/test_ctrader_provider.py`, `.github/workflows/ctrader-integration.yml`, `PROJECT_LOG.md`.

- Required secrets for manual smoke: `CTRADER_CLIENT_ID`, `CTRADER_CLIENT_SECRET`, `CTRADER_ACCESS_TOKEN`, (optional) `CTRADER_API_BASE`.

- Remaining work: run the manual cTrader demo smoke test (manual Actions run) with the required secrets, capture a real XAUUSD candles payload, and, if necessary, add a tiny normalization patch and a recorded unit test to lock the shape.
