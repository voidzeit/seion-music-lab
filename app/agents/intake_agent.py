"""Intake Agent — produce a normalised UserRequest.

The CLI usually builds a UserRequest directly. This agent also offers a light
free-form parser so a future prompt like
"warm NTO loop, 124 bpm, A minor, 16 bars" can be turned into a request without
an LLM. (An LLM-backed parser can replace ``parse_prompt`` later.)
"""

from __future__ import annotations

import re

from app.schemas import UserRequest

_BPM_RE = re.compile(r"(\d{2,3})\s*bpm", re.IGNORECASE)
_BARS_RE = re.compile(r"(\d{1,3})\s*bars?", re.IGNORECASE)
_KEY_RE = re.compile(r"\b([A-G][#b]?)\s*(minor|major|min|maj)\b", re.IGNORECASE)


def normalize(request: UserRequest) -> UserRequest:
    """Clean up an already-structured request (trim/dedup target lists)."""
    request.style_targets = [s.strip() for s in request.style_targets if s.strip()]
    request.emotional_targets = [e.strip() for e in request.emotional_targets if e.strip()]
    if not request.title:
        request.title = _default_title(request)
    return request


def parse_prompt(prompt: str, **overrides) -> UserRequest:
    """Best-effort parse of a free-form prompt into a UserRequest."""
    data: dict = {"raw_prompt": prompt}

    bpm = _BPM_RE.search(prompt)
    if bpm:
        data["bpm"] = int(bpm.group(1))

    bars = _BARS_RE.search(prompt)
    if bars:
        data["bars"] = int(bars.group(1))

    key = _KEY_RE.search(prompt)
    if key:
        mode = key.group(2).lower()
        mode = "minor" if mode.startswith("min") else "major"
        data["key"] = f"{key.group(1).upper()} {mode}"

    data.update(overrides)
    return normalize(UserRequest(**data))


def _default_title(request: UserRequest) -> str:
    emo = "_".join(e.lower() for e in request.emotional_targets[:2]) or "loop"
    return f"{emo}_{request.bpm}bpm"
