"""Drum generator: four-on-the-floor that can follow a song arrangement.

Called with just ``bars`` it produces the original steady warm-house kit (this
keeps the MVP behaviour and the MIDI tests stable). Pass ``sections`` and it
becomes arrangement-aware: it holds the kick back in the intro/break, drops a
fill at the end of the build/break, and opens up in the drop. Optional swing and
deterministic humanisation add feel without breaking reproducibility.
"""

from __future__ import annotations

from app.music.constants import BEATS_PER_BAR, GM_DRUMS
from app.music.groove import apply_swing, humanize_velocity
from app.music.rhythm import downbeats, offbeat_eighths, sixteenth_grid
from app.schemas import DrumEvent, MixerHint, Section, Track

# Section names this generator knows how to voice; anything else plays as "main".
_KNOWN_MODES = {"intro", "build", "main", "break", "drop", "outro"}


def _section_modes(sections: list[Section] | None, bars: int) -> list[dict] | None:
    """Per-bar {mode, start, end} map, or None to use the steady default."""
    if not sections:
        return None
    out: list[dict] = []
    for bar in range(bars):
        bar_no = bar + 1
        mode, is_start, is_end = "main", False, False
        for sec in sections:
            last = sec.start_bar + sec.length_bars - 1
            if sec.start_bar <= bar_no <= last:
                name = sec.name.lower()
                mode = name if name in _KNOWN_MODES else "main"
                is_start = bar_no == sec.start_bar
                is_end = bar_no == last
                break
        out.append({"mode": mode, "start": is_start, "end": is_end})
    return out


def _pos(bar_offset: int, pos_in_bar: float, swing: float) -> float:
    return float(bar_offset + apply_swing(pos_in_bar, swing))


def _vel(velocity: int, humanize: bool, seed: int) -> int:
    return humanize_velocity(velocity, 6 if humanize else 0, seed)


def _add(events, instrument, bar_offset, pos, dur, velocity, *, swing, humanize):
    seed = int(round((bar_offset + pos) * 100)) + GM_DRUMS[instrument]
    events.append(
        DrumEvent(
            instrument=instrument,
            midi=GM_DRUMS[instrument],
            start_beat=_pos(bar_offset, pos, swing),
            duration_beats=dur,
            velocity=_vel(velocity, humanize, seed),
        )
    )


def _bar_main(events, bar, bpb, swing, humanize, kv, cv, hv, *, drop=False):
    off = bar * bpb
    for beat in downbeats(bpb):
        _add(events, "kick", off, beat, 0.25, kv, swing=swing, humanize=humanize)
    for beat in (1, 3):
        _add(events, "clap", off, beat, 0.25, cv, swing=swing, humanize=humanize)
    offbeats = offbeat_eighths(bpb)
    last = offbeats[-1]
    open_bar = drop or (bar % 2 == 1)
    for pos in offbeats:
        is_open = open_bar and abs(pos - last) < 1e-6
        instrument = "open_hat" if is_open else "closed_hat"
        dur = 0.4 if is_open else 0.2
        _add(events, instrument, off, pos, dur, hv + (6 if is_open else 0),
             swing=swing, humanize=humanize)


def _bar_intro(events, bar, bpb, swing, humanize, hv):
    off = bar * bpb
    for pos in offbeat_eighths(bpb):
        _add(events, "closed_hat", off, pos, 0.2, hv - 10, swing=swing, humanize=humanize)


def _bar_build(events, bar, bpb, swing, humanize, kv, hv):
    off = bar * bpb
    for beat in downbeats(bpb):
        _add(events, "kick", off, beat, 0.25, kv - 6, swing=swing, humanize=humanize)
    for pos in offbeat_eighths(bpb):
        _add(events, "closed_hat", off, pos, 0.2, hv, swing=swing, humanize=humanize)


def _bar_break(events, bar, bpb, swing, humanize, cv, hv):
    off = bar * bpb
    for beat in (1, 3):
        _add(events, "clap", off, beat, 0.25, cv - 8, swing=swing, humanize=humanize)
    for pos in (offbeat_eighths(bpb)[0], offbeat_eighths(bpb)[2]):
        _add(events, "closed_hat", off, pos, 0.2, hv - 6, swing=swing, humanize=humanize)


def _bar_outro(events, bar, bpb, swing, humanize, kv, hv):
    off = bar * bpb
    for beat in (0, 2):
        _add(events, "kick", off, beat, 0.25, kv - 4, swing=swing, humanize=humanize)
    for pos in offbeat_eighths(bpb)[:2]:
        _add(events, "closed_hat", off, pos, 0.2, hv - 6, swing=swing, humanize=humanize)


def _add_fill(events, bar, bpb, humanize):
    """A rising 16th-note snare roll across the bar (section transition)."""
    off = bar * bpb
    grid = sixteenth_grid(bpb)
    for i, pos in enumerate(grid):
        velocity = 70 + int((i / max(1, len(grid) - 1)) * 45)  # 70 -> 115
        _add(events, "snare", off, pos, 0.18, velocity, swing=0.0, humanize=humanize)


def generate_drum_track(
    bars: int,
    beats_per_bar: int = BEATS_PER_BAR,
    *,
    sections: list[Section] | None = None,
    swing: float = 0.0,
    humanize: bool = False,
    kick_velocity: int = 112,
    clap_velocity: int = 98,
    hat_velocity: int = 78,
) -> Track:
    """Generate the kit.

    Default (no ``sections``): kick four-on-the-floor, clap on 2 & 4, closed hats
    off-beat, open hat on the last off-beat of every second bar — identical to
    the MVP. With ``sections`` the kit follows the arrangement and adds fills.
    """
    events: list[DrumEvent] = []
    modes = _section_modes(sections, bars)

    for bar in range(bars):
        info = modes[bar] if modes else {"mode": "main", "start": False, "end": False}
        mode = info["mode"]

        if mode == "intro":
            _bar_intro(events, bar, beats_per_bar, swing, humanize, hat_velocity)
        elif mode == "build":
            if info["end"]:
                _add_fill(events, bar, beats_per_bar, humanize)
            else:
                _bar_build(events, bar, beats_per_bar, swing, humanize,
                           kick_velocity, hat_velocity)
        elif mode == "break":
            if info["end"]:
                _add_fill(events, bar, beats_per_bar, humanize)
            else:
                _bar_break(events, bar, beats_per_bar, swing, humanize,
                           clap_velocity, hat_velocity)
        elif mode == "drop":
            if info["start"]:
                _add(events, "crash", bar * beats_per_bar, 0.0, 0.5,
                     hat_velocity + 30, swing=0.0, humanize=humanize)
            _bar_main(events, bar, beats_per_bar, swing, humanize,
                      kick_velocity, clap_velocity, hat_velocity, drop=True)
        elif mode == "outro":
            _bar_outro(events, bar, beats_per_bar, swing, humanize,
                       kick_velocity, hat_velocity)
        else:  # "main" — the exact MVP kit
            _bar_main(events, bar, beats_per_bar, swing, humanize,
                      kick_velocity, clap_velocity, hat_velocity)

    return Track(
        id="track_drums",
        name="four_on_the_floor_kit",
        role="drums",
        instrument_hint="Clean house kick, soft clap, tight closed hats, subtle swing",
        mixer_hint=MixerHint(
            volume_db=-5.0,
            pan=0.0,
            effects=["bus_compression_light", "hat_high_shelf"],
        ),
        drum_events=events,
        is_drum=True,
    )
