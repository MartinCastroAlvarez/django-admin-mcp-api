# `.github/`

> Repository automation — CI, Dependabot, code-owners, issue & PR templates.
> Nothing here ships in the wheel; everything here keeps the wheel honest.

## In this folder

| File / dir                              | Purpose                                                                              |
| --------------------------------------- | ------------------------------------------------------------------------------------ |
| [`workflows/ci.yml`](workflows/ci.yml)  | CI pipeline — lint, `pip-audit`, and the test matrix across Python 3.10–3.13 × Django 5.0/5.1/5.2/6.0. |
| [`dependabot.yml`](dependabot.yml)      | Weekly dependency bumps. `django-admin-rest-api` is watched in its own group so upstream releases show up as standalone PRs. |
| [`CODEOWNERS`](CODEOWNERS)              | Routes every PR review through the package maintainer; tighter on the wire layer and security-impacting files. |
| [`ISSUE_TEMPLATE/bug_report.yml`](ISSUE_TEMPLATE/bug_report.yml)         | Structured bug report; collects versions + repro and redirects bugs in the underlying REST API to the upstream repo. |
| [`ISSUE_TEMPLATE/feature_request.yml`](ISSUE_TEMPLATE/feature_request.yml) | Feature requests, gated by "is this MCP wire behaviour or admin behaviour?". |
| [`ISSUE_TEMPLATE/config.yml`](ISSUE_TEMPLATE/config.yml)                 | Disables blank issues; surfaces the security advisory link, the rest-api repo, Discussions, and the project board. |
| [`pull_request_template.md`](pull_request_template.md)                   | Nudges contributors toward CHANGELOG + test plan + the five rules in `CLAUDE.md`.   |

## What does NOT belong here

- **Secrets.** Repository / org / environment secrets are managed in the GitHub UI; the workflows reference them by name only.
- **Package code.** Anything importable from the published wheel lives under [`django_admin_mcp_api/`](../django_admin_mcp_api/).
- **End-user documentation.** That goes in the top-level [`docs/`](../docs/) folder.

## See also

- [`../README.md`](../README.md) — user-facing entry point.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — the design contract.
- [`../CLAUDE.md`](../CLAUDE.md) — the contributor / agent contract.
