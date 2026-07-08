from __future__ import annotations

from pathlib import Path

from mythings.ledger import LedgerEntry

from mychangelogger.changelog import prepend_section, relevant_entries, render_section


def _entry(kind: str, detail: str, ts: str) -> LedgerEntry:
    return LedgerEntry(tool="claude-code", kind=kind, outcome="success", detail=detail, ts=ts)


def test_relevant_entries_filters_kind_and_window() -> None:
    entries = [
        _entry("ship", "released v0.0.1", "2026-07-06T01:00:00Z"),
        _entry("decision", "chose JSON over YAML", "2026-07-06T01:30:00Z"),
        _entry("fix", "fixed off-by-one", "2026-07-06T02:00:00Z"),
        _entry("ship", "old ship", "2026-07-05T00:00:00Z"),
    ]

    out = relevant_entries(entries, since="2026-07-06T00:00:00Z")

    assert [e.detail for e in out] == ["released v0.0.1", "fixed off-by-one"]


def test_render_section_groups_by_heading() -> None:
    entries = [
        _entry("ship", "released v0.0.1", "2026-07-06T01:00:00Z"),
        _entry("build", "added feature x", "2026-07-06T01:15:00Z"),
        _entry("fix", "fixed off-by-one", "2026-07-06T02:00:00Z"),
    ]

    section = render_section(entries, version=None)

    assert "## [Unreleased]" in section
    assert "### Shipped" in section
    assert "- released v0.0.1" in section
    assert "### Added/Changed" in section
    assert "### Fixed" in section
    assert section.index("### Shipped") < section.index("### Added/Changed")
    assert section.index("### Added/Changed") < section.index("### Fixed")


def test_render_section_uses_version_heading() -> None:
    entries = [_entry("ship", "released v0.0.1", "2026-07-06T01:00:00Z")]
    section = render_section(entries, version="1.2.0")
    assert section.startswith("## [1.2.0] -")


def test_prepend_section_creates_file_with_standard_header(tmp_path: Path) -> None:
    path = tmp_path / "CHANGELOG.md"
    prepend_section(path, "## [Unreleased]\n### Shipped\n- released v0.0.1")

    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Changelog")
    assert "## [Unreleased]" in text


def test_prepend_section_keeps_older_sections_below(tmp_path: Path) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text("# Changelog\n\n## [1.0.0] - 2026-06-01\n### Shipped\n- first release\n",
                     encoding="utf-8")

    prepend_section(path, "## [Unreleased]\n### Fixed\n- fixed off-by-one")

    text = path.read_text(encoding="utf-8")
    assert text.index("## [Unreleased]") < text.index("## [1.0.0]")
    assert "first release" in text


from pathlib import Path

from mychangelogger.changelog import prepend_section


def test_prepend_section_inserts_new_section_before_existing_entries(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## [0.0.1] - 2026-07-01\n### Fixed\n- old fix\n",
        encoding="utf-8",
    )

    prepend_section(changelog, "## [Unreleased]\n### Shipped\n- new feature")

    assert changelog.read_text(encoding="utf-8") == (
        "# Changelog\n\n"
        "## [Unreleased]\n### Shipped\n- new feature\n\n"
        "## [0.0.1] - 2026-07-01\n### Fixed\n- old fix\n"
    )
