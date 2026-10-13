"""Acceptance checks for rendered WAVs (stdlib only)."""

from __future__ import annotations

import math
import wave
from array import array
from dataclasses import asdict, dataclass
from pathlib import Path

SILENCE_RMS_DBFS = -60.0
WINDOW_SECONDS = 0.5


@dataclass(frozen=True)
class WavReport:
    file: str
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: int
    peak_dbfs: float
    rms_dbfs: float
    nonzero_samples: int
    active_ratio: float  # share of 0.5 s windows louder than SILENCE_RMS_DBFS
    passed: bool

    def as_dict(self) -> dict:
        return asdict(self)


def _db(x: float) -> float:
    return 20 * math.log10(x) if x > 0 else float("-inf")


def check_wav(path: Path) -> WavReport:
    with wave.open(str(path), "rb") as w:
        sr, ch, width, frames = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(frames)
    if width == 2:
        samples = array("h", raw)
        full_scale = 32768.0
    elif width == 3:
        samples = array("i", (int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw), 3)))
        full_scale = 8388608.0
    elif width == 4:
        samples = array("i", raw)
        full_scale = 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {width}")
    n = len(samples) or 1
    peak = max((abs(s) for s in samples), default=0) / full_scale
    rms = math.sqrt(sum(s * s for s in samples) / n) / full_scale
    nonzero = sum(1 for s in samples if s)
    duration = frames / sr if sr else 0.0
    win = max(int(sr * WINDOW_SECONDS) * ch, 1)
    windows = [samples[i:i + win] for i in range(0, len(samples), win)]
    active = sum(
        1 for w in windows if w and _db(math.sqrt(sum(s * s for s in w) / len(w)) / full_scale) > SILENCE_RMS_DBFS
    )
    active_ratio = active / len(windows) if windows else 0.0
    passed = duration > 0 and nonzero > 0 and _db(rms) > SILENCE_RMS_DBFS
    return WavReport(
        file=path.name,
        duration_seconds=round(duration, 3),
        sample_rate=sr,
        channels=ch,
        bit_depth=width * 8,
        peak_dbfs=round(_db(peak), 2),
        rms_dbfs=round(_db(rms), 2),
        nonzero_samples=nonzero,
        active_ratio=round(active_ratio, 3),
        passed=passed,
    )


def note_coverage(notes: list[tuple], bpm: float, duration: float) -> float:
    """Share of 0.5 s windows (over ``duration``) touched by at least one note."""
    n_windows = max(math.ceil(duration / WINDOW_SECONDS), 1)
    hit = set()
    sec_per_beat = 60.0 / bpm
    for start, length, *_ in notes:
        a = int(start * sec_per_beat / WINDOW_SECONDS)
        b = int((start + length) * sec_per_beat / WINDOW_SECONDS)
        hit.update(range(a, min(b, n_windows - 1) + 1))
    return len(hit) / n_windows
