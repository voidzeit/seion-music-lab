"""Guardrails: keep generation inside the MVP's stated principles.

- prefer loops of 8/16/32 bars,
- keep tempo sane,
- enforce the quality gate that triggers a revision pass.
"""

from __future__ import annotations

from app.schemas import SeionScore, UserRequest

PREFERRED_BARS = {8, 16, 32}
QUALITY_GATE = 0.72  # below this, the orchestrator attempts a revision


def check_request(request: UserRequest) -> list[str]:
    warnings: list[str] = []
    if request.bars not in PREFERRED_BARS:
        warnings.append(
            f"{request.bars} bars is unusual; loops of 8/16/32 are easier to arrange."
        )
    if not 90 <= request.bpm <= 160:
        warnings.append(f"{request.bpm} BPM is outside the typical 90-160 range.")
    if not request.style_targets:
        warnings.append("No style targets given; defaulting to warm melodic techno.")
    return warnings


def passes_quality_gate(score: SeionScore, gate: float = QUALITY_GATE) -> bool:
    return score.overall >= gate
