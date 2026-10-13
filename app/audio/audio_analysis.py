"""Evidence-based PCM WAV measurements. No genre, artistic or mastering claims.

Requires pip install -e ".[preview]" (NumPy). Measurements are observed
signal properties, not perceptual scores or exact LUFS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import wave
from pathlib import Path


def _np():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError('WAV analysis requires pip install -e ".[preview]"') from exc
    return np


def _read_wav(path: Path):
    np = _np()
    with wave.open(str(path), "rb") as reader:
        sr = reader.getframerate()
        ch = reader.getnchannels()
        sw = reader.getsampwidth()
        frames = reader.getnframes()
        if not sr or not ch or not frames:
            raise ValueError("empty or invalid WAV")
        raw = reader.readframes(frames)
    if sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        sample = b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (
            b[:, 2].astype(np.int32) << 16
        )
        sample = (sample ^ 0x800000) - 0x800000
        data = sample.astype(np.float64) / 8388608.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"unsupported PCM bit depth: {sw * 8}")
    if data.size != frames * ch:
        raise ValueError("truncated audio file")
    return data.reshape(frames, ch), sr, sw * 8


def _db(value: float) -> float | None:
    return round(20 * math.log10(value), 2) if value > 0 else None


def analyze_wav(path: Path, *, bpm: float | None = None) -> dict:
    """Compute grounded signal statistics; never infer artistic worth."""
    np = _np()
    if bpm is not None and not (20 <= bpm <= 400):
        raise ValueError("bpm must be within 20..400 for beat-aligned measurements")
    arr, sample_rate, bits = _read_wav(path)
    channels = arr.shape[1]
    mono = np.mean(arr, axis=1)
    abs_peak = float(np.max(np.abs(arr)))
    rms = float(np.sqrt(np.mean(arr**2)))
    dc = float(np.mean(mono))
    clipping_samples = int(np.count_nonzero(np.abs(arr) >= 32760 / 32768))
    length = len(mono)
    duration = length / sample_rate

    # Use fixed 50 ms RMS frames for silence / transient estimate.
    hop = max(1, round(sample_rate * 0.05))
    count = len(mono) // hop
    frames = mono[:count * hop].reshape(count, hop) if count else np.zeros((0, hop))
    rms_frames = np.sqrt(np.mean(frames**2, axis=1)) if count else np.empty(0)
    silence_ratio = float(np.mean(rms_frames < 0.001)) if count else 0.0
    flux = np.maximum(0.0, np.diff(rms_frames)) if count > 1 else np.empty(0)
    if flux.size:
        med = float(np.median(flux))
        mad = float(np.median(np.abs(flux - med)))
        threshold = max(med + 3 * mad, 0.0075)
        candidates = np.where(flux > threshold)[0]
        previous = -999
        detected = 0
        for idx in candidates:
            if idx - previous >= 2:
                detected += 1
                previous = idx
        transient_density = detected / duration
    else:
        transient_density = 0.0

    # Welch-like energy accumulator: Hanning-windowed rFFT, hop = half window.
    window_size = 2048
    fft_energy = np.zeros(window_size // 2 + 1, dtype=np.float64)
    window = np.hanning(window_size)
    for start in range(0, max(0, length - window_size + 1), window_size // 2):
        spectrum = np.fft.rfft(mono[start:start + window_size] * window)
        fft_energy += np.abs(spectrum) ** 2
    freqs = np.fft.rfftfreq(window_size, 1 / sample_rate)
    total_energy = float(np.sum(fft_energy))
    bands = {"sub_20_120_hz": (20, 120), "bass_120_500_hz": (120, 500),
             "mid_500_4000_hz": (500, 4000), "high_4000_plus_hz": (4000, sample_rate / 2)}
    band_ratios = {}
    for name, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs < hi)
        band_ratios[name] = round(float(fft_energy[mask].sum()) / total_energy, 4) if total_energy else 0.0
    centroid = float(np.sum(freqs * fft_energy) / total_energy) if total_energy else 0.0

    result = {
        "schema_version": "1.0",
        "analysis_kind": "measured_pcm_signal_features",
        "measurement_limitations": [
            "RMS is NOT integrated LUFS",
            "Onset density is an estimate, not a drum transcription",
            "Spectral ratios are not genre recognition or perceptual mix quality",
            "No listening, reference comparison or master approval was performed",
        ],
        "source_file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sample_rate": sample_rate,
        "channels": channels,
        "bit_depth": bits,
        "duration_seconds": round(duration, 3),
        "peak_dbfs": _db(abs_peak),
        "rms_dbfs": _db(rms),
        "crest_factor_db": round(20 * math.log10(abs_peak / rms), 2) if rms > 0 else None,
        "dc_offset": round(dc, 7),
        "clipped_sample_count": clipping_samples,
        "silent_frame_ratio": round(silence_ratio, 4),
        "estimated_transients_per_second": round(transient_density, 3),
        "spectral_centroid_hz": round(centroid, 1),
        "spectral_energy_ratios": band_ratios,
        "bpm_assumed": bpm,
        "technical_flags": {
            "potential_silence": rms < 0.001,
            "clipped_samples": clipping_samples > 0,
            "unusual_dc_offset": abs(dc) > 0.015,
        },
    }
    if bpm is not None:
        beat_sec = 60 / bpm
        # Non-overlapping four-bar mean RMS to track macro energy.
        cells = max(1, math.ceil(duration / (beat_sec * 16)))
        result["four_bar_rms_dbfs"] = [
            _db(float(np.sqrt(np.mean(mono[int(i * beat_sec * 16 * sample_rate):
                                           min(length, int((i + 1) * beat_sec * 16 * sample_rate))] ** 2))))
            for i in range(cells)
        ]
    return result


def analyze_prototypes(root: Path, out: Path | None = None) -> dict:
    """Compare acoustic properties of A/B/C without inventing a musical winner."""
    results = {}
    from app.audio.preview_synth import MODES

    for mode in MODES:
        report_path = root / mode / "preview_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("mode") != mode:
            raise ValueError(f"wrong mode provenance: {mode}")
        path = root / mode / "preview.wav"
        stats = analyze_wav(path, bpm=report["bpm"])
        if stats["sha256"] != report["files"]["master"]["sha256"]:
            raise ValueError(f"modified audio after render: {mode}")
        results[mode] = stats
    data = {
        "schema_version": "1.0",
        "comparison_type": "technical_only_no_automatic_approval",
        "results": results,
        "creative_gate": "human_listening_required",
    }
    if out is not None:
        if out.exists():
            raise FileExistsError(f"refusing to overwrite analysis: {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--wav", type=Path)
    group.add_argument("--preview-root", type=Path)
    parser.add_argument("--bpm", type=float)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"refusing to overwrite: {args.out}")
    if args.wav:
        data = analyze_wav(args.wav, bpm=args.bpm)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        data = analyze_prototypes(args.preview_root, out=args.out)
    print(f"Measured audio signal properties in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
