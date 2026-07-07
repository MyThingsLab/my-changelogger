# my-changelogger

Turns a repo's [`dev-ledger`](../mythings-core/docs/PROVENANCE.md) `ship`/`fix`/
`build` entries into a `CHANGELOG.md` section and opens a PR, for the
[MyThingsLab](../mythings-core) fleet.

## How it works

Deterministic, no Engine call:

1. Read the target repo's `dev-ledger/*.jsonl`, sorted by timestamp.
2. Take entries since this tool's own last `kind=changelog` write (or all-time
   on first run) — the same incremental-window pattern as MyReporter.
3. Group by kind: `ship` → "Shipped", `build` → "Added/Changed", `fix` →
   "Fixed". `decision` entries are internal rationale and are omitted.
4. Prepend a new `## [Unreleased]` (or `## [X.Y.Z] - date` with `--version`)
   section to `CHANGELOG.md`, creating the file if it doesn't exist, and open
   a PR with the single-file diff.

If there's nothing new since the last run, it does nothing (`outcome=skipped`)
— no worktree, no PR.

## Usage

```bash
mychangelogger update [--version X.Y.Z] [--repo owner/name] [--base main]
```

## Install (development)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ../mythings-core -e ".[dev]"
pytest
```

## License

MIT — see [`LICENSE`](LICENSE).
