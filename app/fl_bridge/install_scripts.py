"""Install the bundled Piano Roll scripts into FL Studio's scripts folder."""

from __future__ import annotations

import shutil
from pathlib import Path

from app.exceptions import ConfigError
from app.fl_bridge.paths import fl_piano_roll_scripts_dir

# Where the repo keeps its .pyscript sources.
_REPO_SCRIPTS = Path(__file__).resolve().parents[2] / "fl_scripts" / "piano_roll"


def install_piano_roll_scripts(dest: str | Path | None = None) -> list[Path]:
    """Copy ``fl_scripts/piano_roll/*.pyscript`` into FL's scripts directory.

    Returns the list of destination paths. Raises ConfigError if the FL scripts
    directory cannot be resolved (set FL_PIANO_ROLL_SCRIPTS_DIR in your .env).
    """
    target = Path(dest) if dest else fl_piano_roll_scripts_dir()
    if target is None:
        raise ConfigError(
            "Could not resolve FL Piano Roll scripts directory. "
            "Set FL_PIANO_ROLL_SCRIPTS_DIR in your environment."
        )
    target.mkdir(parents=True, exist_ok=True)

    installed: list[Path] = []
    for script in _REPO_SCRIPTS.glob("*.pyscript"):
        out = target / script.name
        shutil.copyfile(script, out)
        installed.append(out)
    return installed
