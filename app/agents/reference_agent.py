"""Reference Agent — turn artist names into *actionable* musical traits.

Deterministic for the MVP: a small built-in registry maps each reference to
MIDI-achievable traits, and ``build_style_context`` merges the selected
references into the dict the SEION scorer consumes. (A later version can read
``prompts/styles/*.md`` and/or the style graph instead.)
"""

from __future__ import annotations

# Canonical trait profiles. Only traits that MIDI can carry are scored; the
# 'timbre' / 'notes' fields are advice surfaced to the producer.
STYLE_PROFILES: dict[str, dict] = {
    "computer data": {
        "label": "Computer Data",
        "bpm_range": (118, 126),
        "prefers_minor": True,
        "wants_seventh_chords": True,
        "wants_offbeat_bass": True,
        "wants_hypnotic_arp": False,
        "wants_four_on_floor": True,
        "wants_filter_automation": False,
        "notes": "Warm healing house: soft maj7/min7 pads, round bass, gentle swing.",
    },
    "dj heartstring": {
        "label": "DJ Heartstring",
        "bpm_range": (140, 150),
        "prefers_minor": True,
        "wants_seventh_chords": True,
        "wants_offbeat_bass": True,
        "wants_hypnotic_arp": False,
        "wants_four_on_floor": True,
        "wants_filter_automation": True,
        "notes": "Emotional trance/eurodance: supersaw chords, offbeat bass, big breaks.",
    },
    "floating points": {
        "label": "Floating Points",
        "bpm_range": (118, 128),
        "prefers_minor": True,
        "wants_seventh_chords": True,
        "wants_offbeat_bass": False,
        "wants_hypnotic_arp": True,
        "wants_four_on_floor": False,
        "wants_filter_automation": True,
        "notes": "Organic, jazzy harmony, evolving textures, live-feeling groove.",
    },
    "fred again": {
        "label": "Fred again..",
        "bpm_range": (128, 150),
        "prefers_minor": True,
        "wants_seventh_chords": True,
        "wants_offbeat_bass": True,
        "wants_hypnotic_arp": False,
        "wants_four_on_floor": True,
        "wants_filter_automation": False,
        "notes": "Intimate vocal chops, emotional chords, lo-fi warmth, garage swing.",
    },
    "nto": {
        "label": "NTO",
        "bpm_range": (122, 126),
        "prefers_minor": True,
        "wants_seventh_chords": True,
        "wants_offbeat_bass": True,
        "wants_hypnotic_arp": True,
        "wants_four_on_floor": True,
        "wants_filter_automation": True,
        "notes": "Dark melodic techno: short repeating arps, slow filter opens, wide reverb.",
    },
    "stephan bodzin": {
        "label": "Stephan Bodzin",
        "bpm_range": (122, 128),
        "prefers_minor": True,
        "wants_seventh_chords": True,
        "wants_offbeat_bass": True,
        "wants_hypnotic_arp": True,
        "wants_four_on_floor": True,
        "wants_filter_automation": True,
        "notes": "Big detuned analog lead motifs, driving bass, cinematic builds.",
    },
}

# A few convenient aliases.
_ALIASES = {
    "computer data / healing": "computer data",
    "healing": "computer data",
    "fred again..": "fred again",
    "bodzin": "stephan bodzin",
}


def _lookup(name: str) -> dict | None:
    key = name.strip().lower()
    key = _ALIASES.get(key, key)
    return STYLE_PROFILES.get(key)


def traits_for(name: str) -> dict | None:
    """Return the trait profile for a single reference (or None if unknown)."""
    return _lookup(name)


def build_style_context(style_targets: list[str]) -> dict:
    """Merge selected references into one style context for scoring + teaching."""
    profiles = [p for p in (_lookup(s) for s in style_targets) if p is not None]
    if not profiles:
        # Fall back to a sensible warm melodic-techno default.
        profiles = [STYLE_PROFILES["nto"]]

    los = [p["bpm_range"][0] for p in profiles]
    his = [p["bpm_range"][1] for p in profiles]

    def any_true(flag: str) -> bool:
        return any(p.get(flag, False) for p in profiles)

    return {
        "artists": [p["label"] for p in profiles],
        "bpm_range": (min(los), max(his)),
        "prefers_minor": any_true("prefers_minor"),
        "wants_seventh_chords": any_true("wants_seventh_chords"),
        "wants_offbeat_bass": any_true("wants_offbeat_bass"),
        "wants_hypnotic_arp": any_true("wants_hypnotic_arp"),
        "wants_four_on_floor": any_true("wants_four_on_floor"),
        "wants_filter_automation": any_true("wants_filter_automation"),
        "notes": [f"{p['label']}: {p['notes']}" for p in profiles],
    }
