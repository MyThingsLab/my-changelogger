from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from mythings._devledger import read_all
from mythings.github import GitHub, PullRequest
from mythings.isolation import Workspace, in_github_actions
from mythings.ledger import Ledger
from mythings.policy import ALLOW, Action, Decision, Policy, PolicyResult

from mychangelogger.changelog import prepend_section, relevant_entries, render_section

_CHANGELOG = "CHANGELOG.md"


class _AllowPolicy:
    def evaluate(self, action: Action) -> PolicyResult:
        return ALLOW


class PolicyDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class Result:
    outcome: str  # success | skipped | failure
    version: str | None
    pr: int | None
    detail: str
    entries_count: int = 0


def last_changelog_ts(ledger: Ledger) -> str | None:
    entries = ledger.read(tool="mychangelogger", kind="changelog")
    if not entries:
        return None
    return max(e.ts for e in entries)


class Changelogger:
    def __init__(
        self,
        *,
        repo: str | Path,
        ledger: Ledger,
        github: GitHub,
        base: str = "main",
        policy: Policy | None = None,
    ) -> None:
        self.repo = Path(repo)
        self.ledger = ledger
        self.github = github
        self.base = base
        self.policy: Policy = policy or _AllowPolicy()

    def update(self, *, version: str | None = None) -> Result:
        try:
            with Workspace(self.repo, self.base) as tree:
                return self._update_in(tree, version)
        except PolicyDenied as denied:
            return self._fail(version, str(denied))

    def _update_in(self, tree: Path, version: str | None) -> Result:
        since = last_changelog_ts(self.ledger)
        entries = relevant_entries(read_all(root=tree), since)
        if not entries:
            self._record("skipped", version, 0, "nothing new since last changelog", None)
            return Result("skipped", version, None, "nothing new since last changelog")

        section = render_section(entries, version)
        prepend_section(tree / _CHANGELOG, section)
        pr = self._open_pr(tree, version)
        detail = f"added entry for {version or 'unreleased'}"
        self._record("success", version, len(entries), detail, pr.number)
        return Result("success", version, pr.number, detail, len(entries))

    def _open_pr(self, tree: Path, version: str | None) -> PullRequest:
        branch = f"my-changelogger/{version}" if version else "my-changelogger/unreleased"
        self._git(tree, ["checkout", "-b", branch])
        self._git(tree, ["add", _CHANGELOG])
        self._git(tree, ["commit", "-m", f"docs: changelog for {version or 'unreleased'}"])
        self._git(tree, ["push", "-u", "origin", branch])
        title = f"docs: changelog for {version or 'unreleased'}"
        body = f"Adds a `{_CHANGELOG}` section for {version or 'unreleased'}."
        self._guard(f"gh pr create --head {branch} --base {self.base}")
        return self.github.open_pr(title=title, body=body, base=self.base, head=branch)

    def _git(self, tree: Path, argv: list[str]) -> None:
        self._guard("git " + " ".join(argv))
        proc = subprocess.run(["git", "-C", str(tree), *argv], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(argv)} failed: {proc.stderr.strip()}")

    def _guard(self, command: str) -> None:
        result = self.policy.evaluate(Action(kind="bash", payload={"command": command}))
        if result.under(unattended=in_github_actions()) is not Decision.ALLOW:
            raise PolicyDenied(f"policy blocked: {command} ({result.reason or result.decision})")

    def _fail(self, version: str | None, detail: str) -> Result:
        self._record("failure", version, 0, detail, None)
        return Result("failure", version, None, detail)

    def _record(
        self,
        outcome: str,
        version: str | None,
        entries_count: int,
        detail: str,
        pr: int | None,
    ) -> None:
        self.ledger.record(
            tool="mychangelogger",
            kind="changelog",
            outcome=outcome,
            detail=detail,
            version=version,
            entries_count=entries_count,
            pr=pr,
        )
