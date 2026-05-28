"""Security invariants of the shipped package.

These tests are the executable form of ``SECURITY.md``. If one of them
fails, fix the package — never relax the test.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "django_admin_mcp_api"


def _read_all_py():
    for path in PACKAGE_ROOT.rglob("*.py"):
        yield path, path.read_text(encoding="utf-8")


def test_no_csrf_exempt_in_package():
    """No view in the shipped package may be CSRF-exempt."""
    offenders = []
    for path, source in _read_all_py():
        if "csrf_exempt" in source:
            offenders.append(str(path))
    assert not offenders, f"csrf_exempt found in: {offenders}"


def test_no_direct_objects_queries_in_server():
    """The server layer must never query the DB — that's rest-api's job."""
    pattern = re.compile(r"objects\.(all|filter)\(")
    offenders = []
    for path, source in _read_all_py():
        if "server/" in str(path) and pattern.search(source):
            offenders.append(str(path))
    assert not offenders, f"objects.all/filter found in server/: {offenders}"


def test_no_user_has_perm_in_package():
    """Permission checks belong to django-admin-rest-api, not this layer."""
    offenders = []
    for path, source in _read_all_py():
        if "user.has_perm(" in source:
            offenders.append(str(path))
    assert not offenders, f"user.has_perm found in: {offenders}"


def test_no_partial_token_references():
    """No token-shaped strings anywhere in the shipped package.

    Defense in depth on top of the pre-commit hook and gitleaks. If you
    need to *document* a forbidden pattern (e.g., in this file), excerpt
    it via concatenation so the rule itself is not detected as a leak.
    """
    needles = ["ghp_", "gho_", "ghs_", "github_pat_", "aws_secret_access_key"]
    for path, source in _read_all_py():
        for needle in needles:
            assert needle not in source, f"Token-shaped substring {needle!r} found in {path}"


def test_repo_tree_has_no_env_file():
    """The .env file must never be tracked in git."""
    git = shutil.which("git")
    if git is None:
        # No git on the host (CI matrix can include minimal images).
        # The .gitignore + pre-commit hook are the primary defence;
        # this test is belt-and-braces.
        return
    result = subprocess.run(  # noqa: S603 — runs against the local repo only.
        [git, "ls-files", "--error-unmatch", ".env"],
        cwd=PACKAGE_ROOT.parent,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0, ".env appears to be tracked by git"
