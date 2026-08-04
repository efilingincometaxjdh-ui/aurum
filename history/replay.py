"""RAHUL AI TEAM — REPLAY ENGINE (ADVISORY ONLY)

Deterministic, offline-only replay of append-only UTC candle JSONL data.

- Reuses existing historical JSONL conventions (one record per line, UTC ISO-8601).
- Emits candles in strict chronological order.
- Supports step, play, pause and resume operations.
- Remains advisory-only: emitted events are tagged with `mode: REPLAY` and
  `execution_enabled: false` and must not be wired to any execution authority.

This module does not depend on live services, IMarketDataProvider, Agent05 or
Agent06. Higher layers may use the replayed events to drive intelligence
pipelines for analysis, backtesting or inspection while preserving the
fail-closed architecture.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from history.observations import _parse_timestamp, _read_jsonl


def _normalize_candle(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a single historical candle record.

    Required fields:
    - datetime: ISO-8601 string with timezone information (UTC enforced
      upstream by _parse_timestamp).
    - open, high, low, close: numeric values.

    Extra fields are preserved but do not affect replay ordering.
    """

    if not isinstance(record, dict):
        raise ValueError("candle record must be a dictionary")

    for key in ("datetime", "open", "high", "low", "close"):
        if key not in record:
            raise ValueError(f"candle record missing required field: {key}")

    dt = _parse_timestamp(record["datetime"], "datetime")

    normalized: Dict[str, Any] = {
        "datetime": dt,
        "open": float(record["open"]),
        "high": float(record["high"]),
        "low": float(record["low"]),
        "close": float(record["close"]),
    }

    for key, value in record.items():
        if key not in normalized:
            normalized[key] = value

    return normalized


def load_candles(path: str) -> List[Dict[str, Any]]:
    """Load append-only UTC candles from JSONL in deterministic chronological order.

    - Uses the shared _read_jsonl helper from history.observations.
    - Validates and normalizes each record via _normalize_candle.
    - Sorts by parsed datetime to guarantee deterministic ordering.
    """

    raw = _read_jsonl(path)
    candles = [_normalize_candle(record) for record in raw]
    candles.sort(key=lambda c: c["datetime"])
    return candles


@dataclass
class ReplayState:
    index: int = 0
    playing: bool = False


class ReplayEngine:
    """Deterministic, offline replay of historical candles.

    ReplayEngine is a minimal state machine over a fixed list of normalized
    candle records. It exposes:

    - step(): emit exactly one event if available.
    - play(max_steps=None): emit until end-of-stream or max_steps.
    - pause(): stop emitting; idempotent.
    - resume(max_steps=None): alias for play() from the current index.

    Emitted events include advisory-only metadata:
    - mode: "REPLAY"
    - execution_enabled: False

    This engine never calls live services, never touches Agent05 or Agent06,
    and must not be wired to any autonomous execution path.
    """

    def __init__(self, candles: List[Dict[str, Any]], on_event: Callable[[Dict[str, Any]], None]) -> None:
        self._candles = candles
        self._on_event = on_event
        self._state = ReplayState()

    @property
    def index(self) -> int:
        """Current replay index (0-based)."""

        return self._state.index

    @property
    def done(self) -> bool:
        """True when all candles have been replayed."""

        return self._state.index >= len(self._candles)

    def step(self) -> bool:
        """Replay exactly one candle, if available.

        Returns True if an event was emitted, False at end-of-stream.
        """

        if self.done:
            return False

        candle = self._candles[self._state.index]
        self._state.index += 1
        event = {
            **candle,
            "mode": "REPLAY",
            "execution_enabled": False,
        }
        self._on_event(event)
        return True

    def play(self, max_steps: Optional[int] = None) -> None:
        """Replay until end-of-stream or max_steps.

        Safe to call repeatedly; respects pause() and completes deterministically.
        """

        if self.done:
            return

        self._state.playing = True
        steps = 0
        while self._state.playing and not self.done:
            if max_steps is not None and steps >= max_steps:
                break
            if not self.step():
                break
            steps += 1

    def pause(self) -> None:
        """Pause replay; idempotent."""

        self._state.playing = False

    def resume(self, max_steps: Optional[int] = None) -> None:
        """Resume replay from the current index.

        This is an alias for play() from the current state.
        """

        self.play(max_steps=max_steps)
