# `docs/`

> Long-form documentation. The README, ARCHITECTURE, SECURITY, and
> CHANGELOG at the repo root cover the day-to-day surface; the documents
> here go deeper.

## In this folder

| File                                       | Purpose                                                        |
| ------------------------------------------ | -------------------------------------------------------------- |
| [`threat-model.md`](threat-model.md)       | MCP-layer threat model — assets, trust boundaries, mitigations, what's delegated to rest-api / the consumer, and a review checklist. |
| [`api-contract.md`](api-contract.md)       | The MCP wire contract — JSON-RPC envelope shapes, the three methods (`initialize` / `tools/list` / `tools/call`), error codes, response envelope, semver stability policy. |

## What does NOT belong here

- **README content.** The top-level [`README.md`](../README.md) is the canonical install / quickstart entry point.
- **Per-folder explainers.** Those live next to the code (e.g. [`django_admin_mcp_api/server/README.md`](../django_admin_mcp_api/server/README.md)).
- **Decisions / open questions.** Tracked in [GitHub Issues](https://github.com/MartinCastroAlvarez/django-admin-mcp-api/issues) and the [project board](https://github.com/users/MartinCastroAlvarez/projects/4), not in markdown.

## See also

- [`../README.md`](../README.md) — the user-facing entry point.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — the design contract.
- [`../SECURITY.md`](../SECURITY.md) — the non-negotiable security rules.
