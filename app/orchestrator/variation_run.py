"""The variation pipeline (Sprint 2).

Load a saved idea, apply a deterministic directed variation ("darker, simpler
arp"), re-score it, and save it as a *child* version with full lineage. Returns
the before/after scores and per-component deltas so the CLI can show what
changed and why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app import tools
from app.agents import (
    critic_agent,
    sound_design_agent,
    teacher_agent,
    variation_agent,
)
from app.logging_config import get_logger
from app.music.variations import VariationSpec, apply_variation
from app.schemas import DecisionLogEntry, MusicalIdea, SeionScore, UserRequest
from app.seion import score_idea
from app.storage import ProjectStore
from app.storage.sqlite_store import SqliteStore

logger = get_logger(__name__)


@dataclass
class VariationResult:
    parent: MusicalIdea
    child: MusicalIdea
    parent_score: SeionScore
    child_score: SeionScore
    deltas: dict[str, float]
    spec: VariationSpec
    changes: list[str]
    project_dir: Path
    midi_paths: dict[str, str] = field(default_factory=dict)
    file_paths: dict[str, str] = field(default_factory=dict)
    explanation_path: Path | None = None


def _request_from_idea(idea: MusicalIdea, extra_emotions: list[str]) -> UserRequest:
    emotions = list(idea.emotional_targets)
    for emo in extra_emotions:
        if emo not in emotions:
            emotions.append(emo)
    progression = _infer_progression(idea)
    return UserRequest(
        bpm=idea.bpm,
        key=idea.key,
        bars=idea.bars,
        style_targets=list(idea.style_targets),
        emotional_targets=emotions,
        progression=progression,
        title=idea.title,
    )


def _infer_progression(idea: MusicalIdea) -> list[str]:
    """Best-effort: reuse the request default unless the idea carried one."""
    stored = idea.export_paths.get("progression") if idea.export_paths else None
    if isinstance(stored, list) and stored:
        return stored
    return ["Am7", "Fmaj7", "Cmaj7", "G6"]


def _child_id(parent_id: str, version: int, store: ProjectStore) -> str:
    base = f"{parent_id}_v{version}"
    candidate = base
    counter = 2
    while (store.root / candidate).exists():
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def run_variation(
    parent_id: str,
    direction: str,
    store: ProjectStore | None = None,
) -> VariationResult:
    store = store or ProjectStore()
    parent = store.load_idea(parent_id)

    spec = variation_agent.parse_direction(direction)
    child, changes = apply_variation(parent, spec)

    # Lineage + identity.
    version = parent.version + 1
    child.id = _child_id(parent_id, version, store)
    child.parent_id = parent_id
    child.version = version
    child.variation_request = direction.strip()
    child.lineage = [*parent.lineage, parent_id]
    child.title = f"{parent.title}_v{version}"
    for emo in spec.add_emotions:
        if emo not in child.emotional_targets:
            child.emotional_targets.append(emo)

    # Record the variation as a decision so the explanation teaches it.
    child.decision_log.append(
        DecisionLogEntry(
            decision_id=f"v{version:03d}",
            agent="variation_agent",
            type="variation",
            decision=f'Variation from {parent_id}: "{direction.strip()}".',
            reason="; ".join(changes),
            references=spec.labels,
            expected_effect=", ".join(spec.add_emotions) or "directed change",
        )
    )

    # Re-score the child against a request that reflects the new direction.
    request = _request_from_idea(child, spec.add_emotions)
    style_context = {"artists": child.style_targets}
    child_score = score_idea(child, request, style_context)
    child.seion_scores = child_score

    parent_score = parent.seion_scores or score_idea(parent, request, style_context)
    deltas = tools.compare_versions(parent_score, child_score)

    # Export + explain + persist.
    project_dir = store.project_dir(child.id)
    midi_paths = tools.export_idea_midi(child, project_dir)

    sound_design = sound_design_agent.suggest(child)
    critique = critic_agent.critique(child, child_score)
    explanation = teacher_agent.explain(
        child,
        style_context={"progression": _infer_progression(child)},
        sound_design=sound_design,
        critique=critique,
        warnings=[f"Variation of {parent_id} (v{parent.version})."],
    )
    explanation_path = tools.write_explanation_file(project_dir, explanation)

    child.export_paths = {
        "midi": midi_paths,
        "explanation": str(explanation_path),
        "idea": str(project_dir / "idea.json"),
        "seion_score": str(project_dir / "seion_score.json"),
        "parent": parent_id,
    }
    file_paths = tools.save_project(child, project_dir)
    file_paths.update(midi_paths)
    file_paths["explanation"] = str(explanation_path)

    # Catalog both versions so the lineage is queryable.
    _catalog(parent, parent_score, direction="")
    _catalog(child, child_score, direction=direction.strip())

    # Keep the FL drop folder pointing at the newest idea.
    try:
        from app.fl_bridge import update_drop_folder

        update_drop_folder(project_dir)
    except Exception:  # pragma: no cover - FL integration is optional
        logger.debug("Drop folder update skipped.")

    return VariationResult(
        parent=parent,
        child=child,
        parent_score=parent_score,
        child_score=child_score,
        deltas=deltas,
        spec=spec,
        changes=changes,
        project_dir=project_dir,
        midi_paths=midi_paths,
        file_paths=file_paths,
        explanation_path=explanation_path,
    )


def _catalog(idea: MusicalIdea, score: SeionScore, direction: str) -> None:
    try:
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
                "direction": direction,
                "created_at": str(idea.created_at),
            }
        )
    except Exception:  # pragma: no cover - catalog is best-effort
        logger.debug("Project catalog update skipped for %s.", idea.id)
