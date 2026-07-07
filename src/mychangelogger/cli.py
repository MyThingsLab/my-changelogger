from __future__ import annotations

import argparse
from pathlib import Path

from mythings.github import GitHub
from mythings.ledger import Ledger

from mychangelogger.changelogger import Changelogger, Result


def _render(result: Result) -> str:
    line = f"{result.outcome}: {result.detail}"
    if result.pr is not None:
        line += f" (PR #{result.pr})"
    return line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mychangelogger",
        description="Turn new dev-ledger entries into a CHANGELOG.md section and open a PR.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    update = sub.add_parser("update", help="add a changelog section for entries since the last run")
    update.add_argument("--version", help="release version for the new section (default: [Unreleased])")  # noqa: E501
    update.add_argument("--repo", help="GitHub slug owner/name for the PR (defaults to the local remote)")  # noqa: E501
    update.add_argument("--base", default="main", help="base branch for the PR")
    update.add_argument("--source", type=Path, default=Path.cwd(), help="local git repo to update")
    update.add_argument("--ledger", type=Path, default=Path(".mythings/ledger.jsonl"))

    args = parser.parse_args(argv)
    changelogger = Changelogger(
        repo=args.source,
        ledger=Ledger(args.ledger),
        github=GitHub(args.repo),
        base=args.base,
    )
    result = changelogger.update(version=args.version)
    print(_render(result))
    return 0 if result.outcome != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
