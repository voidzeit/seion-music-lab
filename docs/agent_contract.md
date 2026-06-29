# Agent contract

Every agent has a narrow responsibility and a typed interface. In the MVP they
are deterministic; the contracts are designed so an LLM-backed implementation can
replace any one of them without touching the orchestrator.

| Agent | Input | Output | Responsibility |
| --- | --- | --- | --- |
| `intake_agent` | prompt / `UserRequest` | `UserRequest` | normalise the request |
| `reference_agent` | `style_targets` | style context dict | artists -> actionable traits |
| `composer_agent` | `UserRequest`, style context | tracks, automation, decisions | generate editable material |
| `arranger_agent` | `UserRequest`, energy | `list[Section]` | structure (MVP: one loop) |
| `sound_design_agent` | `MusicalIdea` | `{role: [tips]}` | FL Studio sound advice |
| `critic_agent` | `MusicalIdea`, `SeionScore` | `[{target, change, reason}]` | concrete fixes |
| `seion_agent` | `MusicalIdea`, `UserRequest`, ctx | `SeionScore` | deterministic scoring |
| `teacher_agent` | `MusicalIdea` (+extras) | Markdown | explain it for learning |

## Hard rules every agent obeys

- No opaque music — every decision is recorded in the decision log.
- Every track has exactly one clear musical role.
- Tracks are always separated by role and exported individually.
- Prefer clarity over complexity; do not overload the loop.
- All musical output is representable as a `MusicalIdea`.

## Decision log entry

Each meaningful choice appends a `DecisionLogEntry`:

```json
{
  "decision_id": "d001",
  "agent": "composer_agent",
  "type": "harmony",
  "decision": "Use Am7 - Fmaj7 - Cmaj7 - G6",
  "reason": "min7/maj7 give warm nostalgia without being too dark or too happy.",
  "references": ["Computer Data", "NTO"],
  "expected_effect": "warmth, nostalgia, harmonic softness"
}
```

This log is what trains the producer's ear, so it is mandatory, not optional.
