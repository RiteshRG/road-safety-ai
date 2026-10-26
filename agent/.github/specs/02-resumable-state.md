# 02 — Persistent resumable state

Derive an isolated run ID from normalized scenario text. Persist run status and completed stage names in JSON. Save each stage artifact using atomic replace before marking the stage complete. At startup, inspect both state and artifact validity; a missing/corrupt artifact must be recomputed. Identical scenario reruns reuse complete work. A changed scenario uses a new directory. API credentials must never enter state.
