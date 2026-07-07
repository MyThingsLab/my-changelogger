from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from mythings.ledger import Ledger, LedgerEntry


@pytest.fixture(autouse=True)
def _clean_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # pre-commit runs hooks with GIT_DIR/GIT_INDEX_FILE set; they leak into the
    # git subprocesses these tests spawn (and into isolation.Workspace) and break
    # worktree ops on the throwaway repo. Real MyChangelogger runs aren't inside a hook.
    for var in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY"):
        monkeypatch.delenv(var, raising=False)


def entry(kind: str, outcome: str, detail: str, *, ts: str) -> LedgerEntry:
    return LedgerEntry(tool="claude-code", kind=kind, outcome=outcome, detail=detail, ts=ts)


class FakeRunner:
    # Mocks only the `gh` subprocess boundary.
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> str:
        self.calls.append(argv)
        if argv[:2] == ["pr", "create"]:
            return "https://github.com/owner/name/pull/9\n"
        raise AssertionError(f"unexpected gh call: {argv}")


def _git(repo: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True, text=True)


def make_target_repo(tmp_path: Path, dev_ledger: list[LedgerEntry]) -> Path:
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
