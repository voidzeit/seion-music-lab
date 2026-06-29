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
    notes: list[str] = field(default_factory=list)


def create_plan(request: UserRequest, style_context: dict) -> GenerationPlan:
    plan = GenerationPlan()
    plan.add_filter_automation = bool(style_context.get("wants_filter_automation", True))

    # Energy target leans on the requested emotions (warm/hypnotic = gentle rise).
    emotions = {e.lower() for e in request.emotional_targets}
    if "energetic" in emotions or "euphoric" in emotions:
        plan.energy_start, plan.energy_end = 0.4, 0.85
    elif "calm" in emotions or "ambient" in emotions:
        plan.energy_start, plan.energy_end = 0.2, 0.45

    plan.notes.append(
        f"Plan: {', '.join(plan.layers)} over {request.bars} bars; "
        f"energy {plan.energy_start}->{plan.energy_end}; "
        f"filter automation={'on' if plan.add_filter_automation else 'off'}."
    )
    return plan
