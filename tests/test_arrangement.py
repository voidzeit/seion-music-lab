"""Sprint 3: song arrangement + section-aware drums + tension scoring."""

from __future__ import annotations

from app.music import build_song_sections, generate_drum_track
from app.music.arrangement import build_loop_section
from app.schemas import EnergyTarget, MusicalIdea
from app.seion.tension_curve import compute_tension_curve

PROG = ["Am7", "Fmaj7", "Cmaj7", "G6"]


def test_song_sections_cover_all_bars():
    sections = build_song_sections(16, 0.25, 0.65)
    assert len(sections) >= 4
    assert sum(s.length_bars for s in sections) == 16
    # Sections are contiguous and 1-indexed from bar 1.
    cursor = 1
    for sec in sections:
        assert sec.start_bar == cursor
        cursor += sec.length_bars


def test_song_sections_have_energy_curve():
    sections = build_song_sections(16, 0.25, 0.65)
    energies = [s.energy for s in sections]
    assert max(energies) - min(energies) > 0.2  # a real rise and fall
    names = {s.name for s in sections}
    assert "drop" in names and "intro" in names


def test_short_request_falls_back_to_loop():
    sections = build_song_sections(4, 0.25, 0.65)
    assert len(sections) == 1


def test_default_drums_unchanged():
    """The section-less default must stay byte-stable: 10 hits/bar * 16 bars."""
    drums = generate_drum_track(16)
    assert len(drums.drum_events) == 16 * 10
    assert all(e.midi for e in drums.drum_events)


def test_section_drums_hold_back_the_intro():
    sections = build_song_sections(16, 0.25, 0.65)
    drums = generate_drum_track(16, sections=sections)
    # Intro bars (mode "intro") carry no kick.
    intro = next(s for s in sections if s.name == "intro")
    intro_kicks = [
        e
        for e in drums.drum_events
        if e.instrument == "kick"
        and (intro.start_bar - 1) * 4 <= e.start_beat < (intro.start_bar - 1 + intro.length_bars) * 4
    ]
    assert intro_kicks == []
    # But the track as a whole still has kicks (in build/main/drop).
    assert any(e.instrument == "kick" for e in drums.drum_events)


def _idea(sections, automation=None) -> MusicalIdea:
    return MusicalIdea(
        id="t",
        title="t",
        bpm=124,
        key="A minor",
        bars=16,
        sections=sections,
        automation=automation or [],
        energy_target=EnergyTarget(start=0.25, end=0.65),
    )


def test_full_arrangement_beats_flat_loop_on_tension():
    flat = compute_tension_curve(_idea(build_loop_section(16)))[0]
    full = compute_tension_curve(_idea(build_song_sections(16, 0.25, 0.65)))[0]
    assert full > flat
    assert full > 0.65  # the whole point of Sprint 3
