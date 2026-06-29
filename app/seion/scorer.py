"""The deterministic SEION scorer.

Six components in [0, 1], combined with the weights in
:data:`app.schemas.seion_score.SEION_WEIGHTS`. The scorer never calls an LLM —
it is pure heuristics over the :class:`MusicalIdea`, which keeps scoring fast,
explainable and unit-testable.

Penalises: out-of-scale notes, overload, missing bass/harmony/rhythm.
Rewards:   clear roles, editable separation, coherent traits, repetition with
           small variation, simple hypnotic patterns.
"""

from __future__ import annotations

from collections import defaultdict

from app.music import analysis
from app.music.scales import parse_key
from app.schemas import MusicalIdea, SeionScore, UserRequest
from app.seion.novelty import compute_novelty
from app.seion.style_match import compute_style_match
from app.seion.tension_curve import compute_tension_curve

# Realism ceilings: an MVP loop is quantised, un-humanised and un-mixed, so even
# a flawless skeleton leaves headroom. These keep "perfect" scores honest.
COHERENCE_REALISM = 0.90
EMOTION_REALISM = 0.85
EDITABILITY_REALISM = 0.90


# --------------------------------------------------------------------------- #
# Coherence
# --------------------------------------------------------------------------- #
def _density_ideal(notes_per_bar: float) -> float:
    if 10.0 <= notes_per_bar <= 20.0:
        return 1.0
    if notes_per_bar < 10.0:
        return max(0.4, notes_per_bar / 10.0)
    return max(0.2, 1.0 - (notes_per_bar - 20.0) / 40.0)


def _voicing_spacing_ok(idea: MusicalIdea) -> float:
    """Reward chord voicings that avoid muddy sub-minor-third clusters."""
    harmony = idea.track_by_role("harmony") or idea.track_by_role("pad")
    if harmony is None or not harmony.notes:
        return 0.6
    chords: dict[float, list[int]] = defaultdict(list)
    for note in harmony.notes:
        chords[round(note.start_beat, 3)].append(note.midi)
    clean = 0
    for midis in chords.values():
        ordered = sorted(midis)
        if all(ordered[i + 1] - ordered[i] >= 3 for i in range(len(ordered) - 1)):
            clean += 1
    return clean / len(chords) if chords else 0.6


def compute_coherence(idea: MusicalIdea, request: UserRequest) -> tuple[float, str]:
    in_scale = analysis.in_scale_ratio(idea, idea.key)
    bass_follows = analysis.bass_follows_roots_ratio(idea, request.progression)
    density = _density_ideal(analysis.notes_per_bar(idea))
    spacing = _voicing_spacing_ok(idea)

    raw = 0.45 * in_scale + 0.25 * bass_follows + 0.15 * density + 0.15 * spacing
    score = round(raw * COHERENCE_REALISM, 4)
    note = (
        f"{in_scale * 100:.0f}% of notes are in {idea.key}; bass tracks chord roots "
        f"{bass_follows * 100:.0f}% of the time; density {analysis.notes_per_bar(idea):.1f} "
        f"notes/bar; voicings are clean. (x{COHERENCE_REALISM} MVP realism cap.)"
    )
    return score, note


# --------------------------------------------------------------------------- #
# Emotional clarity
# --------------------------------------------------------------------------- #
def _eval_warm(idea: MusicalIdea, request: UserRequest) -> float:
    score = 0.0
    if analysis.uses_seventh_or_sixth_chords(request.progression):
        score += 0.4
    harmony = idea.track_by_role("harmony") or idea.track_by_role("pad")
    hint = harmony.instrument_hint.lower() if harmony else ""
    if any(k in hint for k in ("pad", "piano", "warm", "flex")):
        score += 0.3
    if 110 <= idea.bpm <= 128:
        score += 0.3
    return min(1.0, score)


def _eval_melancholic(idea: MusicalIdea, request: UserRequest) -> float:
    score = 0.0
    _, mode = parse_key(idea.key)
    if mode != "major":
        score += 0.5
    if analysis.uses_seventh_or_sixth_chords(request.progression):
        score += 0.3
    notes = analysis.all_melodic_notes(idea)
    if not any(n.midi > 84 for n in notes):
        score += 0.2
    return min(1.0, score)


