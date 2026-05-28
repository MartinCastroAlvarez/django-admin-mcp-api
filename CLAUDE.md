# CLAUDE.md

Contract between this repository and any AI agent contributing to it.
Read top to bottom before doing anything else, every session.

## 0. Required reading

1. This file.
2. [`README.md`](README.md) — the user-facing mission.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — the design contract.
4. [`SECURITY.md`](SECURITY.md) — non-negotiable security rules.
5. The folder-level `README.md` for any folder your task touches.
6. The open
   [Issues](https://github.com/MartinCastroAlvarez/django-admin-mcp/issues)
   and the
   [Project board](https://github.com/users/MartinCastroAlvarez/projects/4).

## 1. Mission summary

We are building an open-source Django package, **`django-admin-mcp-api`**, that:

- Is installed with `pip install django-admin-mcp-api` and added to
  `INSTALLED_APPS`.
- Mounts at any URL the consumer chooses (e.g.,
  `path("mcp/", include("django_admin_mcp_api.urls"))`).
- Exposes the MCP (Model Context Protocol) JSON-RPC 2.0 wire on top of
  [`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api).
- Reuses the consumer's existing `ModelAdmin` classes — through rest-api —
  as the **only** source of truth for permissions, querysets, forms, and
  serialization.
- Reuses Django's session + CSRF for authentication. Staff-only by default.

This package is a **wire-protocol adapter, not an admin engine.** That
distinction is the prime directive.

## 2. The five rules

These mirror django-admin-react's prime directives. Violating one is a
review-blocking comment.

1. **`django-admin-rest-api` is the only source of admin behaviour.**
   Never re-implement permissions, querysets, forms, or serialization
   here.
2. **Never `Model.objects.all()` / `Model.objects.filter()` in
   `django_admin_mcp_api/server/`.** This package does not query the
   database.
3. **Never `user.has_perm(…)`.** Per-tool permission is owned by
   rest-api.
4. **Staff-only by default, CSRF always on.** No view is `@csrf_exempt`.
   `ALLOW_ANONYMOUS = True` is test-only.
5. **Every folder has a `README.md`.** Adding a folder without one is a
   review-blocking comment.

## 3. Working agreements

- **PR-only flow.** No direct commits to `main` except the bootstrap
  empty commit. Branch as `feat/…`, `fix/…`, `docs/…`, `chore/…`.
- **One PR per branch. Keep PRs small.** Split aggressively.
- **Update docs in the same PR.** Architecture / scope changes that
  don't update the corresponding doc get reverted.
- **No secrets in commits.** `gitleaks` and the local
  `no-partial-tokens` pygrep hook are authoritative. Never bypass with
  `--no-verify`.
- **Tests before or alongside features.** See §5.
- **Boring beats clever.** Stable, readable code beats abstraction.
- **Ambiguous → ask, don't invent.** Open a Discussion or comment on the
  driving issue.

## 4. The single seam

Almost all of this package is wire shape. The one piece that touches
the outside world is
[`django_admin_mcp_api/server/dispatch.py`](django_admin_mcp_api/server/dispatch.py).
That file owns the forward to `django-admin-rest-api` and nothing else
in the repo does. When rest-api ships, *only* that file changes.

## 5. Test minimums

For every change to a tool or view:

- Anonymous user → `401`.
- Authenticated non-staff → `403`.
- Authenticated staff → success path.
- Unknown tool name → `METHOD_NOT_FOUND`.
- Missing required argument → `INVALID_PARAMS`.
- Wire shape (method/path/body/query) matches the rest-api endpoint
  exactly (assert in `tests/test_tools.py`).
- The security invariants in `tests/test_security.py` still pass.

## 6. Git / GitHub etiquette

- Never force-push `main`.
- Never `git config --global` anything.
- Never bypass hooks (`--no-verify`) without explaining in the PR why.
- Use `gh pr create` with a HEREDOC body so newlines render.
- Commit messages: imperative mood, ≤72 char subject, body explains why.
- **Never paste tokens** (PATs, API keys, anything) in commits,
  comments, PR descriptions, or issue bodies. The pre-commit hook
  blocks them; the test suite scans for them.

## 7. When stuck

- Open a draft PR with what you have. Describe the blocker in the PR
  body.
- Open a [Discussion](https://github.com/MartinCastroAlvarez/django-admin-mcp/discussions)
  if it's a question that needs a human.
- Open an Issue if it's a tracked piece of work.

Do **not**:

- Silently change scope.
- Disable a security check to make a test pass.
- Force-push or rewrite shared history.
- Add a feature flag to hide an unfinished feature.
