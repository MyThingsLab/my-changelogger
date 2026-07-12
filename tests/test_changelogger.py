from __future__ import annotations

from pathlib import Path

from mythings.github import GitHub
from mythings.ledger import Ledger
from mythings.policy import Action, Decision, PolicyResult

from conftest import entry, fake_gh, make_target_repo
from mychangelogger.changelogger import Changelogger


def _changelogger(repo: Path, tmp_path: Path, **kw) -> tuple[Changelogger, fake_gh, Ledger]:
    fake = fake_gh()
    ledger = Ledger(tmp_path / "ledger.jsonl")
    github = GitHub("owner/name", runner=fake)
    changelogger = Changelogger(repo=repo, ledger=ledger, github=github, **kw)
    return changelogger, fake, ledger


def test_happy_path_opens_pr_with_grouped_entries(tmp_path: Path) -> None:
    repo = make_target_repo(
        tmp_path,
        dev_ledger=[
            entry("ship", "success", "released v0.0.1", ts="2026-07-06T01:00:00Z"),
            entry("fix", "success", "fixed off-by-one", ts="2026-07-06T02:00:00Z"),
            entry("decision", "success", "chose JSON over YAML", ts="2026-07-06T02:30:00Z"),
        ],
    )
    changelogger, fake, ledger = _changelogger(repo, tmp_path)

    result = changelogger.update()

    assert result.outcome == "success"
    assert result.pr == 9
    assert result.entries_count == 2  # decision omitted
    assert any(c[:2] == ["pr", "create"] for c in fake.calls)

    written = list(ledger)[0]
    assert written.kind == "changelog"
    assert written.outcome == "success"
    assert written.data["pr"] == 9
    assert written.data["entries_count"] == 2


def test_no_new_entries_is_a_noop(tmp_path: Path) -> None:
    repo = make_target_repo(tmp_path, dev_ledger=[])
    changelogger, fake, ledger = _changelogger(repo, tmp_path)

    result = changelogger.update()

    assert result.outcome == "skipped"
    assert result.pr is None
    assert not any(c[:2] == ["pr", "create"] for c in fake.calls)
    assert list(ledger)[0].outcome == "skipped"


def test_second_run_is_incremental(tmp_path: Path) -> None:
    repo = make_target_repo(
        tmp_path,
        dev_ledger=[entry("ship", "success", "released v0.0.1", ts="2026-07-06T01:00:00Z")],
    )
    changelogger, fake, ledger = _changelogger(repo, tmp_path)
    first = changelogger.update()
    assert first.outcome == "success"

    second = changelogger.update()

    assert second.outcome == "skipped"  # nothing new since the first run's write


class _DenyAll:
    def evaluate(self, action: Action) -> PolicyResult:
        return PolicyResult(Decision.DENY, reason="locked down", rule="deny_all")


def test_policy_deny_aborts_with_failure(tmp_path: Path) -> None:
    repo = make_target_repo(
        tmp_path,
        dev_ledger=[entry("ship", "success", "released v0.0.1", ts="2026-07-06T01:00:00Z")],
    )
    changelogger, fake, ledger = _changelogger(repo, tmp_path, policy=_DenyAll())

    result = changelogger.update()

    assert result.outcome == "failure"
    assert result.pr is None
    assert not any(c[:2] == ["pr", "create"] for c in fake.calls)
    assert list(ledger)[0].outcome == "failure"
