"""The ``seion-music`` command line interface (Typer + Rich)."""

from __future__ import annotations

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
    help="SEION Music Lab - generate editable, explained musical ideas for FL Studio.",
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


@app.command()
def version() -> None:
    """Print the SEION Music Lab version."""
    console.print(f"SEION Music Lab v{__version__}")


if __name__ == "__main__":
    app()
