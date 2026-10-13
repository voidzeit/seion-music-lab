# v002 — Three controlled, independent 16-bar prototypes

v001 was a 156 BPM / G minor placeholder and is NOT accepted as the remix.
Do not overwrite it. Generate original, new v002 MIDI with:

    python -m app.music.prototype_lab --out projects/cumbia-de-los-monjes-rave/versions/v002/generated

The generator refuses nonempty output directories. Each of the three modes
(groove, trance_bounce, hardcore_hybrid) produces seven independent MIDI role
files, a full Type-1 MIDI, plus a machine-readable prototype_manifest.json.

Musical baseline: **158 BPM, 4/4, C# minor candidate**, shared four-bar
C#m/B/B/F# harmony with intentional Dorian colour.

Technical MIDI validation does not confirm the sonic result. For each
prototype, choose independent kick, bass, harmony and lead synth patches, render
master + stems, audition with comparable loudness, and record human feedback.

The experimental seion_ardour.cli now has a --prototype option and accepts
v002/prototype_manifest.json. Linux CI tests the adapter with a fake renderer;
actual Windows Ardour9/Surge rendering remains unverified for this version.

No original audio or source-song melody is included.


## Local synth and review gate

    python -m pip install -e ".[preview]"
    python -m app.audio.preview_synth --bundle projects/cumbia-de-los-monjes-rave/versions/v002/generated --out projects/cumbia-de-los-monjes-rave/versions/v002/preview_wav
    python -m app.audio.audio_analysis --preview-root projects/cumbia-de-los-monjes-rave/versions/v002/preview_wav --out projects/cumbia-de-los-monjes-rave/versions/v002/preview_wav/technical_comparison.json
    python -m app.audio.listening_gate init projects/cumbia-de-los-monjes-rave/versions/v002/preview_wav

Render previews are separated by groove, trance_bounce, hardcore_hybrid.
One can audition without installing Ardour. Listen and rate all three before
explicit selection. Technical signal integrity never implies sonic approval.
