"""Turn a UserRequest + style context into a concrete generation plan.

For the MVP the plan is straightforward (chords + bass + arp + drums, one loop
section). It is explicit so the orchestrator's intent is inspectable and so a
later LLM planner can produce the same shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import UserRequest


@dataclass
class GenerationPlan:
    layers: list[str] = field(default_factory=lambda: ["harmony", "bass", "arp", "drums"])
    energy_start: float = 0.25
    energy_end: float = 0.65
    add_filter_automation: bool = True
    # Sprint 3: lay out a full arrangement (intro/build/break/drop) when there is
    # room for it. A short request stays a single loop.
    use_full_arrangement: bool = True
    swing: float = 0.0
    humanize: bool = True
    notes: list[str] = field(default_factory=list)


def create_plan(request: UserRequest, style_context: dict) -> GenerationPlan:
    plan = GenerationPlan()
    plan.add_filter_automation = bool(style_context.get("wants_filter_automation", True))
    plan.use_full_arrangement = request.bars >= 8

    # Energy target leans on the requested emotions (warm/hypnotic = gentle rise).
    emotions = {e.lower() for e in request.emotional_targets}
    if "energetic" in emotions or "euphoric" in emotions:
        plan.energy_start, plan.energy_end = 0.4, 0.85
    elif "calm" in emotions or "ambient" in emotions:
        plan.energy_start, plan.energy_end = 0.2, 0.45

    # A touch of swing for warm-house feels; humanise velocities slightly.
    plan.swing = 0.08 if style_context.get("wants_four_on_floor", True) else 0.0

    plan.notes.append(
        f"Plan: {', '.join(plan.layers)} over {request.bars} bars; "
        f"energy {plan.energy_start}->{plan.energy_end}; "
        f"arrangement={'full' if plan.use_full_arrangement else 'loop'}; "
        f"filter automation={'on' if plan.add_filter_automation else 'off'}."
    )
    return plan
