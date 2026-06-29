"""Four-on-the-floor drum generator: kick, clap, hats. Simple and editable."""

from __future__ import annotations

from app.music.constants import BEATS_PER_BAR, GM_DRUMS
from app.music.rhythm import downbeats, offbeat_eighths
from app.schemas import DrumEvent, MixerHint, Track


def generate_drum_track(
    bars: int,
    beats_per_bar: int = BEATS_PER_BAR,
    kick_velocity: int = 112,
    clap_velocity: int = 98,
    hat_velocity: int = 78,
) -> Track:
    """Classic warm-house kit:

    - kick four-on-the-floor (every beat),
    - clap on beats 2 and 4,
    - closed hat on every off-beat,
    - open hat on the last off-beat of every second bar (subtle lift).
    """
    events: list[DrumEvent] = []

    for bar in range(bars):
        bar_offset = bar * beats_per_bar

        # Kick on every beat.
        for beat in downbeats(beats_per_bar):
            events.append(
                DrumEvent(
                    instrument="kick",
                    midi=GM_DRUMS["kick"],
                    start_beat=float(bar_offset + beat),
                    duration_beats=0.25,
                    velocity=kick_velocity,
                )
            )

        # Clap / snare on beats 2 and 4 (0-indexed beats 1 and 3).
        for beat in (1, 3):
            events.append(
                DrumEvent(
                    instrument="clap",
                    midi=GM_DRUMS["clap"],
                    start_beat=float(bar_offset + beat),
                    duration_beats=0.25,
                    velocity=clap_velocity,
                )
            )

        # Closed hats on the off-beats; swap the last one for an open hat on
        # every second bar to breathe.
        offbeats = offbeat_eighths(beats_per_bar)
        last_offbeat = offbeats[-1]
        open_hat_bar = bar % 2 == 1
        for pos in offbeats:
            is_open = open_hat_bar and abs(pos - last_offbeat) < 1e-6
            events.append(
                DrumEvent(
                    instrument="open_hat" if is_open else "closed_hat",
                    midi=GM_DRUMS["open_hat"] if is_open else GM_DRUMS["closed_hat"],
                    start_beat=float(bar_offset + pos),
                    duration_beats=0.2 if not is_open else 0.4,
                    velocity=hat_velocity + (6 if is_open else 0),
                )
            )

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
