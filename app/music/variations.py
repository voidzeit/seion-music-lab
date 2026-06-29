"""Deterministic variation operations on a MusicalIdea.

Sprint 2. A :class:`VariationSpec` is a structured, MIDI-achievable description
of *how* to change an idea ("darker", "simpler arp", "more drive"). The
:func:`apply_variation` function takes a parent idea and returns a NEW idea (a
deep copy) with the ops applied, plus a list of human-readable change notes that
feed the explanation and the version graph.

Everything here is pure and deterministic — no randomness, no I/O — so a
variation is reproducible and unit-testable.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.music.constants import BEATS_PER_BAR
from app.music.notes import midi_to_note_name
from app.schemas import MusicalIdea, NoteEvent, Track


@dataclass
class VariationSpec:
    """A structured, deterministic transform of an idea."""

    raw: str = ""

    # Register / brightness.
    arp_octave_shift: int = 0          # -1 darker, +1 brighter
    harmony_thin_top: bool = False     # drop the brightest chord tone

    # Density.
    simpler_arp: bool = False          # keep on-beat arp notes only (more hypnotic)
    arp_keep_ratio: float = 1.0        # 0<r<=1 keeps a fraction of arp notes
    bass_double: bool = False          # add downbeat roots (more drive)
    thin_hats: bool = False            # drop closed hats (more space)

    # Dynamics.
    velocity_scale: float = 1.0
    energy_shift: float = 0.0

    # Emotional hint so the re-score rewards the requested direction.
    add_emotions: list[str] = field(default_factory=list)

    # Human summary of each op (for the decision log / compare view).
    labels: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (
            self.arp_octave_shift
            or self.harmony_thin_top
            or self.simpler_arp
            or self.arp_keep_ratio < 1.0
            or self.bass_double
            or self.thin_hats
            or self.velocity_scale != 1.0
            or abs(self.energy_shift) > 1e-9
        )


def _clamp_vel(v: int) -> int:
    return max(1, min(127, v))


def _clamp_midi(m: int) -> int:
    return max(0, min(127, m))


def _scale_velocity(track: Track, scale: float) -> None:
    if scale == 1.0:
        return
    for note in track.notes:
        note.velocity = _clamp_vel(round(note.velocity * scale))
    for ev in track.drum_events:
        ev.velocity = _clamp_vel(round(ev.velocity * scale))


def _shift_arp_octave(arp: Track, shift: int) -> None:
    if shift == 0:
        return
    for note in arp.notes:
        note.midi = _clamp_midi(note.midi + 12 * shift)
        note.pitch = midi_to_note_name(note.midi)


def _thin_harmony_top(harmony: Track) -> None:
    """Drop the highest note of every chord (group by start beat)."""
    by_start: dict[float, list[NoteEvent]] = defaultdict(list)
    for note in harmony.notes:
        by_start[round(note.start_beat, 3)].append(note)
    keep: list[NoteEvent] = []
    for group in by_start.values():
        if len(group) <= 2:
            keep.extend(group)
            continue
        highest = max(group, key=lambda n: n.midi)
        keep.extend(n for n in group if n is not highest)
    keep.sort(key=lambda n: (n.start_beat, n.midi))
    harmony.notes = keep


def _simplify_arp(arp: Track) -> None:
    """Keep only on-beat arp notes and lengthen them: fewer, more hypnotic."""
    kept: list[NoteEvent] = []
    for note in arp.notes:
        if abs(note.start_beat - round(note.start_beat)) < 1e-6:
            note.duration_beats = max(note.duration_beats, 0.9)
            kept.append(note)
    if kept:
        arp.notes = kept


def _keep_arp_ratio(arp: Track, ratio: float) -> None:
    """Deterministically thin the arp by keeping 1 of every N notes."""
    if ratio >= 1.0 or not arp.notes:
        return
    step = max(2, round(1.0 / ratio))
    arp.notes = [n for i, n in enumerate(arp.notes) if i % step == 0]


def _double_bass(bass: Track, bars: int, beats_per_bar: int = BEATS_PER_BAR) -> None:
    """Add a root note on each downbeat to push the groove harder."""
    if not bass.notes:
        return
    # Root per bar is the lowest note that starts in that bar.
    root_by_bar: dict[int, NoteEvent] = {}
    for note in bass.notes:
        bar = int(note.start_beat // beats_per_bar)
        if bar not in root_by_bar or note.midi < root_by_bar[bar].midi:
            root_by_bar[bar] = note
    existing = {(round(n.start_beat, 3)) for n in bass.notes}
    additions: list[NoteEvent] = []
    for bar in range(bars):
        ref = root_by_bar.get(bar % len(root_by_bar)) if root_by_bar else None
        if ref is None:
            continue
        for beat in range(beats_per_bar):
            start = float(bar * beats_per_bar + beat)
            if round(start, 3) in existing:
                continue
            additions.append(
                NoteEvent(
                    pitch=ref.pitch,
                    midi=ref.midi,
                    start_beat=start,
                    duration_beats=0.22,
                    velocity=_clamp_vel(ref.velocity - 12),
                )
            )
    bass.notes = sorted(bass.notes + additions, key=lambda n: (n.start_beat, n.midi))


def _thin_hats(drums: Track) -> None:
    drums.drum_events = [
        e for e in drums.drum_events if e.instrument != "closed_hat" or _keep_hat(e)
    ]


def _keep_hat(event) -> bool:
    # Keep hats on the first off-beat of each bar only (every 4 beats-ish).
    return abs((event.start_beat % BEATS_PER_BAR) - 0.5) < 1e-6


def apply_variation(idea: MusicalIdea, spec: VariationSpec) -> tuple[MusicalIdea, list[str]]:
    """Return a deep-copied, transformed idea plus a list of change notes."""
    child = idea.model_copy(deep=True)
    changes: list[str] = []

    arp = child.track_by_role("arp")
    harmony = child.track_by_role("harmony") or child.track_by_role("pad")
    bass = child.track_by_role("bass")
    drums = next((t for t in child.tracks if t.is_drum), None)

    if spec.arp_octave_shift and arp:
        _shift_arp_octave(arp, spec.arp_octave_shift)
        direction = "down" if spec.arp_octave_shift < 0 else "up"
        changes.append(f"Moved the arp {abs(spec.arp_octave_shift)} octave(s) {direction}.")

    if spec.harmony_thin_top and harmony:
        _thin_harmony_top(harmony)
        changes.append("Dropped the brightest note of each chord for a darker voicing.")

    if spec.simpler_arp and arp:
        _simplify_arp(arp)
        changes.append("Simplified the arp to on-beat notes only (more hypnotic).")

    if spec.arp_keep_ratio < 1.0 and arp:
        _keep_arp_ratio(arp, spec.arp_keep_ratio)
        changes.append("Thinned the arp for more space.")

    if spec.bass_double and bass:
        _double_bass(bass, child.bars)
        changes.append("Added downbeat bass notes for more drive.")

    if spec.thin_hats and drums:
        _thin_hats(drums)
        changes.append("Thinned the closed hats to open up the groove.")

    if spec.velocity_scale != 1.0:
        for track in child.tracks:
            _scale_velocity(track, spec.velocity_scale)
        louder = "louder" if spec.velocity_scale > 1.0 else "softer"
        changes.append(f"Scaled velocities {louder}.")

    if abs(spec.energy_shift) > 1e-9:
        start = max(0.0, min(1.0, child.energy_target.start + spec.energy_shift))
        end = max(0.0, min(1.0, child.energy_target.end + spec.energy_shift))
        child.energy_target.start = round(start, 3)
        child.energy_target.end = round(end, 3)
        changes.append(f"Shifted the energy target by {spec.energy_shift:+.2f}.")

    if not changes:
        changes.append("No structural change requested; re-scored as-is.")

    return child, changes
