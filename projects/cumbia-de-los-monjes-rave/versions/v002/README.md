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

The experimental seion_ardour.cli currently reads legacy idea.json schemas;
it DOES NOT consume v002/prototype_manifest.json directly. Use manual import
or implement and test a manifest adapter before claiming full integration.

No original audio or source-song melody is included.
