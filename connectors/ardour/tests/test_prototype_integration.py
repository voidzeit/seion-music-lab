"""Prototype -> Ardour CLI adaptation without requiring Ardour in CI."""
from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest
from seion_ardour import cli

from app.music.prototype_lab import build_experiments


def _wav(path: Path) -> None:
    samples = [int(3000 * math.sin(2 * math.pi * 220 * i / 8000)) for i in range(800)]
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(8000)
        f.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def test_v002_prototype_is_read_and_split_preserves_kick(tmp_path, monkeypatch):
    bundle = tmp_path / "projects" / "song" / "versions" / "v002" / "generated"
    manifest = build_experiments(bundle)
    monkeypatch.setattr(cli, "seed_manifest", lambda seed: {
        "split": {"kick": {"from": "drums", "notes": [35, 36]}},
        "merge": {"latin_perc": "drums"},
    })
    monkeypatch.setattr(cli, "workspace", lambda: tmp_path / "sessions")
    monkeypatch.setattr(cli, "prepare_session", lambda target, seed: target)
    monkeypatch.setattr(cli.ArdourInstall, "locate", lambda: SimpleNamespace(home=tmp_path))
    seen = {}

    def fake_render(_install, _session, job):
        text = job.read_text(encoding="utf-8")
        seen["job"] = text
        _wav(job.parent / "master.wav")
        return "test-render"

    monkeypatch.setattr(cli, "run_render", fake_render)
    assert cli.main([str(bundle), "--prototype", "groove", "--name", "audition", "--no-stems"]) == 0
    assert "bpm = 158.0000" in seen["job"]
    assert '["kick"] = {' in seen["job"]
    report_path = bundle.parent / "renders" / "audition" / "render_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["passed"]
    assert report["seed"] == "seion_seed_v2"
    assert report["bpm"] == manifest["bpm"]

    with pytest.raises(SystemExit, match="refusing to overwrite"):
        cli.main([str(bundle), "--prototype", "groove", "--name", "audition", "--no-stems"])


def test_rejects_unsafe_output_name(tmp_path):
    with pytest.raises(SystemExit):
        cli.main([str(tmp_path), "--prototype", "groove", "--name", "../escape"])
