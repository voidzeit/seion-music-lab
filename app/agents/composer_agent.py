"""Composer Agent — generate the editable material and explain every choice.

Deterministic: it calls the music generators and records a decision log. The
decision log is the point — it teaches *why* each layer is the way it is.
"""

from __future__ import annotations

from app.music import (
    filter_open_automation,
    generate_arp_track,
    generate_bass_track,
    generate_chord_track,
    generate_drum_track,
)
from app.music.constants import BEATS_PER_BAR
from app.schemas import AutomationEvent, DecisionLogEntry, Track, UserRequest


def compose(
    request: UserRequest,
    style_context: dict,
) -> tuple[list[Track], list[AutomationEvent], list[DecisionLogEntry]]:
    progression = request.progression
    bars = request.bars
    artists = ", ".join(style_context.get("artists", request.style_targets)) or "the references"

    chords = generate_chord_track(progression, bars, BEATS_PER_BAR)
    bass = generate_bass_track(progression, bars, BEATS_PER_BAR)
    arp = generate_arp_track(progression, bars, BEATS_PER_BAR)
    drums = generate_drum_track(bars, BEATS_PER_BAR)

    automation = [filter_open_automation(arp.name, bars, BEATS_PER_BAR)]

    decisions = [
        DecisionLogEntry(
            decision_id="d001",
            agent="composer_agent",
            type="harmony",
            decision=f"Use the progression {' - '.join(progression)} as warm seventh chords.",
            reason=(
                "Minor 7 and major 7 voicings give nostalgia and warmth without "
                "sounding too dark or too happy. One chord per bar keeps a slow "
                "harmonic rhythm so the loop feels hypnotic, not busy."
            ),
            references=style_context.get("artists", []),
            expected_effect="warmth, nostalgia, harmonic softness",
        ),
        DecisionLogEntry(
            decision_id="d002",
            agent="composer_agent",
            type="bass",
            decision="Play the chord root on every off-beat in a low register.",
            reason=(
                "Root notes keep the harmony unambiguous while the off-beat "
                "placement (between the four-on-the-floor kicks) creates the "
                "forward push you hear in house and melodic techno."
            ),
            references=style_context.get("artists", []),
            expected_effect="drive, clarity, forward motion",
        ),
        DecisionLogEntry(
            decision_id="d003",
            agent="composer_agent",
            type="arp",
            decision="Repeat a short up-and-down arp using only chord tones.",
            reason=(
                "A small repeating motif (not a long melody) is what makes an arp "
                "feel hypnotic. Chord tones only means it can never clash with the "
                "harmony, and the low density keeps space to edit."
            ),
            references=[a for a in style_context.get("artists", []) if a in ("NTO", "Stephan Bodzin")]
            or style_context.get("artists", []),
            expected_effect="hypnosis, motion-through-repetition",
        ),
        DecisionLogEntry(
            decision_id="d004",
            agent="composer_agent",
            type="drums",
            decision="Four-on-the-floor kick, clap on 2 and 4, closed hats off-beat, open hat every 2 bars.",
            reason=(
                "This is the spine of warm house: the kick anchors the pulse, the "
                "clap marks the backbeat, the off-beat hats add lift, and the open "
                "hat every second bar stops it feeling static."
            ),
            references=style_context.get("artists", []),
            expected_effect="steady groove, editable, not overloaded",
        ),
        DecisionLogEntry(
            decision_id="d005",
            agent="composer_agent",
            type="automation",
            decision="Open the arp's low-pass filter slowly across the whole loop.",
            reason=(
                f"Following {artists}, tension comes from timbre, not extra notes. "
                "A slow filter open makes the same loop feel like it is growing."
            ),
            references=style_context.get("artists", []),
            expected_effect="rising tension without adding density",
        ),
    ]

    return [chords, bass, arp, drums], automation, decisions
