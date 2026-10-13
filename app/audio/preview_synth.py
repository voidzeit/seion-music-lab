"""Reproducible ORIGINAL SYNTHETIC previews for Project 001's editable MIDI.

This is a lightweight sound-design audition, not a DAW replacement, reference
transcription, commercial release master or imitation of any named artist.

Requires optional extra: pip install -e ".[preview]"
Run: python -m app.audio.preview_synth --bundle <generated> --out <new-dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import wave
from pathlib import Path

import mido

SAMPLE_RATE = 24000
MODES = ("groove", "trance_bounce", "hardcore_hybrid")
ROLE_ORDER = ("kick", "drums", "percussion", "bass", "chords", "arp", "lead")
SOUND_PROFILES = {
    "groove": {
        "kick_end_hz": 53.0, "kick_pitch_ms": 47.0, "kick_drive": 1.5,
        "bass_character": "round", "bass_drive": 1.25,
        "chord_character": "stabs", "lead_character": "restrained",
        "levels": (0.88, 0.38, 0.45, 0.72, 0.22, 0.18, 0.22),
    },
    "trance_bounce": {
        "kick_end_hz": 57.0, "kick_pitch_ms": 33.0, "kick_drive": 1.7,
        "bass_character": "fm_donk", "bass_drive": 1.6,
        "chord_character": "wide", "lead_character": "bright",
        "levels": (0.89, 0.43, 0.22, 0.64, 0.23, 0.23, 0.26),
    },
    "hardcore_hybrid": {
        "kick_end_hz": 60.0, "kick_pitch_ms": 65.0, "kick_drive": 4.2,
        "bass_character": "gated", "bass_drive": 2.6,
        "chord_character": "sparse", "lead_character": "sharp",
        "levels": (0.80, 0.37, 0.18, 0.53, 0.16, 0.19, 0.24),
    },
}


def _numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError('Preview synthesis requires pip install -e ".[preview]"') from exc
    return np


def _safe_path(base: Path, relative: str) -> Path:
    """Do not trust relative paths in an externally supplied bundle manifest."""
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError(f"Missing/unsafe MIDI path: {relative}")
    return path


def _read_notes(path: Path, expected_bpm: float) -> list[tuple[float, float, int, int]]:
    mid = mido.MidiFile(path)
    if mid.ticks_per_beat <= 0:
        raise ValueError("invalid ticks_per_beat")
    ppq = mid.ticks_per_beat
    events = []
    found_tempo = False
    for track in mid.tracks:
        ticks = 0
        starts: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for event in track:
            ticks += event.time
            if event.type == "set_tempo":
                bpm = mido.tempo2bpm(event.tempo)
                if abs(bpm - expected_bpm) > 0.03:
                    raise ValueError(f"{path.name}: expected {expected_bpm} BPM, found {bpm:.3f}")
                found_tempo = True
            if event.type == "note_on" and event.velocity > 0:
                starts.setdefault((event.channel, event.note), []).append((ticks, event.velocity))
            elif event.type == "note_off" or (event.type == "note_on" and event.velocity == 0):
                queue = starts.get((event.channel, event.note), [])
                if queue:
                    onset, velocity = queue.pop(0)
                    if ticks > onset:
                        events.append((onset / ppq, (ticks - onset) / ppq, event.note, velocity))
        if any(starts.values()):
            raise ValueError(f"{path.name}: unclosed MIDI notes")
    if not found_tempo:
        raise ValueError(f"{path.name}: tempo missing")
    return sorted(events)


def _oscillator(role, mode, frequency, t, duration, velocity, rng):
    """Role-aware sound design from controllable DSP, no external samples."""
    np = _numpy()
    p = SOUND_PROFILES[mode]
    two_pi = 2 * np.pi
    vel = velocity / 127.0
    if role == "kick":
        tau = p["kick_pitch_ms"] / 1000
        start_hz = 185 if mode == "hardcore_hybrid" else 151
        phase = two_pi * (p["kick_end_hz"] * t
                          + (start_hz - p["kick_end_hz"]) * tau * (1 - np.exp(-t / tau)))
        body = np.sin(phase) * np.exp(-t / (0.19 if mode == "groove" else 0.26))
        click = rng.normal(0, 1, len(t)) * np.exp(-t / 0.004) * 0.16
        return np.tanh((body + click) * p["kick_drive"]) * vel * 0.95
    if role == "drums":
        # MIDI 39 clap, 42 closed hat, 46 open hat. Fixed-noise design, no samples.
        if frequency == 39:
            noise = rng.normal(0, 1, len(t))
            env = np.exp(-t / 0.055) * (0.6 + 0.4 * np.cos(two_pi * 24 * t) ** 2)
            return np.tanh((noise - np.roll(noise, 1)) * 0.38) * env * vel
        tau = 0.11 if frequency == 46 else 0.032
        noise = rng.normal(0, 1, len(t))
        return np.tanh((noise - np.roll(noise, 1)) * 0.32) * np.exp(-t / tau) * vel
    if role == "percussion":
        freq = {64: 540, 67: 715, 56: 805}.get(frequency, 560)
        tone = np.sin(two_pi * freq * t + 0.8 * np.sin(two_pi * 97 * t))
        tone += 0.3 * np.sin(two_pi * freq * 1.47 * t)
        return np.tanh(tone * 0.8) * np.exp(-t / 0.07) * vel
    if role == "bass":
        phase = two_pi * frequency * t
        if p["bass_character"] == "round":
            tone = np.sin(phase) + 0.22 * np.sin(2 * phase)
        elif p["bass_character"] == "fm_donk":
            tone = np.sin(phase + 5.3 * np.exp(-t / 0.055) * np.sin(2.9 * phase))
        else:
            tone = np.sin(phase) + 0.34 * np.sin(3 * phase)
        envelope = (1 - np.exp(-t / 0.003)) * np.exp(-np.maximum(0, t - duration) / 0.035)
        envelope *= np.minimum(1, (duration + 0.035 - t) / 0.035).clip(0, 1)
        return np.tanh(tone * p["bass_drive"]) * envelope * vel
    phase = two_pi * frequency * t
    if role == "chords":
        detune = 0.0035 if mode == "trance_bounce" else 0.0015
        tone = (np.sin(phase) + 0.38 * np.sin(2 * phase)
                + 0.30 * np.sin(phase * (1 + detune))
                + 0.22 * np.sin(phase * (1 - detune)))
        attack = 0.065 if mode == "trance_bounce" else 0.012
        envelope = (1 - np.exp(-t / attack)) * np.exp(-np.maximum(0, t - duration) / 0.11)
        return np.tanh(tone * 0.7) * envelope * vel * 0.6
    if role == "arp":
        tone = np.sin(phase) + 0.33 * np.sin(2 * phase) + 0.13 * np.sin(4 * phase)
        return np.tanh(tone) * np.exp(-t / 0.13) * vel * 0.58
    # lead: intentionally new gesture, distinct colour by prototype.
    vibrato = 0.002 * np.sin(two_pi * 5.2 * t)
    tone = np.sin(phase * (1 + vibrato))
    tone += (0.26 if mode == "groove" else 0.50) * np.sin(2 * phase)
    tone += (0.05 if mode == "groove" else 0.18) * np.sin(3 * phase)
    env = (1 - np.exp(-t / 0.008)) * np.exp(-np.maximum(0, t - duration) / 0.06)
    return np.tanh(tone * (1.3 if mode == "hardcore_hybrid" else 0.95)) * env * vel * 0.67


def _write_wav(path: Path, samples, sample_rate: int) -> dict:
    np = _numpy()
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) if len(samples) else 0.0
    if peak > 1:
        raise ValueError(f"audio exceeds digital full scale: {peak:.3f}")
    pcm = np.round(np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(pcm)
    return {
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "peak_dbfs": round(20 * math.log10(peak), 2) if peak > 0 else None,
        "rms_dbfs": round(20 * math.log10(rms), 2) if rms > 0 else None,
        "non_silent": rms > 1e-5,
    }


def render_mode(bundle: Path, out: Path, mode: str, *, sample_rate: int = SAMPLE_RATE) -> dict:
    """Render full 16-bar experimental audio and per-role stems; no overwrite."""
    np = _numpy()
    if mode not in MODES:
        raise ValueError(f"invalid mode: {mode}")
    if not 16000 <= sample_rate <= 48000:
        raise ValueError("preview sample rate must be between 16kHz and 48kHz")
    bundle = bundle.resolve()
    meta = json.loads((bundle / "prototype_manifest.json").read_text(encoding="utf-8"))
    if meta.get("schema_version") != "1.0":
        raise ValueError("unsupported prototype manifest")
    if mode not in meta.get("experiments", {}):
        raise ValueError(f"bundle has no {mode!r} prototype")
    bpm, bars = float(meta["bpm"]), int(meta["bars"])
    if bpm <= 0 or bars <= 0:
        raise ValueError("invalid arrangement")
    duration = bars * 4 * 60 / bpm + 0.6  # synth release; not an Ardour mastering tail
    length = round(duration * sample_rate)
    profile = SOUND_PROFILES[mode]
    exp = meta["experiments"][mode]
    lanes = {}
    note_counts = {}
    for role in ROLE_ORDER:
        path = _safe_path(bundle, exp["midi_files"][role])
        notes = _read_notes(path, bpm)
        note_counts[role] = len(notes)
        audio = np.zeros(length, dtype=np.float32)
        rng = np.random.default_rng(int(meta["seed"]) + 97 * (ROLE_ORDER.index(role) + 1))
        for start_beat, duration_beats, pitch, velocity in notes:
            onset = round(start_beat * 60 / bpm * sample_rate)
            duration_s = duration_beats * 60 / bpm
            tail = 0.4 if role == "kick" else 0.16 if role in ("drums", "percussion") else 0.12
            if role == "chords":
                tail = 0.3
            if role == "arp":
                tail = 0.23
            span = min(round((duration_s + tail) * sample_rate), length - onset)
            if span <= 0:
                continue
            t = np.arange(span, dtype=np.float64) / sample_rate
            frequency = 440 * 2 ** ((pitch - 69) / 12)
            event = _oscillator(role, mode, pitch if role in ("drums", "percussion") else frequency,
                                t, duration_s, velocity, rng)
            audio[onset:onset + span] += event.astype(np.float32)
        audio *= profile["levels"][ROLE_ORDER.index(role)]
        if role == "bass":
            # Sidechain audition: kick suppresses bass for ~140 ms, not a DAW effect.
            pos = (np.arange(length) / sample_rate) % (60 / bpm)
            duck = 0.35 + 0.65 * np.minimum(pos / 0.14, 1.0)
            audio *= duck.astype(np.float32)
        lanes[role] = audio

    mix = sum(lanes.values(), np.zeros(length, dtype=np.float32))
    rms = float(np.sqrt(np.mean(mix.astype(np.float64) ** 2)))
    peak = float(np.max(np.abs(mix)))
    if rms < 1e-7:
        raise ValueError("empty/silent preview mix")
    gain = min(3.0, 0.126 / rms, 0.78 / peak)
    out = out.resolve()
    if out.exists():
        raise FileExistsError(f"refusing to overwrite preview directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    (out / "stems").mkdir()
    files = {}
    files["master"] = _write_wav(out / "preview.wav", mix * gain, sample_rate)
    for role in ROLE_ORDER:
        files[role] = _write_wav(out / "stems" / f"{role}.wav", lanes[role] * gain, sample_rate)
    report = {
        "schema_version": "1.0",
        "source": "original_generated_midi",
        "backend": "seion-numpy-preview",
        "quality_status": "synthetic_preview_unreviewed",
        "not": ["Ardour", "Surge XT", "mastered audio", "artist style fingerprint"],
        "mode": mode,
        "bpm": bpm,
        "bars": bars,
        "sample_rate": sample_rate,
        "duration_seconds": round(duration, 3),
        "sound_profile": {k: v for k, v in profile.items() if k != "levels"},
        "levels": dict(zip(ROLE_ORDER, profile["levels"], strict=True)),
        "note_counts": note_counts,
        "normalization_gain": round(gain, 6),
        "files": files,
        "gate": "requires_human_listening",
    }
    (out / "preview_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=("all", *MODES), default="all")
    parser.add_argument("--sample-rate", type=int, default=SAMPLE_RATE)
    args = parser.parse_args(argv)
    modes = MODES if args.mode == "all" else (args.mode,)
    for mode in modes:
        dest = args.out / mode
        report = render_mode(args.bundle, dest, mode, sample_rate=args.sample_rate)
        print(f"{mode}: {dest / 'preview.wav'} | {report['duration_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
