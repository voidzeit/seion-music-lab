# Task: create variations

Given a `MusicalIdea` and a direction from the user (e.g. "darker, less happy,
simpler arp"), produce a new version.

Steps:
1. Read the user's likes/dislikes and the free-form request.
2. Apply targeted changes (swap a chord, thin the arp, change register, adjust
   energy) — small, explainable edits, not a rewrite.
3. Re-score with SEION and `compare_versions` against the previous score.
4. Export as a new project version and explain exactly what changed and why.

Prefer one clear change the user can hear over many at once.
