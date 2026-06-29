"""Variation Agent — turn a free-form "make it ..." into a VariationSpec.

Deterministic keyword parser (no LLM), mirroring the intake agent. A future
LLM can replace :func:`parse_direction` while keeping the same return type, so
the rest of the variation pipeline is unchanged.
"""

from __future__ import annotations

from app.music.variations import VariationSpec

# Each rule: trigger phrases -> a function that mutates the spec in place.
# Phrases are matched as substrings of the lower-cased direction text.
_DARKER = ("darker", "dark", "less happy", "sad", "moody", "melancholic", "moodier")
_BRIGHTER = ("brighter", "happier", "lighter", "uplifting", "sunnier")
_SIMPLER = ("simpler", "simple arp", "simpler arp", "less busy", "minimal", "stripped arp")
_DRIVE = ("more drive", "driving", "punchier", "harder", "energetic", "more energy", "push")
_SOFTER = ("softer", "calmer", "gentler", "gentle", "chill", "smoother", "warmer")
_SPARSER = ("sparser", "more space", "spacier", "emptier", "breathe")
_HYPNOTIC = ("hypnotic", "trippy", "more hypnotic")


def _has(text: str, phrases: tuple[str, ...]) -> bool:
    return any(p in text for p in phrases)


def parse_direction(direction: str) -> VariationSpec:
    """Best-effort parse of a free-form direction into a VariationSpec."""
    text = (direction or "").strip().lower()
    spec = VariationSpec(raw=direction.strip())

    if _has(text, _DARKER):
        spec.arp_octave_shift = -1
        spec.harmony_thin_top = True
        spec.velocity_scale *= 0.95
        spec.energy_shift -= 0.08
        spec.add_emotions.append("dark")
        spec.labels.append("darker")

    if _has(text, _BRIGHTER):
        spec.arp_octave_shift = 1
        spec.energy_shift += 0.08
        spec.add_emotions.append("uplifting")
        spec.labels.append("brighter")

    if _has(text, _SIMPLER) or _has(text, _HYPNOTIC):
        spec.simpler_arp = True
        spec.add_emotions.append("hypnotic")
        spec.labels.append("simpler/hypnotic arp")

    if _has(text, _DRIVE):
        spec.bass_double = True
        spec.velocity_scale *= 1.05
        spec.energy_shift += 0.12
        spec.labels.append("more drive")

    if _has(text, _SOFTER):
        spec.velocity_scale *= 0.9
        spec.energy_shift -= 0.08
        spec.add_emotions.append("warm")
        spec.labels.append("softer")

    if _has(text, _SPARSER):
        spec.arp_keep_ratio = 0.5
        spec.thin_hats = True
        spec.energy_shift -= 0.05
        spec.labels.append("sparser")

    # Round the accumulated velocity scale so repeated multipliers stay clean.
    spec.velocity_scale = round(spec.velocity_scale, 3)
    return spec
