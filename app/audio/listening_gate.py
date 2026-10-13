"""Human audition gate for the three experimental Project 001 WAV previews.

Technical tests do not grant creative approval. All three variations must be
rated from actual listening before one is selected for 32-bar development.

    python -m app.audio.listening_gate init <preview-root>
    python -m app.audio.listening_gate rate <preview-root> groove --groove 4 --low-end 4 --hook 3 --timbre 4 --notes "..."
    python -m app.audio.listening_gate approve <preview-root> groove --reason "..." --heard-all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

MODES = ("groove", "trance_bounce", "hardcore_hybrid")
DIMENSIONS = ("groove", "low_end", "hook", "timbre")
REVIEW_FILE = "listening_review.json"


def _utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, data: dict) -> None:
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _review_path(root: Path) -> Path:
    return root / REVIEW_FILE


def load_review(root: Path) -> dict:
    return json.loads(_review_path(root).read_text(encoding="utf-8"))


def init_review(root: Path) -> dict:
    """Index actual WAV preview hashes; refuse to reset existing reviews."""
    if _review_path(root).exists():
        raise FileExistsError(f"Existing human reviews preserved: {_review_path(root)}")
    versions = {}
    for mode in MODES:
        report_path = root / mode / "preview_report.json"
        if not report_path.is_file():
            raise FileNotFoundError(f"render {mode} first: {report_path}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        wav = root / mode / "preview.wav"
        expected_hash = report["files"]["master"]["sha256"]
        if not wav.is_file() or _sha(wav) != expected_hash:
            raise ValueError(f"Missing or changed audio for {mode}")
        if report.get("mode") != mode or report.get("quality_status") != "synthetic_preview_unreviewed":
            raise ValueError(f"Unexpected preview provenance for {mode}")
        versions[mode] = {
            "file": str(wav.relative_to(root)).replace("\\", "/"),
            "sha256": expected_hash,
            "rating": None,
        }
    data = {
        "schema_version": "1.0",
        "decision": "unreviewed",
        "created_at": _utc(),
        "creative_gate": "needs_human_listening",
        "variants": versions,
        "history": [],
        "approval": None,
    }
    _atomic_json(_review_path(root), data)
    return data


def _verify_audio(root: Path, state: dict) -> None:
    for mode, entry in state["variants"].items():
        audio = root / entry["file"]
        if not audio.is_file() or _sha(audio) != entry["sha256"]:
            raise ValueError(f"Original audition audio has changed: {mode}")


def rate(root: Path, mode: str, scores: dict[str, int], notes: str) -> dict:
    if mode not in MODES:
        raise ValueError(f"unknown variant: {mode}")
    if not notes.strip():
        raise ValueError("listening notes are required")
    if set(scores) != set(DIMENSIONS) or any(
        not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > 5
        for value in scores.values()
    ):
        raise ValueError("scores must be integer 1-5 for groove, low_end, hook and timbre")
    state = load_review(root)
    if state["approval"] is not None:
        raise ValueError("approved review is immutable; start a new listening round")
    _verify_audio(root, state)
    review = {"scores": scores, "notes": notes.strip(), "listened_at": _utc()}
    state["variants"][mode]["rating"] = review
    state["history"].append({"action": "rate", "mode": mode, **review})
    state["decision"] = "under_review"
    _atomic_json(_review_path(root), state)
    return state


def approve(root: Path, mode: str, reason: str, heard_all: bool = False) -> dict:
    """Explicit HUMAN approval for development only, not distribution/mastering."""
    if mode not in MODES:
        raise ValueError(f"unknown variant: {mode}")
    if not heard_all:
        raise ValueError("human must explicitly attest to hearing all three WAV previews")
    if len(reason.strip()) < 15:
        raise ValueError("selection reason must contain at least 15 characters")
    state = load_review(root)
    if state["approval"] is not None:
        raise ValueError("review already approved and immutable")
    _verify_audio(root, state)
    if any(state["variants"][key]["rating"] is None for key in MODES):
        raise ValueError("all three variants must have listening ratings before approval")
    selection = {
        "mode": mode,
        "reason": reason.strip(),
        "heard_all": True,
        "decided_at": _utc(),
        "gate": "approved_for_32bar_development_only",
    }
    state["approval"] = selection
    state["decision"] = "approved_for_32bar_development_only"
    state["history"].append({"action": "approve", **selection})
    _atomic_json(_review_path(root), state)
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    init = subs.add_parser("init")
    init.add_argument("root", type=Path)
    review = subs.add_parser("rate")
    review.add_argument("root", type=Path)
    review.add_argument("mode", choices=MODES)
    for name in DIMENSIONS:
        review.add_argument(f"--{name.replace('_', '-')}", type=int, required=True)
    review.add_argument("--notes", required=True)
    approval = subs.add_parser("approve")
    approval.add_argument("root", type=Path)
    approval.add_argument("mode", choices=MODES)
    approval.add_argument("--reason", required=True)
    approval.add_argument("--heard-all", action="store_true")
    status = subs.add_parser("status")
    status.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    if args.command == "init":
        state = init_review(args.root)
    elif args.command == "rate":
        scores = {name: getattr(args, name) for name in DIMENSIONS}
        state = rate(args.root, args.mode, scores, args.notes)
    elif args.command == "approve":
        state = approve(args.root, args.mode, args.reason, heard_all=args.heard_all)
    else:
        state = load_review(args.root)
    print(json.dumps({
        "decision": state["decision"],
        "rated": [mode for mode, entry in state["variants"].items() if entry["rating"] is not None],
        "approval": state["approval"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
