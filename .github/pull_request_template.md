<!--
Thanks for opening a PR. A few things to confirm before review:

- The change does NOT introduce new admin functionality, permission
  checks, queryset construction, or serialization (those belong to
  django-admin-rest-api).
- The five rules in CLAUDE.md still hold.
- Pre-commit hooks (`pre-commit install`) ran cleanly on this branch.
-->

## Summary

<!-- One or two sentences. What changed and why. -->

## Test plan

<!-- Bulleted list of how you verified the change. The reviewer should be
     able to repeat these steps. -->

- [ ] `poetry run pytest -q` passes locally
- [ ] `poetry run bash scripts/lint.sh` passes locally
- [ ] CHANGELOG.md updated (Unreleased section) for user-visible changes
- [ ] Any new tools have a matching case in `tests/test_tools.py`
- [ ] No secrets, PATs, or credentials in the diff
- [ ] Linked to its issue (or there's no driving issue)

## Linked issue

<!-- Closes #N, or "n/a — chore" -->

## Notes for reviewer

<!-- Anything non-obvious about the approach, trade-offs, things you tried
     and rejected, edge cases that need extra scrutiny. -->
