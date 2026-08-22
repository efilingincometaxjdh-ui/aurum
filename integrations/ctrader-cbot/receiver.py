"""Local read-only receiver for the Aurum cTrader cBot bridge.

This development receiver accepts authenticated market bars from the cBot and
persists them as local evidence. It does not run Agent02 and it never places
orders. The production application should eventually expose the same contract
through its existing backend rather than deploying this development server.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "current"
LATEST_PATH = DATA_DIR / "ctrader_cbot_latest.json"
JSONL_PATH = DATA_DIR / "ctrader_cbot_candles.jsonl"
HOST = os.getenv("AURUM_CBOT_HOST", "127.0.0.1")
PORT = int(os.getenv("AURUM_CBOT_PORT", "8000"))
EXPECTED_TOKEN = os.getenv("AURUM_CBOT_INGEST_TOKEN", "")


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_bar(payload: dict[str, Any]) -> dict[str, Any]:
    required = (
        "schemaVersion",
        "provider",
        "symbol",
        "timeframe",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "tickVolume",
        "digits",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")

    if payload["schemaVersion"] != 1:
        raise ValueError("unsupported schemaVersion")
    if payload["provider"] != "ctrader_cbot":
        raise ValueError("invalid provider")
    if not isinstance(payload["symbol"], str) or not payload["symbol"]:
        raise ValueError("invalid symbol")
    if not isinstance(payload["timeframe"], str) or not payload["timeframe"]:
        raise ValueError("invalid timeframe")

    try:
        timestamp = datetime.fromisoformat(str(payload["timestamp"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must include timezone")

    prices = {key: payload[key] for key in ("open", "high", "low", "close")}
    if not all(_finite_number(value) for value in prices.values()):
        raise ValueError("OHLC must contain finite numbers")
    if prices["low"] <= 0:
        raise ValueError("low must be positive")
    if prices["high"] < max(prices["open"], prices["close"], prices["low"]):
        raise ValueError("high is below another OHLC value")
    if prices["low"] > min(prices["open"], prices["close"]):
        raise ValueError("low is above another OHLC value")
    if not isinstance(payload["digits"], int) or not 0 <= payload["digits"] <= 10:
        raise ValueError("invalid digits")
    if not isinstance(payload["tickVolume"], int) or payload["tickVolume"] < 0:
        raise ValueError("invalid tickVolume")

    normalized = dict(payload)
    normalized["timestamp"] = timestamp.astimezone(timezone.utc).isoformat()
    return normalized


class Handler(BaseHTTPRequestHandler):
    server_version = "AurumCTraderBotReceiver/1.0"

    def _json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/market-data/ctrader-cbot":
            self._json(404, {"error": "not_found"})
            return

        if EXPECTED_TOKEN and self.headers.get("X-Aurum-Ingest-Token") != EXPECTED_TOKEN:
            self._json(401, {"error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 64 * 1024:
                raise ValueError("invalid content length")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("payload must be an object")
            normalized = validate_bar(payload)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json(400, {"error": "invalid_payload", "detail": str(exc)})
            return

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        key = f"{normalized['symbol']}::{normalized['timeframe']}"

        latest: dict[str, Any] = {}
        if LATEST_PATH.exists():
            try:
                latest = json.loads(LATEST_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                latest = {}
        latest[key] = normalized
        LATEST_PATH.write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")
        with JSONL_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalized, separators=(",", ":")) + "\n")

        self._json(200, {"accepted": True, "key": key, "timestamp": normalized["timestamp"]})

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/api/market-data/ctrader-cbot/health":
            self._json(404, {"error": "not_found"})
            return
        self._json(200, {"status": "OK", "provider": "ctrader_cbot", "read_only": True})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[cBot receiver] {format % args}")


def main() -> None:
    print(f"Aurum cTrader cBot receiver listening on http://{HOST}:{PORT}")
    print("POST /api/market-data/ctrader-cbot")
    print("GET  /api/market-data/ctrader-cbot/health")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
