"""Executable tests for the original synthetic MIDI-to-WAV audition renderer."""
from __future__ import annotations

import json
import wave

import pytest

from app.music.prototype_lab import build_experiments


def test_preview_optional_numpy_and_deterministic_output(tmp_path):
    pytest.importorskip("numpy")
    from app.audio.preview_synth import render_mode

    bundle = tmp_path / "bundle"
    build_experiments(bundle)
    first = render_mode(bundle, tmp_path / "audition_a", "groove", sample_rate=16000)
    second = render_mode(bundle, tmp_path / "audition_b", "groove", sample_rate=16000)
    assert first["files"]["master"]["sha256"] == second["files"]["master"]["sha256"]
    assert first["quality_status"] == "synthetic_preview_unreviewed"
    assert first["files"]["master"]["non_silent"]
    with wave.open(str(tmp_path / "audition_a" / "preview.wav")) as wav:
        assert wav.getframerate() == 16000
        assert wav.getnchannels() == 1
        assert wav.getnframes() > 16000 * 24
    assert set(first["note_counts"]) == {
        "kick", "drums", "percussion", "bass", "chords", "arp", "lead"
    }
    assert len(list((tmp_path / "audition_a" / "stems").glob("*.wav"))) == 7
    with pytest.raises(FileExistsError):
        render_mode(bundle, tmp_path / "audition_a", "groove", sample_rate=16000)


def test_modes_generate_distinct_audio_and_nonempty_stems(tmp_path):
    pytest.importorskip("numpy")
    from app.audio.preview_synth import render_mode

    bundle = tmp_path / "bundle"
    build_experiments(bundle)
    hashes = set()
    for mode in ("groove", "trance_bounce", "hardcore_hybrid"):
        report = render_mode(bundle, tmp_path / mode, mode, sample_rate=16000)
        hashes.add(report["files"]["master"]["sha256"])
        assert all(x["non_silent"] for x in report["files"].values())
        assert all(x["peak_dbfs"] <= 0 for x in report["files"].values())
        assert json.loads((tmp_path / mode / "preview_report.json").read_text())["gate"] == "requires_human_listening"
    assert len(hashes) == 3


def test_manifest_path_traversal_rejected(tmp_path):
    pytest.importorskip("numpy")
    from app.audio.preview_synth import render_mode

    bundle = tmp_path / "bundle"
    meta = build_experiments(bundle)
    meta["experiments"]["groove"]["midi_files"]["kick"] = "../../etc/passwd"
    (bundle / "prototype_manifest.json").write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="unsafe"):
        render_mode(bundle, tmp_path / "result", "groove", sample_rate=16000)
    assert not (tmp_path / "result").exists()
