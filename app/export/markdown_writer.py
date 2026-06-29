"""Render the human-facing explanation.md.

This is the teacher's voice: it turns the structured idea + score into prose a
beginner can learn from. The renderer takes plain data (no agent imports) so it
stays decoupled and easy to test.
"""

from __future__ import annotations

from pathlib import Path

from app.schemas import MusicalIdea

_SCORE_LABELS = {
    "coherence": "Coherence",
    "style_match": "Style match",
    "emotional_clarity": "Emotional clarity",
    "tension_curve": "Tension curve",
    "editability": "Editability",
    "novelty": "Novelty",
}

_FL_IMPORT_STEPS = [
    "Open FL Studio and set the project tempo to the BPM above.",
    "Drag each `.mid` file (chords, bass, arp, drums) onto its own track in the "
    "Playlist, or import via *File ▸ Import ▸ MIDI file*.",
    "For chords/bass/arp, add the suggested instrument to each Channel Rack slot.",
    "Route the drum MIDI to a kit (FPC / Slicer / individual samples) — the notes "
    "use the General MIDI map (kick 36, clap 39, closed hat 42, open hat 46).",
    "Or audition everything at once by dropping `full_loop.mid` in first, then "
    "swap the placeholder instruments for your own.",
]


def _score_table(idea: MusicalIdea) -> str:
    score = idea.seion_scores
    if score is None:
        return "_No SEION score available._"
    rows = ["| Component | Score | What it means |", "| --- | --- | --- |"]
    for key, label in _SCORE_LABELS.items():
        value = getattr(score, key)
        note = score.details.get(key, "")
        rows.append(f"| {label} | {value:.2f} | {note} |")
    rows.append(f"| **Overall** | **{score.overall:.2f}** | Weighted SEION score. |")
    return "\n".join(rows)


def _decision_section(idea: MusicalIdea) -> str:
    if not idea.decision_log:
        return "_No decisions recorded._"
    blocks = []
    for entry in idea.decision_log:
        refs = f" _(refs: {', '.join(entry.references)})_" if entry.references else ""
        blocks.append(
            f"**{entry.decision_id} · {entry.type}** — {entry.decision}{refs}\n\n"
            f"> {entry.reason}\n>\n> _Expected effect: {entry.expected_effect}_"
        )
    return "\n\n".join(blocks)


def _arrangement_section(idea: MusicalIdea) -> str:
    sections = idea.sections
    if not sections or len(sections) < 2:
        return (
            "_Single steady loop (no full arrangement). Ask SEION to vary it or "
            "generate 16+ bars for an intro/build/drop structure._"
        )
    rows = ["| Section | Bars | Energy | Role |", "| --- | --- | --- | --- |"]
    for sec in sections:
        last = sec.start_bar + sec.length_bars - 1
        bar_range = f"{sec.start_bar}-{last}" if sec.length_bars > 1 else f"{sec.start_bar}"
        bar = round(sec.energy * 20)
        meter = "#" * bar + "." * (20 - bar)
        rows.append(f"| {sec.name} | {bar_range} | `{meter}` {sec.energy:.2f} | {sec.description} |")
    return "\n".join(rows)


def _track_section(idea: MusicalIdea) -> str:
    lines = []
    for track in idea.tracks:
        count = track.event_count
        effects = ", ".join(track.mixer_hint.effects) or "—"
        lines.append(
            f"### {track.name}  ·  role: `{track.role}`\n"
            f"- **Events:** {count}\n"
            f"- **Suggested instrument:** {track.instrument_hint or '—'}\n"
            f"- **Mixer hint:** {track.mixer_hint.volume_db:+.0f} dB, "
            f"effects: {effects}"
        )
    return "\n\n".join(lines)


def _sound_design_section(sound_design: dict[str, list[str]]) -> str:
    if not sound_design:
        return "_No sound-design suggestions._"
    blocks = []
    for role, tips in sound_design.items():
        bullets = "\n".join(f"- {tip}" for tip in tips)
        blocks.append(f"**{role.capitalize()}**\n{bullets}")
    return "\n\n".join(blocks)


def _next_steps_section(critique: list[dict]) -> str:
    if not critique:
        return "- Listen, then tell SEION what to change (darker, simpler, more drive…)."
    lines = []
    for fix in critique:
        target = fix.get("target", "?")
        change = fix.get("change", "")
        reason = fix.get("reason", "")
        lines.append(f"- **{target}:** {change} — _{reason}_")
    return "\n".join(lines)


def build_explanation_markdown(
    idea: MusicalIdea,
    *,
    style_context: dict | None = None,
    sound_design: dict[str, list[str]] | None = None,
    critique: list[dict] | None = None,
    warnings: list[str] | None = None,
) -> str:
    style_context = style_context or {}
    sound_design = sound_design or {}
    critique = critique or []
    warnings = warnings or []

    styles = ", ".join(idea.style_targets) or "—"
    emotions = ", ".join(idea.emotional_targets) or "—"
    warning_block = (
        "\n".join(f"- ⚠️ {w}" for w in warnings) if warnings else "- None. Clean loop. ✅"
    )

    overall = idea.seion_scores.overall if idea.seion_scores else 0.0

    return f"""# {idea.title}

_A SEION Music Lab idea — generated material you can edit, not a finished track._

## 1. Summary

A **{idea.bars}-bar loop** at **{idea.bpm} BPM** in **{idea.key}**, aimed at a
**{emotions}** feeling in the style of **{styles}**. It contains four clearly
separated, editable layers: warm seventh-chord harmony, an offbeat root bass, a
hypnotic chord-tone arp, and a four-on-the-floor kit. Overall SEION score:
**{overall:.2f}**.

## 2. Musical frame

| Field | Value |
| --- | --- |
| BPM | {idea.bpm} |
| Key | {idea.key} |
| Time signature | {idea.time_signature} |
| Bars | {idea.bars} |
| Progression | {" - ".join(style_context.get("progression", []))} |
| Style targets | {styles} |
| Emotional targets | {emotions} |

## 3. Arrangement

{_arrangement_section(idea)}

## 4. Track-by-track

{_track_section(idea)}

## 5. Why these decisions (musical decision log)

{_decision_section(idea)}

## 6. What the SEION score means

{_score_table(idea)}

The overall score is a weighted blend (coherence 25%, style 20%, emotion 20%,
tension 15%, editability 10%, novelty 10%). It is a compass, not a grade — a
"good" loop you love can score lower than a safe one. Use the per-row notes to
decide what to push next.

## 7. Suggested FL Studio sound design

{_sound_design_section(sound_design)}

## 8. How to import the MIDI into FL Studio

{chr(10).join(f"{i}. {step}" for i, step in enumerate(_FL_IMPORT_STEPS, 1))}

## 9. Validation notes

{warning_block}

## 10. Suggested next modifications

{_next_steps_section(critique)}
"""


def write_markdown(path: str | Path, text: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
