# Monty v0.7 — MCPBackend bridge

MCPBackend project `Monty Racing` is active. Four owner-only tables exist: `race_meetings`, `runners`, `monty_predictions`, `race_results`.

`backend_bridge.py` prepares rows from the existing V6 snapshot and scoring output. It defaults to an **offline preview**, does not upload data or expose credentials, and refuses to freeze predictions unless the audit explicitly confirms independent TAB verification. No live data was inserted during this build.

Example:

```bash
python backend_bridge.py --snapshot path/to/krok_snapshot.json --scored path/to/monty_selections.csv --audit path/to/run_audit.json --output backend_preview.json
```

For server-side upload only, provide a **new, narrowly scoped** MCPBackend project API key through `MCPBACKEND_API_KEY` and add `--upload`. Do not place keys in files, ChatGPT messages, client/browser code or logs. This is not a hosted background service. Repeated uploads may create duplicate records; use once per frozen snapshot until idempotent ingestion is implemented. The Krok API connection remains blocked from this environment and is not fixed by MCPBackend.
