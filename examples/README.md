# `examples/`

Runnable demos you can `cd` into and start in under a minute.

| Example                     | What it shows                                                       |
| --------------------------- | ------------------------------------------------------------------- |
| [`quickstart/`](quickstart/) | Smallest possible Django project that mounts the MCP adapter and dispatches a real `tools/call`. Use this to confirm your install before integrating into your own project. |

## What does NOT live here

- Anything that the shipped package depends on. The wheel never imports
  from `examples/` — they're standalone projects that consume the
  published package via `pip`.
- Production deployment recipes. The repo is small on purpose; deploy
  recipes live in the consumer's own infra.
