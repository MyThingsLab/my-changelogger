from __future__ import annotations

import pytest

from mychangelogger import cli
from mychangelogger.changelogger import Result


def _stub_changelogger(monkeypatch: pytest.MonkeyPatch, result: Result) -> dict:
    captured: dict = {}

    class _Stub:
        def __init__(self, **kwargs: object) -> None:
            captured["kwargs"] = kwargs

        def update(self, *, version: str | None = None) -> Result:
            captured["update"] = {"version": version}
            return result

    monkeypatch.setattr(cli, "Changelogger", _Stub)
    return captured


def test_render_plain_outcome() -> None:
    assert cli._render(Result("skipped", None, None, "nothing new")) == "skipped: nothing new"


def test_render_includes_pr_number() -> None:
    out = cli._render(Result("success", "1.2.0", 12, "added section"))
    assert "(PR #12)" in out


@pytest.mark.parametrize(
    ("outcome", "code"),
    [("success", 0), ("skipped", 0), ("failure", 1)],
)
def test_exit_code_maps_outcome(
    monkeypatch: pytest.MonkeyPatch, outcome: str, code: int
) -> None:
    _stub_changelogger(monkeypatch, Result(outcome, None, None, "detail"))
    assert cli.main(["update"]) == code


def test_update_threads_version(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _stub_changelogger(monkeypatch, Result("success", "2.0.0", 3, "d"))

    cli.main(["update", "--version", "2.0.0"])

    assert captured["update"] == {"version": "2.0.0"}


def test_base_flag_reaches_the_changelogger(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _stub_changelogger(monkeypatch, Result("success", None, None, "d"))

    cli.main(["update", "--base", "dev"])

    assert captured["kwargs"]["base"] == "dev"


def test_prints_rendered_result(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_changelogger(monkeypatch, Result("success", "1.0.0", 9, "added section"))

    cli.main(["update"])

    assert "success: added section (PR #9)" in capsys.readouterr().out


def test_missing_subcommand_is_a_usage_error() -> None:
    with pytest.raises(SystemExit):
        cli.main([])
