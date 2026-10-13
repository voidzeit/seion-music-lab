"""Render a SEION version through Ardour headless.

usage:
  python -m seion_ardour.cli <version_dir> [--bars 65-96] [--name drop_1] [--seed seion_seed_v2] [--no-stems]

Reads <version_dir>/idea.json for midi_files, renders master (+ stems) into
<version_dir>/renders/<name>/ and writes render_report.json there.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from seion_ardour.midi_job import BarRange, read_notes, slice_notes, split_role, write_job
from seion_ardour.runner import (
    CONNECTOR_DIR,
    ArdourInstall,
    prepare_session,
    run_render,
    seed_manifest,
    workspace,
)
from seion_ardour.surge_state import apply_kit
from seion_ardour.validation import check_wav, note_coverage


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version_dir", type=Path)
    ap.add_argument("--bars", type=BarRange.parse, help="1-based inclusive range, e.g. 65-96")
    ap.add_argument("--name", default="full")
    ap.add_argument("--seed", default="seion_seed", help="seed session under templates/")
    ap.add_argument("--kit", type=Path, help="Surge XT kit JSON (default: the seed's kit)")
    ap.add_argument("--no-stems", action="store_true")
    ap.add_argument(
        "--prototype",
        choices=("groove", "trance_bounce", "hardcore_hybrid"),
        help="Render one Project 001 v002 MIDI prototype from prototype_manifest.json",
    )
    args = ap.parse_args(argv)

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args.name):
        ap.error("--name must be a safe identifier: letters, digits, _ and -")
    version_dir = args.version_dir.resolve()
    if args.prototype:
        manifest = json.loads((version_dir / "prototype_manifest.json").read_text(encoding="utf-8"))
        exp = manifest["experiments"][args.prototype]
        bpm = float(manifest["bpm"])
        total_bars = int(manifest["bars"])
        beats_per_bar = 4
        tracks = {}
        for role, midi_rel in exp["midi_files"].items():
            notes, file_bpm = read_notes(version_dir / midi_rel)
            if file_bpm and abs(file_bpm - bpm) > 0.01:
                raise SystemExit(f"{role}: MIDI tempo {file_bpm} != manifest bpm {bpm}")
            tracks[role] = notes
        # The seed uses a GM drum track; the extra percussion remains editable
        # in the prototype source, but shares drums during this render.
        if "percussion" in tracks:
            tracks["drums"] = sorted(tracks.get("drums", []) + tracks.pop("percussion"))
        seed_name = "seion_seed_v2" if args.seed == "seion_seed" else args.seed
    else:
        idea = json.loads((version_dir / "idea.json").read_text(encoding="utf-8"))
        beats_per_bar = int(idea.get("time_signature", "4/4").split("/")[0])
        tracks, bpm = {}, float(idea["bpm"])
        total_bars = int(idea["bars"])
        for role in idea["track_roles"]:
            notes, file_bpm = read_notes(version_dir / idea["midi_files"][role])
            if file_bpm and abs(file_bpm - bpm) > 0.01:
                raise SystemExit(f"{role}: MIDI tempo {file_bpm} != idea bpm {bpm}")
            tracks[role] = notes
        seed_name = args.seed

    if args.bars:
        start, end = args.bars.beats(beats_per_bar)
    else:
        start, end = 0.0, float(total_bars * beats_per_bar)
    tracks = {role: slice_notes(notes, start, end) for role, notes in tracks.items()}
    manifest = seed_manifest(seed_name)
    for source, target in manifest.get("merge", {}).items():
        if source in tracks:
            tracks[target] = sorted(tracks.get(target, []) + tracks.pop(source))
    for new_role, rule in manifest.get("split", {}).items():
        if new_role not in tracks or not tracks[new_role]:
            tracks = split_role(tracks, new_role, rule["from"], set(rule["notes"]))

    kit_file = args.kit or (CONNECTOR_DIR / manifest["kit"] if "kit" in manifest else None)
    kit = json.loads(Path(kit_file).read_text(encoding="utf-8")) if kit_file else {}

    # v002/generated is an input bundle, not the song version root.
    version_root = version_dir.parent if args.prototype else version_dir
    out_dir = version_root / "renders" / args.name
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"render already exists, refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    job = write_job(
        out_dir / "job.lua",
        tracks=tracks,
        bpm=bpm,
        length_beats=end - start,
        export_dir=out_dir,
        stems=not args.no_stems,
        gains_db=kit.get("gains_db"),
        master_gain_db=kit.get("master_gain_db", 0.0),
    )

    install = ArdourInstall.locate()
    project_slug = version_root.parents[1].name
    version = version_root.name
    session = prepare_session(workspace() / project_slug / f"{version}_{args.name}", seed_name)
    kit_applied = apply_kit(next(session.glob("*.ardour")), kit) if kit else {}
    if kit:
        wanted = set(kit.get("patches", kit))
        missing = wanted - set(kit_applied)
        if missing:
            raise SystemExit(f"kit patches could not be assigned to session tracks: {sorted(missing)}")
    log = run_render(install, session, job)

    music_seconds = (end - start) * 60.0 / bpm
    reports = []
    for p in sorted(out_dir.glob("*.wav")):
        r = check_wav(p).as_dict()
        role = p.stem.removeprefix("stem_")
        if role in tracks:
            # A stem must sound in at least half of the windows where its MIDI has notes;
            # catches patches that only emit a start-up burst and then stay silent.
            expected = note_coverage(tracks[role], bpm, music_seconds)
            r["expected_active_ratio"] = round(expected, 3)
            if r["active_ratio"] < 0.5 * expected:
                r["passed"] = False
                r["failure"] = "stem mostly silent where its MIDI has notes"
        reports.append(r)
    report = {
        "rendered_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "backend": "ardour-headless",
        "backend_status": "experimental",
        "ardour_home": str(install.home),
        "ardour_session": str(session),
        "seed": seed_name,
        "kit": str(kit_file) if kit_file else None,
        "patches": kit_applied,
        "bars": [args.bars.first, args.bars.last] if args.bars else [1, idea["bars"]],
        "bpm": bpm,
        "note_counts": {role: len(n) for role, n in tracks.items()},
        "files": reports,
        "passed": bool(reports) and all(r["passed"] for r in reports),
        "ardour_log_tail": log[-1500:],
    }
    (out_dir / "render_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for r in reports:
        status = "PASS" if r["passed"] else "FAIL"
        print(
            f"{status} {r['file']}: {r['duration_seconds']}s peak {r['peak_dbfs']} dBFS "
            f"rms {r['rms_dbfs']} dBFS active {r['active_ratio']}"
            + (f" (expected {r['expected_active_ratio']})" if "expected_active_ratio" in r else "")
            + (f" -> {r['failure']}" if "failure" in r else "")
        )
    print(f"report: {out_dir / 'render_report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
