"""The ``seion-music`` command line interface (Typer + Rich)."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app import __version__
from app.config import get_settings
from app.orchestrator import run_generation, run_variation
from app.schemas import Feedback, UserRequest
from app.tools import compare_versions, log_user_feedback

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="SEION Music Lab - compose, render experimental audio and review editable ideas.",
)
console = Console()


def _split(csv: str | None) -> list[str]:
    if not csv:
        return []
    return [part.strip() for part in csv.split(",") if part.strip()]


_COMPONENTS = (
    "coherence",
    "style_match",
    "emotional_clarity",
    "tension_curve",
    "editability",
    "novelty",
    "overall",
)


def _delta_table(before, after, deltas: dict[str, float], title: str) -> Table:
    table = Table(title=title, header_style="bold green")
    table.add_column("Component")
    table.add_column("Before", justify="right")
    table.add_column("After", justify="right")
    table.add_column("Delta", justify="right")
    for component in _COMPONENTS:
        b = getattr(before, component)
        a = getattr(after, component)
        d = deltas.get(component, a - b)
        arrow = "+" if d > 0 else ""
        colour = "green" if d > 0.0001 else ("red" if d < -0.0001 else "dim")
        label = f"[bold]{component}[/bold]" if component == "overall" else component
        table.add_row(label, f"{b:.2f}", f"{a:.2f}", f"[{colour}]{arrow}{d:.2f}[/{colour}]")
    return table


@app.command()
def generate(
    style: str = typer.Option("Computer Data,NTO", "--style", help="Comma-separated references."),
    key: str = typer.Option("A minor", "--key", help="Musical key, e.g. 'A minor'."),
    bpm: int = typer.Option(124, "--bpm", min=40, max=300),
    bars: int = typer.Option(16, "--bars", min=1, max=128),
    emotion: str = typer.Option(
        "warm,melancholic,hypnotic", "--emotion", help="Comma-separated emotions."
    ),
    progression: str = typer.Option(
        None, "--progression", help="Comma-separated chords (default Am7,Fmaj7,Cmaj7,G6)."
    ),
    title: str = typer.Option(None, "--title", help="Optional project title."),
) -> None:
    """Generate a loop: MIDI per track + full_loop.mid + idea.json + explanation.md."""
    get_settings().ensure_dirs()

    request = UserRequest(
        bpm=bpm,
        key=key,
        bars=bars,
        style_targets=_split(style),
        emotional_targets=_split(emotion),
        title=title,
    )
    if progression:
        request.progression = _split(progression)

    with console.status("[bold cyan]Composing, scoring and exporting...", spinner="dots"):
        result = run_generation(request)

    score = result.score
    console.print(
        Panel.fit(
            f"[bold]{result.idea.title}[/bold]\n"
            f"{result.idea.bpm} BPM | {result.idea.key} | {result.idea.bars} bars | "
            f"{', '.join(result.idea.style_targets)}",
            title="SEION Music Lab",
            border_style="cyan",
        )
    )

    console.print(f"\n[bold]Project:[/bold] {result.project_dir}")

    files = Table(title="Output files", show_lines=False, header_style="bold magenta")
    files.add_column("File")
    for label in ("idea.json", "seion_score.json", "explanation.md",
                  "chords.mid", "bass.mid", "arp.mid", "drums.mid", "full_loop.mid"):
        if (result.project_dir / label).exists():
            files.add_row(label)
    console.print(files)

    score_table = Table(title="SEION score", header_style="bold green")
    score_table.add_column("Component")
    score_table.add_column("Score", justify="right")
    for component in ("coherence", "style_match", "emotional_clarity",
                      "tension_curve", "editability", "novelty"):
        score_table.add_row(component, f"{getattr(score, component):.2f}")
    score_table.add_row("[bold]overall[/bold]", f"[bold]{score.overall:.2f}[/bold]")
    console.print(score_table)

    if result.warnings:
        console.print("\n[bold yellow]Notes:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  - {warning}")

    console.print(
        f"\n[dim]Read[/dim] {result.explanation_path} "
        f"[dim]for the full explanation and FL Studio import steps.[/dim]"
    )
    console.print(
        f"[dim]FL drop folder updated:[/dim] {get_settings().fl_drop_dir} "
        f"[dim](run `seion-music install-fl`, then use the Piano Roll script).[/dim]"
    )


@app.command()
def feedback(
    project_id: str = typer.Argument(..., help="The project id to attach feedback to."),
    rating: int = typer.Option(..., "--rating", min=0, max=10),
    comment: str = typer.Option("", "--comment", help="e.g. 'darker, less happy'."),
    liked: str = typer.Option("", "--liked", help="Comma-separated liked traits."),
    disliked: str = typer.Option("", "--disliked", help="Comma-separated disliked traits."),
) -> None:
    """Record listening feedback and update your preference model."""
    fb = Feedback(
        project_id=project_id,
        rating=rating,
        liked=_split(liked),
        disliked=_split(disliked),
        request=comment,
    )
    prefs = log_user_feedback(fb)
    console.print(f"[green]Saved feedback for[/green] {project_id} (rating {rating}/10).")
    console.print(f"[bold]Likes:[/bold] {', '.join(prefs.likes) or '-'}")
    console.print(f"[bold]Dislikes:[/bold] {', '.join(prefs.dislikes) or '-'}")
    console.print(f"[bold]Direction:[/bold] {prefs.current_direction}")


@app.command()
def vary(
    project_id: str = typer.Argument(..., help="The project id to vary."),
    direction: str = typer.Option(
        ..., "--direction", "-d", help="e.g. 'darker, simpler arp, more drive'."
    ),
) -> None:
    """Create a new version of a project in a given direction, with a score diff."""
    from app.storage import ProjectStore

    store = ProjectStore()
    with console.status("[bold cyan]Applying variation, scoring and exporting..."):
        result = run_variation(project_id, direction, store=store)

    console.print(
        Panel.fit(
            f"[bold]{result.child.title}[/bold]\n"
            f"from {result.parent.id}  |  direction: \"{direction}\"",
            title="SEION variation",
            border_style="cyan",
        )
    )
    console.print(f"\n[bold]New version:[/bold] {result.child.id}")
    console.print(f"[bold]Project:[/bold] {result.project_dir}")

    console.print("\n[bold]What changed:[/bold]")
    for change in result.changes:
        console.print(f"  - {change}")

    console.print()
    console.print(
        _delta_table(
            result.parent_score, result.child_score, result.deltas, "Score: before -> after"
        )
    )
    console.print(
        f"\n[dim]Read[/dim] {result.explanation_path} "
        f"[dim]for the full explanation.[/dim]"
    )


@app.command()
def compare(
    before_id: str = typer.Argument(..., help="Baseline project id."),
    after_id: str = typer.Argument(..., help="Project id to compare against it."),
) -> None:
    """Compare the SEION scores of two saved projects."""
    from app.storage import ProjectStore

    store = ProjectStore()
    before = store.load_idea(before_id).seion_scores
    after = store.load_idea(after_id).seion_scores
    if before is None or after is None:
        console.print("[red]One of the projects has no saved SEION score.[/red]")
        raise typer.Exit(code=1)

    deltas = compare_versions(before, after)
    console.print(_delta_table(before, after, deltas, f"{before_id}  ->  {after_id}"))


@app.command(name="list")
def list_projects() -> None:
    """List saved projects."""
    from app.storage import ProjectStore

    projects = ProjectStore().list_projects()
    if not projects:
        console.print("[dim]No projects yet. Run `seion-music generate`.[/dim]")
        return
    table = Table(title="Projects", header_style="bold magenta")
    table.add_column("ID", overflow="fold", no_wrap=False)
    table.add_column("Ver", justify="right")
    table.add_column("Title")
    table.add_column("BPM", justify="right")
    table.add_column("Key")
    table.add_column("Score", justify="right")
    for project in projects:
        score = f"{project.overall_score:.2f}" if project.overall_score is not None else "-"
        ver = f"v{project.version}" + (" *" if project.parent_id else "")
        table.add_row(
            project.id, ver, project.title, str(project.bpm), project.key, score
        )
    console.print(table)
    console.print("[dim]* = variation (child of another version)[/dim]")


@app.command(name="install-fl")
def install_fl(
    dest: str = typer.Option(
        None,
        "--dest",
        help="FL Piano Roll scripts folder (else FL_PIANO_ROLL_SCRIPTS_DIR / default).",
    ),
) -> None:
    """Install the SEION Piano Roll scripts into FL Studio."""
    from app.exceptions import ConfigError
    from app.fl_bridge import install_piano_roll_scripts

    try:
        installed = install_piano_roll_scripts(dest)
    except ConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        console.print(
            "[dim]Tip: pass --dest \"<FL>/Settings/Piano roll scripts\" or set "
            "FL_PIANO_ROLL_SCRIPTS_DIR in your .env.[/dim]"
        )
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Installed {len(installed)} Piano Roll script(s):[/green]")
    for path in installed:
        console.print(f"  - {path.name}")
    console.print(
        "\n[dim]In FL: Piano Roll > hamburger menu > Scripting > pick a SEION "
        "script. Run `seion-music generate` first so latest_idea.json exists.[/dim]"
    )



review_app = typer.Typer(help="Human audition and approval of A/B/C previews.")
app.add_typer(review_app, name="review")


@app.command(name="prototype")
def prototype(
    out: Path = typer.Option(..., "--out", help="New Project 001 MIDI output folder."),
    seed: int = typer.Option(1001, "--seed"),
) -> None:
    """Generate three original editable MIDI experiments."""
    from app.music.prototype_lab import build_experiments

    result = build_experiments(out, seed=seed)
    console.print(f"[green]Generated {len(result['experiments'])} A/B/C prototypes:[/green] {out}")
    console.print("[dim]Symbolic MIDI only; listening required.[/dim]")


@app.command(name="preview")
def preview(
    bundle: Path = typer.Option(..., "--bundle"),
    out: Path = typer.Option(..., "--out"),
    mode: str = typer.Option("all", "--mode"),
) -> None:
    """Synthesize independent previews with the optional NumPy audio engine."""
    from app.audio.preview_synth import MODES, render_mode

    if mode not in (*MODES, "all"):
        raise typer.BadParameter(f"Expected all or one of {MODES}", param_hint="--mode")
    for current in (MODES if mode == "all" else (mode,)):
        report = render_mode(bundle, out / current, current)
        console.print(f"[green]{current}:[/green] {out / current / 'preview.wav'}")
        console.print(f"[dim]{report['quality_status']} — listen before approval[/dim]")


@review_app.command(name="init")
def review_init(root: Path = typer.Argument(...)) -> None:
    """Create a fresh review bound to verified WAV hashes."""
    from app.audio.listening_gate import init_review

    init_review(root)
    console.print(f"[green]Review initialized:[/green] {root / 'listening_review.json'}")


@review_app.command(name="rate")
def review_rate(
    root: Path = typer.Argument(...),
    mode: str = typer.Argument(...),
    groove: int = typer.Option(..., "--groove", min=1, max=5),
    low_end: int = typer.Option(..., "--low-end", min=1, max=5),
    hook: int = typer.Option(..., "--hook", min=1, max=5),
    timbre: int = typer.Option(..., "--timbre", min=1, max=5),
    notes: str = typer.Option(..., "--notes"),
) -> None:
    """Record detailed listening notes and ratings."""
    from app.audio.listening_gate import rate

    state = rate(root, mode, {"groove": groove, "low_end": low_end,
                             "hook": hook, "timbre": timbre}, notes)
    console.print(f"[green]Saved {mode} review:[/green] {state['decision']}")


@review_app.command(name="approve")
def review_approve(
    root: Path = typer.Argument(...),
    mode: str = typer.Argument(...),
    reason: str = typer.Option(..., "--reason"),
    heard_all: bool = typer.Option(False, "--heard-all"),
) -> None:
    """Explicitly approve a variant for 32-bar development, not for release."""
    from app.audio.listening_gate import approve

    state = approve(root, mode, reason, heard_all=heard_all)
    console.print(f"[green]Approved for development:[/green] {state['approval']['mode']}")


@review_app.command(name="status")
def review_status(root: Path = typer.Argument(...)) -> None:
    """Show the recorded A/B/C listening state."""
    from app.audio.listening_gate import load_review

    state = load_review(root)
    console.print(f"Status: {state['decision']}")
    for mode, entry in state["variants"].items():
        console.print(f"  {mode}: {'rated' if entry['rating'] else 'unrated'}")




@app.command(name="analyze-wav")
def analyze_wav_command(
    audio: Path = typer.Argument(..., help="PCM WAV render or stem to inspect."),
    out: Path = typer.Option(..., "--out", help="New JSON report path."),
    bpm: float | None = typer.Option(None, "--bpm"),
) -> None:
    """Measure technical audio features, not mastering quality or artistic merit."""
    import json

    from app.audio.audio_analysis import analyze_wav

    if out.exists():
        raise typer.BadParameter("Output already exists; refusing to overwrite")
    result = analyze_wav(audio, bpm=bpm)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    console.print(f"[green]Signal-analysis evidence:[/green] {out}")


@app.command(name="compare-audio")
def compare_audio_command(
    root: Path = typer.Argument(..., help="A/B/C preview folder."),
    out: Path = typer.Option(..., "--out", help="New JSON comparison path."),
) -> None:
    """Compare A/B/C WAV statistics without declaring a creative winner."""
    from app.audio.audio_analysis import analyze_prototypes

    analyze_prototypes(root, out=out)
    console.print(f"[green]Technical A/B/C comparison:[/green] {out}")
    console.print("[dim]Human listening is still required.[/dim]")

@app.command()
def version() -> None:
    """Print the SEION Music Lab version."""
    console.print(f"SEION Music Lab v{__version__}")


if __name__ == "__main__":
    app()
