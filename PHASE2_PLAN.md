# Rahul AI Team — Phase 2

Status: ACTIVE DEVELOPMENT

## Objective
Build evidence and trader-access infrastructure around the stable deterministic V1 without weakening Agent 05 or enabling autonomous execution.

## Phase 2 pipeline

Agent 02 + Agent 03 -> Agent 04 -> Agent 05 -> Agent 06
                                      |
                                      v
                           Historical Observation
                                      |
                           Outcome Measurement
                                      |
                         Performance Analytics
                                      |
                         Trader Data / Alert View

## Safety invariants
- Agent 05 remains the deterministic permission authority.
- Agent 06 remains read-only and execution_enabled=false.
- Historical/analytics failures never increase trading authority.
- No broker order placement or autonomous execution is introduced.
- Original prediction snapshots are immutable; outcomes are appended separately.
- ML is advisory only until separately validated.

## Current engineering gates
1. Correct PROJECT_LOG.md post-merge documentation drift.
2. Build and test append-only historical observation records.
3. Validate durable cross-run retention.
4. Select and validate an authoritative XAUUSD reference-price source before automated outcome scoring.
5. Record outcomes at +15m, +1h and +4h without rewriting predictions.
6. Build trader-readable Agent 06 status/alert output.
7. Harden Agent 04 with explicit multi-timeframe conflict/alignment scoring and deterministic tests.
8. Run complete Agent02+03 -> Agent04 -> Agent05 -> Agent06 regression tests.
9. Add performance analytics only after sufficient real observations exist.

## Trader-facing target
The interface should expose decision, permission, confidence, technical bias, macro bias, H4/H1/M15/M5 alignment, conflict level, news risk, reasons, freshness, generated time, and eventually evidence-backed historical performance for comparable observations.

## Not yet operational
Do not claim continuous historical collection or outcome statistics until repository CI plus real workflow/artifact evidence proves them.
