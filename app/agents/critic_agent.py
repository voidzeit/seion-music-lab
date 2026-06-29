"""Critic Agent — turn weaknesses into concrete, actionable changes.

Deterministic heuristics over the idea + SEION score. Every suggestion names a
target, a change and a reason (no vague 'improve the mix').
"""

from __future__ import annotations

from app.music import analysis
from app.schemas import MusicalIdea, SeionScore


def critique(idea: MusicalIdea, score: SeionScore) -> list[dict]:
    fixes: list[dict] = []

    if score.tension_curve < 0.7:
        fixes.append(
            {
                "target": "arrangement",
                "change": "Add an intro, a 16-bar build and a short break before the drop.",
                "reason": "a single loop is steady by design; structure is what makes energy move.",
            }
        )

    if score.novelty < 0.5:
        fixes.append(
            {
                "target": "arp",
                "change": "Vary the arp motif every 4 bars (shift one note or invert it).",
                "reason": "small variation keeps repetition hypnotic instead of static.",
            }
        )

    arp = idea.track_by_role("arp")
    if arp and analysis.unique_pitch_classes(arp) > 8:
        fixes.append(
            {
                "target": "arp",
                "change": "Thin the arp to 2-3 pitches per bar.",
                "reason": "fewer notes makes it more hypnotic and more 'NTO'.",
            }
        )

    if score.style_match < 0.78:
        fixes.append(
            {
                "target": "sound design",
                "change": "Do a timbre pass: warm pad, analog pluck, wide reverb, sidechain.",
                "reason": "MIDI nails the notes; the rest of the style lives in the sound.",
            }
        )

    # Always leave one ear-training prompt.
    fixes.append(
        {
            "target": "harmony",
            "change": "Try swapping Cmaj7 for Em7 and listen.",
            "reason": "it keeps the loop darker — train your ear on the difference.",
        }
    )

    return fixes
