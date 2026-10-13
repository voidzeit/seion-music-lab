"""Write Surge XT patches (.fxp) into an Ardour session's saved plugin state.

Ardour stores a VST3 plugin's state as a base64 ``.vstpreset`` blob:
``'VST3' | version | 32-char class id | int64 list offset | data | 'List' chunk table``.
For Surge XT the single 'Comp' chunk is exactly the payload of a Surge
``.fxp`` file after its 60-byte FXP header (it starts with ``sub3``).
So picking a sound = swapping that payload, no GUI and no MIDI timing.

A "kit" is a JSON file ``{"patches": {"role": "path/to/patch.fxp"}, "gains_db": {...}}``;
roles are matched against track names ``<role>-1-t1``.

usage: python -m seion_ardour.surge_state <session.ardour> <kit.json>
"""

from __future__ import annotations

import base64
import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SURGE_XT_CLASS_ID = b"ABCDEF019182FAEB566D624153675854"
FXP_HEADER = 60


def fxp_payload(fxp: bytes) -> bytes:
    if fxp[:4] != b"CcnK" or fxp[FXP_HEADER:FXP_HEADER + 4] != b"sub3":
        raise ValueError("not a Surge .fxp patch")
    return fxp[FXP_HEADER:]


def build_vstpreset(header: bytes, payload: bytes) -> bytes:
    """header = the first 40 bytes ('VST3', version, class id) of an existing blob."""
    data_offset = 48
    return (
        header[:40]
        + struct.pack("<q", data_offset + len(payload))
        + payload
        + b"List"
        + struct.pack("<i", 1)
        + b"Comp"
        + struct.pack("<qq", data_offset, len(payload))
    )


def patch_name(fxp: bytes) -> str:
    return fxp[28:56].split(b"\0")[0].decode("latin-1")


def apply_kit(session_file: Path, kit: dict) -> dict[str, str]:
    """``kit`` is ``{"patches": {role: fxp}, ...}`` (a bare ``{role: fxp}`` also works)."""
    kit = kit.get("patches", kit)
    tree = ET.parse(session_file)
    applied: dict[str, str] = {}
    for route in tree.getroot().iter("Route"):
        m = re.match(r"^(.*?)-\d+-t\d+$", route.get("name", ""))
        role = m.group(1) if m else route.get("name")
        if role not in kit:
            continue
        for chunk in route.iter("chunk"):
            raw = base64.b64decode(chunk.text.strip())
            if raw[8:40] != SURGE_XT_CLASS_ID:
                continue
            fxp = Path(kit[role]).read_bytes()
            chunk.text = base64.b64encode(build_vstpreset(raw, fxp_payload(fxp))).decode("ascii")
            applied[role] = patch_name(fxp)
            break
    tree.write(session_file, encoding="UTF-8", xml_declaration=True)
    return applied



def resolve_kit_paths(kit: dict, root: Path | None = None) -> dict:
    """Resolve portable surge:// URIs and migrate machine-specific path references.

    SEION_SURGE_ROOT may specify the Surge XT data directory. Missing patches
    are errors: no audio preset is silently invented or substituted.
    """
    if not kit:
        return {}
    source = kit.get("patches", kit)
    if not isinstance(source, dict):
        raise ValueError("Surge kit patches must be a dictionary")
    base = root or Path(os.environ.get(
        "SEION_SURGE_ROOT",
        str(Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "Surge XT"),
    ))
    result = dict(kit)
    resolved = {}
    for role, declared in source.items():
        if not isinstance(declared, str) or not declared.strip():
            raise ValueError(f"Invalid patch reference for {role}")
        path = Path(declared)
        if path.is_file():
            candidate = path.resolve()
        else:
            text = declared.replace("\\", "/")
            if text.startswith("surge://"):
                relative = text.removeprefix("surge://")
            elif "/Surge XT/" in text:
                relative = text.split("/Surge XT/", 1)[1]
            elif not path.is_absolute() and ":" not in text:
                relative = text
            else:
                raise FileNotFoundError(f"Surge patch {role} not found: {declared}")
            candidate = (base / relative).resolve()
            if not candidate.is_relative_to(base.resolve()):
                raise ValueError(f"Unsafe Surge patch path for {role}: {declared}")
            if not candidate.is_file():
                raise FileNotFoundError(
                    f"Missing patch for {role}: {candidate}. Set SEION_SURGE_ROOT "
                    "to your local Surge XT directory or use a different --kit."
                )
        if candidate.suffix.lower() != ".fxp":
            raise ValueError(f"Surge patch for {role} must be .fxp: {candidate}")
        resolved[role] = str(candidate)
    if "patches" in kit:
        result["patches"] = resolved
    else:
        result = resolved
    return result

def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    session_file, kit_file = Path(argv[0]), Path(argv[1])
    kit = json.loads(kit_file.read_text(encoding="utf-8"))
    for role, name in apply_kit(session_file, kit).items():
        print(f"{role}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