def _eval_hypnotic(idea: MusicalIdea, request: UserRequest) -> float:
    score = 0.3  # one chord per bar => slow harmonic rhythm by construction
    arp = idea.track_by_role("arp")
    if arp and analysis.unique_pitch_classes(arp) <= 9:
        score += 0.4
    drums = next((t for t in idea.tracks if t.is_drum), None)
    if drums and any(e.instrument == "kick" for e in drums.drum_events):
        score += 0.3
    return min(1.0, score)


def _eval_dark(idea: MusicalIdea, request: UserRequest) -> float:
    score = 0.0
    _, mode = parse_key(idea.key)
    if mode != "major":
        score += 0.5
    notes = analysis.all_melodic_notes(idea)
    avg = sum(n.midi for n in notes) / len(notes) if notes else 60
    if avg < 66:
        score += 0.3
    if not any(n.midi > 82 for n in notes):
        score += 0.2
    return min(1.0, score)


def _eval_uplifting(idea: MusicalIdea, request: UserRequest) -> float:
    _, mode = parse_key(idea.key)
    return 0.85 if mode == "major" else 0.3  # conflicts with a minor key


_EMOTION_EVALUATORS = {
    "warm": _eval_warm,
    "melancholic": _eval_melancholic,
    "melancholy": _eval_melancholic,
    "sad": _eval_melancholic,
    "nostalgic": _eval_melancholic,
    "hypnotic": _eval_hypnotic,
    "trippy": _eval_hypnotic,
    "dark": _eval_dark,
    "moody": _eval_dark,
    "uplifting": _eval_uplifting,
    "happy": _eval_uplifting,
    "euphoric": _eval_uplifting,
    "bright": _eval_uplifting,
}


def compute_emotional_clarity(
    idea: MusicalIdea, request: UserRequest
) -> tuple[float, str]:
    targets = request.emotional_targets or ["warm"]
    values = []
    for target in targets:
        evaluator = _EMOTION_EVALUATORS.get(target.strip().lower())
        values.append(evaluator(idea, request) if evaluator else 0.6)
    raw = sum(values) / len(values)
    score = round(raw * EMOTION_REALISM, 4)
    note = (
        f"Targets {', '.join(targets)} score {raw:.2f} on harmony/mode/tempo/arp "
        f"alignment (x{EMOTION_REALISM} cap; timbre seals the emotion in FL)."
    )
    return score, note


# --------------------------------------------------------------------------- #
# Editability
# --------------------------------------------------------------------------- #
def compute_editability(idea: MusicalIdea) -> tuple[float, str]:
    roles = analysis.role_set(idea)
    role_sep = len(roles) / len(idea.tracks) if idea.tracks else 0.0
    not_overloaded = _density_ideal(analysis.notes_per_bar(idea))
    count_ok = 1.0 if 3 <= len(idea.tracks) <= 6 else 0.6

    raw = 0.5 * role_sep + 0.3 * not_overloaded + 0.2 * count_ok
    score = round(raw * EDITABILITY_REALISM, 4)
    note = (
        f"{len(idea.tracks)} tracks, {len(roles)} distinct roles, "
        f"{analysis.notes_per_bar(idea):.1f} notes/bar — each layer is separate and "
        f"easy to swap or thin in FL."
    )
    return score, note


# --------------------------------------------------------------------------- #
# Top level
# --------------------------------------------------------------------------- #
def score_idea(
    idea: MusicalIdea,
    request: UserRequest,
    style_context: dict | None = None,
) -> SeionScore:
    style_context = style_context or {}

    coherence, coherence_note = compute_coherence(idea, request)
    style_match, style_note = compute_style_match(idea, request, style_context)
    emotional, emotion_note = compute_emotional_clarity(idea, request)
    tension, tension_note = compute_tension_curve(idea)
    editability, edit_note = compute_editability(idea)
    novelty, novelty_note = compute_novelty(idea, request)

    components = {
        "coherence": coherence,
        "style_match": style_match,
        "emotional_clarity": emotional,
        "tension_curve": tension,
        "editability": editability,
        "novelty": novelty,
    }
    overall = SeionScore.compute_overall(components)

    return SeionScore(
        **components,
        overall=overall,
        details={
            "coherence": coherence_note,
            "style_match": style_note,
            "emotional_clarity": emotion_note,
            "tension_curve": tension_note,
            "editability": edit_note,
            "novelty": novelty_note,
        },
    )
