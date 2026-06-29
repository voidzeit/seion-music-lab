# Task: generate a loop

Given a `UserRequest`, produce one editable loop.

Steps:
1. Load style traits for the references.
2. Pick BPM, key, energy and bar count (8/16/32).
3. Generate harmony (seventh chords), bass (offbeat root), arp (chord tones),
   drums (four-on-the-floor).
4. Add one tension move (e.g. slow filter open) instead of more notes.
5. Score with SEION; if below the gate, take one critic-driven pass.
6. Export per-track MIDI + `full_loop.mid` + `idea.json` + `explanation.md`.

Keep it editable and explained. Do not overload.
