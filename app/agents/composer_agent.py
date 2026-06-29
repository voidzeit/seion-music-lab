"""Composer Agent — generate the editable material and explain every choice.

Deterministic: it calls the music generators and records a decision log. The
decision log is the point — it teaches *why* each layer is the way it is. With a
song arrangement (Sprint 3) the drums follow the sections and the filter
automation tracks each section's energy.
"""

from __future__ import annotations

from app.music import (
    filter_open_automation,
    generate_arp_track,
    generate_bass_track,
    generate_chord_track,
    generate_drum_track,
    section_filter_automation,
)
from app.music.constants import BEATS_PER_BAR
from app.schemas import AutomationEvent, DecisionLogEntry, Section, Track, UserRequest


def compose(
    request: UserRequest,
    style_context: dict,
    sections: list[Section] | None = None,
    swing: float = 0.0,
    humanize: bool = False,
) -> tuple[list[Track], list[AutomationEvent], list[DecisionLogEntry]]:
    progression = request.progression
    bars = request.bars
    artists = ", ".join(style_context.get("artists", request.style_targets)) or "the references"

    chords = generate_chord_track(progression, bars, BEATS_PER_BAR)
    bass = generate_bass_track(progression, bars, BEATS_PER_BAR)
    arp = generate_arp_track(progression, bars, BEATS_PER_BAR)
    drums = generate_drum_track(
        bars, BEATS_PER_BAR, sections=sections, swing=swing, humanize=humanize
    )

    has_arrangement = bool(sections) and len(sections) > 1
    if has_arrangement:
        automation = section_filter_automation(arp.name, sections)
    else:
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
            decision=_drum_decision(has_arrangement, swing),
            reason=(
                "This is the spine of warm house: the kick anchors the pulse, the "
                "clap marks the backbeat, the off-beat hats add lift. Holding the "
                "kick back in the intro/break and dropping a fill before the drop "
                "is what makes the energy actually move."
            ),
            references=style_context.get("artists", []),
            expected_effect="steady groove that breathes with the arrangement",
        ),
        DecisionLogEntry(
            decision_id="d005",
            agent="composer_agent",
            type="automation",
            decision=_automation_decision(has_arrangement),
            reason=(
                f"Following {artists}, tension comes from timbre, not extra notes. "
                "Moving the filter with each section makes the same material grow "
                "and release across the track."
            ),
            references=style_context.get("artists", []),
            expected_effect="rising tension without adding density",
        ),
    ]

    if has_arrangement:
        decisions.append(_arrangement_decision(sections))

    return [chords, bass, arp, drums], automation, decisions


def _drum_decision(has_arrangement: bool, swing: float) -> str:
    feel = " with a touch of swing" if swing > 0 else ""
    if has_arrangement:
        return (
            "Four-on-the-floor that follows the arrangement: hats-only intro, "
            f"kick through build/main/drop, kick-less break, fills at transitions{feel}."
        )
    return (
        "Four-on-the-floor kick, clap on 2 and 4, closed hats off-beat, open hat "
        f"every 2 bars{feel}."
    )


def _automation_decision(has_arrangement: bool) -> str:
    if has_arrangement:
        return "Move the arp's low-pass filter per section so the timbre tracks the energy curve."
    return "Open the arp's low-pass filter slowly across the whole loop."


def _arrangement_decision(sections: list[Section]) -> DecisionLogEntry:
    layout = ", ".join(f"{s.name} x{s.length_bars}" for s in sections)
    return DecisionLogEntry(
        decision_id="d006",
        agent="composer_agent",
        type="arrangement",
        decision=f"Arrange the loop into sections: {layout}.",
        reason=(
            "A single loop is steady by design. Splitting it into intro / build / "
            "main / break / drop / outro with a rising-then-releasing energy curve "
            "is what turns a loop into a track you can play start to finish."
        ),
        references=[],
        expected_effect="energy that moves with intent; higher tension-curve score",
    )
