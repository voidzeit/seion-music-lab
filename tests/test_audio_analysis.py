"""Signal measurements are technical evidence, not creative review."""
from __future__ import annotations

import math
import struct
import wave

import pytest

from app.audio.audio_analysis import analyze_wav


def _tone(path, *, amplitude: float, dc: float = 0.0):
    samples = [
        round(max(-1, min(1, amplitude * math.sin(2 * math.pi * 100 * i / 16000) + dc)) * 32767)
        for i in range(16000)
    ]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def test_measure_wav_tone_has_correct_frequency_band(tmp_path):
    pytest.importorskip("numpy")
    path = tmp_path / "tone.wav"
    _tone(path, amplitude=0.5)
    data = analyze_wav(path, bpm=120)
    assert data["duration_seconds"] == 1
    assert data["rms_dbfs"] == pytest.approx(-9.03, abs=0.5)
    assert data["spectral_energy_ratios"]["sub_20_120_hz"] > 0.6
    assert data["spectral_centroid_hz"] == pytest.approx(100, abs=20)
    assert not data["technical_flags"]["clipped_samples"]
    assert len(data["four_bar_rms_dbfs"]) == 1
    assert "NOT integrated LUFS" in data["measurement_limitations"][0]


def test_dc_and_silence_detected(tmp_path):
    pytest.importorskip("numpy")
    silent = tmp_path / "zero.wav"
    _tone(silent, amplitude=0)
    result = analyze_wav(silent)
    assert result["technical_flags"]["potential_silence"]
    assert result["rms_dbfs"] is None
    dc = tmp_path / "dc.wav"
    _tone(dc, amplitude=0.1, dc=0.1)
    assert analyze_wav(dc)["technical_flags"]["unusual_dc_offset"]


def test_invalid_bpm_rejected(tmp_path):
    with pytest.raises(ValueError, match="bpm"):
        analyze_wav(tmp_path / "no.wav", bpm=0)
