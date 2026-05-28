# `docs/`

Long-form documentation. The README, ARCHITECTURE, SECURITY, and
CHANGELOG at the repo root cover the day-to-day surface; the documents
here go deeper.

| File                           | Purpose                                                       |
| ------------------------------ | ------------------------------------------------------------- |
| [`threat-model.md`](threat-model.md) | MCP-layer threat model: assets, trust boundaries, mitigations, out-of-scope items. |
| [`api-contract.md`](api-contract.md) | The MCP wire contract: JSON-RPC methods, tool schemas, error codes, response envelope. |

## What does NOT live here

- README content — the top-level README is the canonical install /
  quickstart entry point.
- Per-folder explainers — those live next to the code in
  `django_admin_mcp_api/*/README.md`.
- Decisions / open questions — those are tracked in GitHub Issues and
  the Project board, not in markdown.
