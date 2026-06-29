"""The SEION Music Lab generation pipeline.

Wires the agents and tools together in the canonical order:

    parse -> style context -> plan -> compose -> validate -> score ->
    critique -> (revise) -> export -> save -> explain

Fully deterministic and offline. No LLM calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app import tools
from app.agents import (
    arranger_agent,
    composer_agent,
    critic_agent,
    intake_agent,
    reference_agent,
    seion_agent,
    sound_design_agent,
    teacher_agent,
)
from app.logging_config import get_logger
from app.music.validation import validate_idea
from app.orchestrator import guardrails, planner
from app.orchestrator.state_machine import GenerationState, StateTracker
from app.schemas import EnergyTarget, MusicalIdea, SeionScore, UserRequest
from app.storage import ProjectStore

logger = get_logger(__name__)


@dataclass
class GenerationResult:
    idea: MusicalIdea
    score: SeionScore
    project_dir: Path
    midi_paths: dict[str, str]
    file_paths: dict[str, str]
    explanation_path: Path
    warnings: list[str] = field(default_factory=list)
    critique: list[dict] = field(default_factory=list)
    states: list[GenerationState] = field(default_factory=list)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:24] or "loop"


def _catalog_project(idea: MusicalIdea, score: SeionScore) -> None:
    """Record the project in the SQLite catalog (best-effort)."""
    try:
        from app.storage.sqlite_store import SqliteStore

        SqliteStore().upsert_project(
            {
                "id": idea.id,
                "parent_id": idea.parent_id,
                "title": idea.title,
                "bpm": idea.bpm,
                "key": idea.key,
                "bars": idea.bars,
                "version": idea.version,
                "overall": score.overall,
                "direction": idea.variation_request,
                "created_at": str(idea.created_at),
            }
        )
    except Exception:  # pragma: no cover - catalog is best-effort
        logger.debug("Project catalog update skipped for %s.", idea.id)


def _update_drop_folder(project_dir: Path) -> None:
    """Mirror the export into data/fl_drop for FL Studio (best-effort)."""
    try:
        from app.fl_bridge import update_drop_folder

        update_drop_folder(project_dir)
    except Exception:  # pragma: no cover - FL integration is optional
        logger.debug("Drop folder update skipped.")


def _new_project_id(request: UserRequest, store: ProjectStore) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"idea_{stamp}_{_slugify(request.title or 'loop')}"
    project_id = base
    counter = 2
    while (store.root / project_id).exists():
        project_id = f"{base}_{counter}"
        counter += 1
    return project_id


def run_generation(request: UserRequest, store: ProjectStore | None = None) -> GenerationResult:
    store = store or ProjectStore()
    tracker = StateTracker()

    # 1. Parse / normalise.
    tracker.enter(GenerationState.PARSE_REQUEST)
    request = intake_agent.normalize(request)
    warnings = guardrails.check_request(request)

    # 2. Style context.
    tracker.enter(GenerationState.LOAD_STYLE_CONTEXT)
    style_context = reference_agent.build_style_context(request.style_targets)

    # 3. Plan.
    tracker.enter(GenerationState.PLAN)
    plan = planner.create_plan(request, style_context)

    # 4. Compose. Build the arrangement first so the drums and filter automation
    #    can follow the sections.
    tracker.enter(GenerationState.COMPOSE)
    sections = arranger_agent.arrange(
        request, plan.energy_start, plan.energy_end, full=plan.use_full_arrangement
    )
    tracks, automation, decisions = composer_agent.compose(
        request, style_context, sections=sections, swing=plan.swing, humanize=plan.humanize
    )

    project_id = _new_project_id(request, store)
    idea = MusicalIdea(
        id=project_id,
        title=request.title or _slugify(request.title or "loop"),
        bpm=request.bpm,
        key=request.key,
        time_signature=request.time_signature,
        bars=request.bars,
        style_targets=request.style_targets,
        emotional_targets=request.emotional_targets,
        energy_target=EnergyTarget(start=plan.energy_start, end=plan.energy_end),
        sections=sections,
        tracks=tracks,
        automation=automation,
        decision_log=decisions,
    )

    # 5. Validate.
    tracker.enter(GenerationState.VALIDATE)
    warnings.extend(validate_idea(idea))

    # 6. Score.
    tracker.enter(GenerationState.SEION_SCORE)
    score = seion_agent.evaluate(idea, request, style_context)
    idea.seion_scores = score

    # 7. Critique (+ revision gate). Deterministic generation already clears the
    #    gate; the hook is here so an LLM composer can revise later.
    tracker.enter(GenerationState.CRITIQUE)
    critique = critic_agent.critique(idea, score)
    if not guardrails.passes_quality_gate(score):
        tracker.enter(GenerationState.REVISE)
        logger.info("Score %.2f below gate; revision deferred to LLM composer.", score.overall)

    sound_design = sound_design_agent.suggest(idea)

    # 8. Export.
    tracker.enter(GenerationState.EXPORT)
    project_dir = store.project_dir(project_id)
    midi_paths = tools.export_idea_midi(idea, project_dir)

    style_context_docs = {**style_context, "progression": request.progression}
    explanation = teacher_agent.explain(
        idea,
        style_context=style_context_docs,
        sound_design=sound_design,
        critique=critique,
        warnings=warnings,
    )
    explanation_path = tools.write_explanation_file(project_dir, explanation)

    idea.export_paths = {
        "midi": midi_paths,
        "explanation": str(explanation_path),
        "idea": str(project_dir / "idea.json"),
        "seion_score": str(project_dir / "seion_score.json"),
        # Stash the progression so a later variation can recover it.
        "progression": request.progression,
    }

    # 9. Save version (idea.json + seion_score.json, now complete).
    tracker.enter(GenerationState.SAVE_VERSION)
    file_paths = tools.save_project(idea, project_dir)
    file_paths.update({k: v for k, v in midi_paths.items()})
    file_paths["explanation"] = str(explanation_path)

    # Catalog the project (SQLite index + lineage) and refresh the FL drop
    # folder. Both are best-effort — generation must not fail if they do.
    _catalog_project(idea, score)
    _update_drop_folder(project_dir)

    tracker.enter(GenerationState.EXPLAIN)
    tracker.enter(GenerationState.DONE)

    return GenerationResult(
        idea=idea,
        score=score,
        project_dir=project_dir,
        midi_paths=midi_paths,
        file_paths=file_paths,
        explanation_path=explanation_path,
        warnings=warnings,
        critique=critique,
        states=tracker.history,
    )
