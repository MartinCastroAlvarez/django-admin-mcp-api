# `examples/`

> Runnable demos. `cd` into one, follow its README, and you have a
> working `django-admin-mcp-api` install in under a minute.

## In this folder

| Example                          | Shows                                                              |
| -------------------------------- | ------------------------------------------------------------------ |
| [`quickstart/`](quickstart/)     | The smallest possible Django project that mounts the MCP adapter and dispatches a real `tools/call`. Use this to confirm your install before integrating into your own project. |

## What does NOT belong here

- **Anything the shipped package depends on.** The wheel never imports from `examples/`; each example is a standalone project that consumes the published package via `pip`.
- **Production deployment recipes.** Those live in the consumer's own infra, not in this repo.

## See also

- [`../README.md`](../README.md) — the 30-second install snippet.
- [`../docs/api-contract.md`](../docs/api-contract.md) — the wire contract you'll see in the smoke output.
