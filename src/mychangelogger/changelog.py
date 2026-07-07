from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from mythings.ledger import LedgerEntry

_HEADINGS = {"ship": "Shipped", "build": "Added/Changed", "fix": "Fixed"}
_ORDER = ("ship", "build", "fix")
_STANDARD_HEADER = "# Changelog\n"


def relevant_entries(entries: list[LedgerEntry], since: str | None) -> list[LedgerEntry]:
    return [e for e in entries if e.kind in _HEADINGS and (since is None or e.ts > since)]


def render_section(entries: list[LedgerEntry], version: str | None) -> str:
    if version:
        heading = f"## [{version}] - {datetime.now(UTC).date().isoformat()}"
    else:
        heading = "## [Unreleased]"
    by_kind: dict[str, list[LedgerEntry]] = defaultdict(list)
    for entry in entries:
        by_kind[entry.kind].append(entry)

    parts = [heading]
    for kind in _ORDER:
        group = by_kind.get(kind)
        if not group:
            continue
        parts.append(f"### {_HEADINGS[kind]}")
        parts += [f"- {e.detail}" for e in group]
    return "\n".join(parts)


def prepend_section(path: Path, section: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else _STANDARD_HEADER
    lines = existing.splitlines()
    if lines and lines[0].startswith("#"):
        header, rest = lines[0], "\n".join(lines[1:]).strip()
    else:
        header, rest = _STANDARD_HEADER.strip(), existing.strip()

    parts = [header, "", section]
    if rest:
        parts += ["", rest]
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
