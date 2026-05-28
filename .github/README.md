# `.github/`

GitHub-specific configuration.

| File / dir            | Purpose                                                       |
| --------------------- | ------------------------------------------------------------- |
| `workflows/ci.yml`    | CI pipeline — lint, type-check, tests across Python + Django matrix. |
| `dependabot.yml`      | Dependabot config — weekly bumps, with `django-admin-rest-api` watched separately so its updates are highly visible. |

## What does NOT live here

- Secrets — repository / org / environment secrets are managed in the
  GitHub UI, not in version control. The workflows reference them by
  name only.
- Documentation that belongs in the package itself — that goes in the
  top-level `docs/` folder.
