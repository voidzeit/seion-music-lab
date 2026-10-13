"""Real-file human-audition acceptance tests; no listener is simulated as real."""
from __future__ import annotations

import json
import wave
from pathlib import Path

import pytest

from app.audio.listening_gate import approve, init_review, load_review, rate


def make_preview(root: Path, mode: str) -> None:
    from app.audio.listening_gate import _sha

    folder = root / mode
    folder.mkdir(parents=True)
    with wave.open(str(folder / "preview.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"\1\0" * 200)
    (folder / "preview_report.json").write_text(json.dumps({
        "mode": mode,
        "quality_status": "synthetic_preview_unreviewed",
        "files": {"master": {"sha256": _sha(folder / "preview.wav")}},
    }))


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "previews"
    for mode in ("groove", "trance_bounce", "hardcore_hybrid"):
        make_preview(root, mode)
    return root


def test_init_preserves_reviews_and_audio_hashes(tmp_path):
    root = _root(tmp_path)
    state = init_review(root)
    assert state["decision"] == "unreviewed"
    with pytest.raises(FileExistsError):
        init_review(root)
    (root / "groove" / "preview.wav").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="changed"):
        rate(root, "groove", dict(groove=4, low_end=3, hook=4, timbre=5), "Auditioned once")


def test_explicit_review_requires_all_variants_and_is_immutable(tmp_path):
    root = _root(tmp_path)
    init_review(root)
    scores = dict(groove=4, low_end=3, hook=4, timbre=5)
    with pytest.raises(ValueError, match="notes"):
        rate(root, "groove", scores, "")
    with pytest.raises(ValueError, match="scores"):
        rate(root, "groove", {**scores, "hook": 6}, "Too high")
    rate(root, "groove", scores, "Kick is punchy, but the midrange is crowded")
    with pytest.raises(ValueError, match="all three"):
        approve(root, "groove", "More physical drive in a DJ set", heard_all=True)
    for mode in ("trance_bounce", "hardcore_hybrid"):
        rate(root, mode, scores, f"Heard and compared {mode}")
    with pytest.raises(ValueError, match="explicitly"):
        approve(root, "groove", "This has excellent pacing", heard_all=False)
    approved = approve(root, "groove", "Better physical groove and low-end space", heard_all=True)
    assert approved["decision"] == "approved_for_32bar_development_only"
    assert load_review(root)["approval"]["mode"] == "groove"
    with pytest.raises(ValueError, match="immutable"):
        rate(root, "groove", scores, "Never mutate after selection")
