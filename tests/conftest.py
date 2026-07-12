from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from mythings.ledger import Ledger, LedgerEntry

# Shared fakes come from mythings.testing (plain imports; aliased fixture
# re-export + getfixturevalue wrapper per core docs/CONVENTIONS.md).
from mythings.testing import FakeGh
from mythings.testing import clean_git_env as _shared_clean_git_env  # noqa: F401


@pytest.fixture(autouse=True)
def _clean_git_env(request: pytest.FixtureRequest) -> None:
    # Real git worktrees in every test; hook-launched pytest (pre-commit)
    # must not leak GIT_* into them.
    request.getfixturevalue("_shared_clean_git_env")


def entry(kind: str, outcome: str, detail: str, *, ts: str) -> LedgerEntry:
    return LedgerEntry(tool="claude-code", kind=kind, outcome=outcome, detail=detail, ts=ts)


def fake_gh() -> FakeGh:
    return FakeGh({("pr", "create"): "https://github.com/owner/name/pull/9\n"})


def _git(repo: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True, text=True)


def make_target_repo(tmp_path: Path, dev_ledger: list[LedgerEntry]) -> Path:
    # Not the shared make_git_repo: the tree may be empty apart from the
    # dev-ledger (--allow-empty), which is the case the tool must handle.
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)

    repo = tmp_path / "work"
    repo.mkdir()
    ledger_file = repo / "dev-ledger" / "s0.jsonl"
    for e in dev_ledger:
        Ledger(ledger_file).append(e)

    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "Tester")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "init", "--allow-empty")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-u", "origin", "main")
    return repo
