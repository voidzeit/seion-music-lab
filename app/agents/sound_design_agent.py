"""Sound Design Agent — translate emotional intent into FL Studio sound advice.

Deterministic, reproducible instructions (no plugin automation yet). Keyed by
track role so the teacher can lay it out next to each layer.
"""

from __future__ import annotations

from app.schemas import MusicalIdea

_BASE_SUGGESTIONS: dict[str, list[str]] = {
    "harmony": [
        "Warm pad or electric piano (FLEX warm keys / pad).",
        "Gentle low-pass filter, medium attack, long release.",
        "Light sidechain to the kick for breathing room.",
        "Medium warm reverb; cut lows below ~120 Hz to avoid mud.",
    ],
    "bass": [
        "Mono synth bass (3xOSC sine + a little saw).",
        "Low-pass filter to keep it round; light saturation for body.",
        "Sidechain to the kick so the two never fight.",
        "Keep it in the sub/low-mid range — no need to be loud, just felt.",
    ],
    "arp": [
        "Analog-style pluck with a short envelope.",
        "1/8 delay + large reverb for the hypnotic, spacious feel.",
        "Automate the low-pass filter opening slowly across the loop.",
        "Pan slightly off-centre to sit beside the chords.",
    ],
    "drums": [
        "Clean house kick with a tight tail.",
        "Soft clap layered with a short noise burst on 2 and 4.",
        "Tight closed hats; roll off some lows, add a touch of high shelf.",
        "Subtle swing (8-15%) for groove; keep velocities varied.",
    ],
}


def suggest(idea: MusicalIdea) -> dict[str, list[str]]:
    """Return per-role sound-design tips for the roles present in the idea."""
    present_roles = {t.role for t in idea.tracks}
    out: dict[str, list[str]] = {}
    for role, tips in _BASE_SUGGESTIONS.items():
        if role in present_roles:
            out[role] = list(tips)
    return out
