"""How much does the idea do something of its own?

Deterministic generation is intentionally safe and repetitive, so novelty is
moderate — the real novelty comes from the producer's edits, sound design and
the way references are blended.
"""

from __future__ import annotations

from app.schemas import MusicalIdea, UserRequest

NOVELTY_BASE = 0.30
MULTI_REFERENCE_BONUS = 0.08
VARIATION_BONUS = 0.05


def compute_novelty(idea: MusicalIdea, request: UserRequest) -> tuple[float, str]:
    score = NOVELTY_BASE
    reasons = ["safe, repeating loop (base)"]

    if len({s.lower() for s in request.style_targets}) >= 2:
        score += MULTI_REFERENCE_BONUS
        reasons.append("blends 2+ references")

    # Any within-loop variation? (e.g. the open hat every 2nd bar.)
    drums = next((t for t in idea.tracks if t.is_drum), None)
    if drums and any(e.instrument == "open_hat" for e in drums.drum_events):
        score += VARIATION_BONUS
        reasons.append("micro-variation across bars (open hat)")

    score = round(min(1.0, score), 4)
    note = "; ".join(reasons) + ". Push novelty with your own edits and sound design."
    return score, note
