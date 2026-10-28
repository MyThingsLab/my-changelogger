# Changelog

## [Unreleased]
### Shipped
- pushed to github.com/MyThingsLab/my-changelogger; PR #1 opened, CI green on first push
### Added/Changed
- implemented Changelogger: reads dev-ledger via mythings._devledger.read_all, groups ship/build/fix under Shipped/Added-Changed/Fixed headings (decision omitted), prepends a CHANGELOG.md section inside a Workspace worktree, opens one PR; 10 tests green, ruff clean
- Mechanical migration to mythings.testing: shared FakeGh + clean_git_env replace local copies; the possibly-empty-tree make_target_repo stays local by design.
