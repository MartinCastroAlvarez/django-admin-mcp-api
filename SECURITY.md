# Security

`django-admin-mcp-api` is a **protocol-only adapter**. Everything below is
either an invariant of the adapter itself or a deliberate decision to defer
the question to `django-admin-rest-api`.

## Reporting a vulnerability

Open a private security advisory at
<https://github.com/MartinCastroAlvarez/django-admin-mcp-api/security/advisories/new>.
Do **not** open a public issue for a suspected vulnerability.

If the issue is in the underlying REST API, report it to
[`django-admin-rest-api`](https://github.com/MartinCastroAlvarez/django-admin-rest-api/security/advisories/new)
instead — that is where the fix will land.

We respond within 5 business days.

## 1. Threat model

`django-admin-mcp-api` only does two things:

1. Accept an authenticated HTTP request from the consumer's Django stack.
2. Translate an MCP JSON-RPC call into the equivalent
   `django-admin-rest-api` HTTP request and forward it.

It owns:

- The JSON-RPC envelope shape.
- The tool catalogue and the per-tool JSON-Schema validation.
- The "is the user signed in as staff?" baseline gate.

It does **not** own — and the code in this repo must never own:

- Any database query.
- Any permission check beyond the staff gate (per-tool permission is
  enforced inside rest-api).
- Any field serialization or form processing.
- Any new feature, validation rule, or behaviour that does not already
  exist in rest-api.

Trying to add one of those here is a bug. Open the change against
`django-admin-rest-api` instead.

## 2. Non-negotiable rules

These are enforced by pre-commit hooks **and** by `tests/test_security.py`.
If a rule is failing, fix the code — never relax the check.

1. **CSRF always on.** No view in `django_admin_mcp_api/` is
   `@csrf_exempt`. The `no-csrf-exempt` pygrep hook fails the commit.
2. **No direct DB access in the adapter.** `Model.objects.all()` and
   `Model.objects.filter()` are forbidden in `django_admin_mcp_api/server/`.
   Querysets come from `ModelAdmin.get_queryset(request)` — inside rest-api.
3. **No `user.has_perm()` calls.** Permission checks belong to rest-api.
4. **Staff-only by default.** `ALLOW_ANONYMOUS = True` is a test-only
   escape hatch. Setting it in production is a security incident.
5. **No new endpoints.** The shipped URL conf exposes exactly `/` (MCP
   JSON-RPC) and `/manifest/` (read-only catalogue). Any other endpoint
   is out of scope for this package.

## 3. Secrets handling

- **Nothing token-shaped lives in the repo.** `gitleaks protect` plus a
  local `no-partial-tokens` pygrep hook block any string matching
  `ghp_`, `gho_`, `ghs_`, `github_pat_`, `aws_secret_access_key`,
  `AKIA[0-9A-Z]{16}`, or `BEGIN (RSA|EC|OPENSSH) PRIVATE` from entering
  the index. The hook excludes its own definition, `SECURITY.md` (this
  file), and `tests/test_security.py` (which references the patterns to
  enforce them).
- **No `.env` is tracked.** `.env` is in `.gitignore`; `.env.example`
  is the only env file ever committed.
- **The MCP wire never logs request bodies that look like secrets.**
  Password set/change calls forward to rest-api's password form — the
  cleartext password is never logged by this package.

## 4. Dependency hygiene

- `pip-audit` runs in CI on every PR. Vulnerable dependencies block
  merge.
- Dependabot is enabled for Python and GitHub Actions.
- Direct dependencies are minimal by design: Django, plus
  `django-admin-rest-api` (once published). Everything else is a dev
  dependency.

## 5. Reproducibility

- Releases are built with `poetry build` and uploaded to PyPI by a
  human + GitHub Actions on a tagged commit. Trusted-Publisher
  authentication is enabled; we never put a long-lived PyPI token in
  the repo.
- The release script lives in `scripts/build.sh` and is reviewable.

## 6. Disclosures

Past advisories will be listed here once the package has shipped a
v0.1.0 to PyPI.
