"""CLI-level end-to-end review of generated MIDI -> WAV -> analysis -> review."""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from app.cli.seion_music import app


def test_project_001_cli_full_local_pipeline(tmp_path):
    pytest.importorskip("numpy")
    runner = CliRunner()
    bundle, audio = tmp_path / "midi", tmp_path / "audio"

    result = runner.invoke(app, ["prototype", "--out", str(bundle)])
    assert result.exit_code == 0, result.output
    assert (bundle / "prototype_manifest.json").is_file()

    result = runner.invoke(app, ["preview", "--bundle", str(bundle), "--out", str(audio)])
    assert result.exit_code == 0, result.output
    assert (audio / "groove" / "preview.wav").is_file()
    assert (audio / "trance_bounce" / "preview.wav").is_file()
    assert (audio / "hardcore_hybrid" / "preview.wav").is_file()

    comparison = audio / "technical_comparison.json"
    result = runner.invoke(app, ["compare-audio", str(audio), "--out", str(comparison)])
    assert result.exit_code == 0, result.output
    assert json.loads(comparison.read_text())["creative_gate"] == "human_listening_required"

    result = runner.invoke(app, ["review", "init", str(audio)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app, ["review", "approve", str(audio), "groove", "--heard-all",
              "--reason", "Only unit tests were run; no actual audition"],
    )
    assert result.exit_code != 0  # unit tests cannot invent human ratings
    assert json.loads((audio / "listening_review.json").read_text())["approval"] is None

    result = runner.invoke(app, ["review", "status", str(audio)])
    assert result.exit_code == 0, result.output
    assert "unreviewed" in result.output


def test_cli_has_new_commands():
    runner = CliRunner()
    for name in ("prototype", "preview", "analyze-wav", "compare-audio", "review"):
        result = runner.invoke(app, [name, "--help"])
        assert result.exit_code == 0, (name, result.output)
