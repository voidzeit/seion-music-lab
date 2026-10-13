"""Run ardour9-lua headlessly against a copy of the seed session."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

CONNECTOR_DIR = Path(__file__).resolve().parents[2]
LUA_DIR = CONNECTOR_DIR / "lua"
DEFAULT_ARDOUR_HOME = Path(r"D:\Program Files\Ardour9")
# Where per-render Ardour sessions live, so they can be opened in the GUI later.
DEFAULT_WORKSPACE = Path(r"D:\Documents\Music-Ardour")


def workspace() -> Path:
    return Path(os.environ.get("SEION_ARDOUR_WORKSPACE", DEFAULT_WORKSPACE))


def session_name(session_dir: Path) -> str:
    """Ardour names the state file after the session; take it from disk."""
    states = list(session_dir.glob("*.ardour"))
    if len(states) != 1:
        raise ArdourError(f"expected one .ardour file in {session_dir}, found {len(states)}")
    return states[0].stem


class ArdourError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArdourInstall:
    home: Path
    major: int = 9

    @classmethod
    def locate(cls) -> ArdourInstall:
        home = Path(os.environ.get("SEION_ARDOUR_HOME", DEFAULT_ARDOUR_HOME))
        inst = cls(home)
        if not inst.lua_exe.exists():
            raise ArdourError(f"ardour{inst.major}-lua not found under {home} (set SEION_ARDOUR_HOME)")
        return inst

    @property
    def lua_exe(self) -> Path:
        return self.home / "bin" / f"ardour{self.major}-lua.exe"

    def env(self) -> dict[str, str]:
        # Without these the Windows session utils cannot find backends/plugins.
        share = self.home / "share" / f"ardour{self.major}"
        lib = self.home / "lib" / f"ardour{self.major}"
        return {
            **os.environ,
            "ARDOUR_DATA_PATH": str(share),
            "ARDOUR_CONFIG_PATH": str(share),
            "ARDOUR_DLL_PATH": str(lib),
            "VAMP_PATH": str(lib / "vamp"),
        }


def seed_dir(seed: str = "seion_seed") -> Path:
    path = CONNECTOR_DIR / "templates" / seed
    if not path.is_dir():
        raise ArdourError(f"seed session missing at {path}; build it with lua/build_seed_session.lua")
    session_name(path)
    return path


def seed_manifest(seed: str = "seion_seed") -> dict:
    """Optional ``seion_seed.json`` next to the seed: e.g. which notes go to a split kick track."""
    path = seed_dir(seed) / "seion_seed.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def prepare_session(target: Path, seed: str = "seion_seed") -> Path:
    """Copy the seed session to ``target`` (replaced on every render)."""
    source = seed_dir(seed)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("*.bak", "*.pending", "*.history", "export", "seion_seed.json"),
    )
    return target


def run_render(install: ArdourInstall, session_dir: Path, job_path: Path, timeout: int = 1800) -> str:
    name = session_name(session_dir)
    cmd = [str(install.lua_exe), str(LUA_DIR / "render_job.lua"), str(session_dir), name, str(job_path)]
    proc = subprocess.run(cmd, env=install.env(), capture_output=True, text=True, timeout=timeout)
    output = "\n".join(
        line for line in (proc.stdout + proc.stderr).splitlines() if "lilv_world" not in line and line.strip()
    )
    if proc.returncode != 0:
        # ardour9-lua on Windows sometimes crashes while tearing down (after
        # close_session). Accept that only if render_job.lua logged "done".
        render_log = Path(_job_export_dir(job_path)) / "render.log"
        lines = render_log.read_text(encoding="utf-8").split() if render_log.exists() else []
        if not lines or lines[-1] != "done":
            raise ArdourError(f"ardour-lua exited {proc.returncode}:\n{output[-2000:]}")
        output += f"\n[seion] ardour-lua exited {proc.returncode} after completing the render (teardown crash)"
    return output


def _job_export_dir(job_path: Path) -> str:
    text = job_path.read_text(encoding="utf-8")
    start = text.index("export_dir = [[") + len("export_dir = [[")
    return text[start:text.index("]]", start)]
