"""Measure a ReferenceFingerprint from separated stems (drums/bass/other/vocals).

Everything here is *measured* from audio with an explicit confidence; nothing
is copied from web sources. Pitch-level transcriptions of the reference
(vocal / bass notes) are written next to the private stems, never into the
project folder, because they are derived from protected material.

usage: python -m app.audio.reference_fingerprint <stems_dir> <out_json> [--private-dir DIR]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import librosa
import numpy as np

SR = 22050
HOP = 512
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def _load(stems: Path, name: str) -> np.ndarray:
    y, _ = librosa.load(str(stems / f"{name}.wav"), sr=SR, mono=True)
    return y


def _key_candidates(chroma: np.ndarray, top: int = 4) -> list[dict]:
    scores = []
    for i in range(12):
        scores.append((np.corrcoef(chroma, np.roll(KS_MAJOR, i))[0, 1], f"{NAMES[i]} major"))
        scores.append((np.corrcoef(chroma, np.roll(KS_MINOR, i))[0, 1], f"{NAMES[i]} minor"))
    scores.sort(reverse=True)
    return [{"key": k, "score": round(float(s), 3)} for s, k in scores[:top]]


def _chord_templates() -> tuple[list[str], np.ndarray]:
    labels, rows = [], []
    for root in range(12):
        for quality, intervals in (("", (0, 4, 7)), ("m", (0, 3, 7))):
            t = np.zeros(12)
            t[[(root + i) % 12 for i in intervals]] = 1
            labels.append(NAMES[root] + quality)
            rows.append(t / np.linalg.norm(t))
    return labels, np.array(rows)


def _beat_grid(drums: np.ndarray) -> tuple[float, np.ndarray, int]:
    onset = librosa.onset.onset_strength(y=drums, sr=SR, hop_length=HOP)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=SR, hop_length=HOP)
    # Downbeat phase: the beat phase (mod 4) with the most low-frequency energy.
    low = librosa.feature.rms(y=librosa.effects.preemphasis(drums, coef=-0.95), hop_length=HOP)[0]
    phase_energy = [float(low[beats[p::4]].sum()) for p in range(4)]
    return float(np.atleast_1d(tempo)[0]), beats, int(np.argmax(phase_energy))


def _pitch_track(y: np.ndarray, fmin: float, fmax: float) -> tuple[np.ndarray, np.ndarray]:
    f0, voiced, _ = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=SR, hop_length=HOP)
    midi = librosa.hz_to_midi(f0)
    return midi, voiced & np.isfinite(midi)


def _notes_from_track(midi: np.ndarray, voiced: np.ndarray, min_frames: int = 4) -> list[tuple[float, float, int]]:
    """Group stable voiced frames into (start_s, dur_s, midi) notes."""
    notes, start, cur = [], None, None
    rounded = np.where(voiced, np.round(midi), -1).astype(int)
    for i, m in enumerate(list(rounded) + [-1]):
        if m != cur:
            if cur is not None and cur >= 0 and i - start >= min_frames:
                t0 = librosa.frames_to_time(start, sr=SR, hop_length=HOP)
                t1 = librosa.frames_to_time(i, sr=SR, hop_length=HOP)
                notes.append((float(t0), float(t1 - t0), int(cur)))
            start, cur = i, m
    return notes


def fingerprint(stems: Path, private_dir: Path | None = None) -> dict:
    drums, bass, other, vocals = (_load(stems, n) for n in ("drums", "bass", "other", "vocals"))
    duration = len(drums) / SR

    tempo, beats, phase = _beat_grid(drums)
    downbeats = beats[phase::4]
    bar_times = librosa.frames_to_time(downbeats, sr=SR, hop_length=HOP)

    harmonic = librosa.effects.harmonic(bass + other)
    chroma = librosa.feature.chroma_cqt(y=harmonic, sr=SR, hop_length=HOP)
    labels, templates = _chord_templates()
    bars = []
    for i in range(len(downbeats) - 1):
        seg = chroma[:, downbeats[i]:downbeats[i + 1]].mean(axis=1)
        if seg.max() <= 0:
            continue
        sims = templates @ (seg / np.linalg.norm(seg))
        best = int(np.argmax(sims))
        bars.append({"bar": i + 1, "time_s": round(float(bar_times[i]), 2), "chord": labels[best],
                     "confidence": round(float(sims[best]), 3)})

    bass_midi, bass_voiced = _pitch_track(bass, 30, 300)
    bass_pc = Counter(int(m) % 12 for m in np.round(bass_midi[bass_voiced]))
    voc_midi, voc_voiced = _pitch_track(vocals, 80, 1000)
    voc_pc = Counter(int(m) % 12 for m in np.round(voc_midi[voc_voiced]))

    def rms_per_bar(y: np.ndarray) -> list[float]:
        r = librosa.feature.rms(y=y, hop_length=HOP)[0]
        return [float(20 * np.log10(r[downbeats[i]:downbeats[i + 1]].mean() + 1e-9))
                for i in range(len(downbeats) - 1)]

    stem_levels = {n: rms_per_bar(y) for n, y in (("drums", drums), ("bass", bass), ("other", other), ("vocals", vocals))}
    vocal_peak = max(stem_levels["vocals"])
    vocal_bars = [b + 1 for b, v in enumerate(stem_levels["vocals"]) if v > vocal_peak - 15]

    chord_seq = [b["chord"] for b in bars]
    loops = Counter(tuple(chord_seq[i:i + 4]) for i in range(len(chord_seq) - 3))

    def pc_hist(c: Counter) -> dict:
        total = sum(c.values()) or 1
        return {NAMES[k]: round(v / total, 3) for k, v in sorted(c.items(), key=lambda kv: -kv[1])}

    result = {
        "schema_version": "1.0",
        "analysis_type": "measured_from_audio",
        "method": "demucs htdemucs_ft stems + librosa (beat_track, chroma_cqt, pyin)",
        "duration_seconds": round(duration, 2),
        "tempo_bpm": round(tempo, 2),
        "beats_detected": int(len(beats)),
        "bars_detected": len(bars),
        "first_downbeat_s": round(float(bar_times[0]), 3) if len(bar_times) else None,
        "key_candidates_harmonic": _key_candidates(chroma.mean(axis=1)),
        "bass_pitch_class_histogram": pc_hist(bass_pc),
        "vocal_pitch_class_histogram": pc_hist(voc_pc),
        "chord_histogram": dict(Counter(chord_seq).most_common(8)),
        "top_4bar_loops": [{"chords": list(k), "count": v} for k, v in loops.most_common(5)],
        "vocal_active_bars": vocal_bars,
        "bars": bars,
        "stem_rms_db_per_bar": {k: [round(x, 1) for x in v] for k, v in stem_levels.items()},
    }

    if private_dir is not None:
        private_dir.mkdir(parents=True, exist_ok=True)
        for name, (m, v) in {"vocal": (voc_midi, voc_voiced), "bass": (bass_midi, bass_voiced)}.items():
            notes = _notes_from_track(m, v)
            (private_dir / f"{name}_notes.json").write_text(
                json.dumps([{"start_s": round(s, 3), "dur_s": round(d, 3), "midi": n} for s, d, n in notes]),
                encoding="utf-8",
            )
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stems", type=Path)
    ap.add_argument("out_json", type=Path)
    ap.add_argument("--private-dir", type=Path)
    args = ap.parse_args(argv)
    result = fingerprint(args.stems, args.private_dir)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
