import json
import os
import tempfile
import unittest

from history.replay import load_candles, ReplayEngine


def _write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


class ReplayEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "candles.jsonl")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_chronological_ordering(self):
        # Out-of-order by time, including a Z suffix and explicit +00:00
        records = [
            {"datetime": "2026-01-01T00:05:00+00:00", "open": 1, "high": 2, "low": 0, "close": 1.5},
            {"datetime": "2026-01-01T00:00:00Z", "open": 1, "high": 2, "low": 0, "close": 1.5},
            {"datetime": "2026-01-01T00:03:00+00:00", "open": 1, "high": 2, "low": 0, "close": 1.5},
        ]
        _write_jsonl(self.path, records)

        candles = load_candles(self.path)
        times = [c["datetime"] for c in candles]

        self.assertEqual(times, sorted(times), "Candles must be returned in chronological order")

    def test_end_of_stream_and_step(self):
        records = [
            {"datetime": "2026-01-01T00:00:00+00:00", "open": 1, "high": 2, "low": 0, "close": 1.5},
            {"datetime": "2026-01-01T00:01:00+00:00", "open": 1, "high": 2, "low": 0, "close": 1.5},
        ]
        _write_jsonl(self.path, records)
        candles = load_candles(self.path)

        events = []

        def on_event(event):
            events.append(event)

        engine = ReplayEngine(candles, on_event)

        self.assertTrue(engine.step())
        self.assertTrue(engine.step())
        self.assertFalse(engine.step(), "After last candle, step() must return False")
        self.assertTrue(engine.done)
        self.assertEqual(len(events), 2)
        for event in events:
            self.assertEqual(event["mode"], "REPLAY")
            self.assertIs(event["execution_enabled"], False)

    def test_deterministic_replay(self):
        records = [
            {"datetime": "2026-01-01T00:00:00+00:00", "open": 1, "high": 2, "low": 0, "close": 1.5},
            {"datetime": "2026-01-01T00:01:00+00:00", "open": 1.1, "high": 2.1, "low": 0.1, "close": 1.6},
        ]
        _write_jsonl(self.path, records)
        candles = load_candles(self.path)

        def run_once():
            events = []

            def on_event(event):
                events.append(event)

            engine = ReplayEngine(candles, on_event)
            engine.play()
            return events

        first = run_once()
        second = run_once()
        self.assertEqual(first, second, "Replay must be deterministic for the same input")

    def test_pause_and_resume(self):
        records = [
            {"datetime": "2026-01-01T00:00:00+00:00", "open": 1, "high": 2, "low": 0, "close": 1.5},
            {"datetime": "2026-01-01T00:01:00+00:00", "open": 1.1, "high": 2.1, "low": 0.1, "close": 1.6},
            {"datetime": "2026-01-01T00:02:00+00:00", "open": 1.2, "high": 2.2, "low": 0.2, "close": 1.7},
        ]
        _write_jsonl(self.path, records)
        candles = load_candles(self.path)

        events = []

        def on_event(event):
            events.append(event)

        engine = ReplayEngine(candles, on_event)

        # Play a single step, then pause
        engine.play(max_steps=1)
        engine.pause()
        self.assertEqual(engine.index, 1)
        self.assertEqual(len(events), 1)

        # Resume with enough steps to finish
        engine.resume(max_steps=10)
        self.assertTrue(engine.done)
        self.assertEqual(len(events), 3)


if __name__ == "__main__":
    unittest.main()
