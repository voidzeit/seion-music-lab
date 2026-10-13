# Evidence Ledger

`ledger.jsonl` is an append-only provenance log. Every AMO command that observes,
derives, or compiles repository knowledge appends one JSON line describing what
ran, what it produced, and how much authority the result carries.

Authority bands:

- `0.9` observed evidence (scan, validation, benchmark)
- `0.8` derived evidence (graph build, optimizer trials)
- `0.6` compiled artifacts (context packs, handoffs, adapter exports)
- `0.5` declared memory updates (postflight summaries are agent-declared
  until corroborated by validation evidence)

Rules:

- The ledger is append-only; entries are never rewritten or deleted.
- `.ai/runtime/` contents are never durable truth and are not recorded here.
- If ledger evidence contradicts source code, source code wins.
