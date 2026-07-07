# my-changelogger — agent instructions

You are developing **my-changelogger**, a MyThingsLab My[X] tool.

**Inherited rules:** obey [`./HARNESS.md`](./HARNESS.md) in full — the vendored
MyThingsLab build-harness rules. Do not restate or override them. Anything not
covered here defers to `HARNESS.md`, then `mythings-core/docs/CONVENTIONS.md`.

## This tool

- **Purpose:** reads a target repo's `dev-ledger/` entries since the last
  `kind=changelog` entry this tool wrote, groups them under conventional-
  changelog-style headings, and opens a PR prepending a new section to
  `CHANGELOG.md`.
- **The single Engine call:** none — deterministic formatting only, same as
  MyReporter's default path. Ledger entries already carry a one-sentence
  `detail`; this tool arranges them, it never composes prose.
- **Invariants / rules:** touches exactly one file (`CHANGELOG.md`), never
  edits source. Every `git`/`gh` side effect is wrapped as
  `Action(kind="bash", ...)` and run through `Policy.evaluate` first; a `DENY`
  aborts and logs `outcome=failure`. Runtime dep is `mythings-core` only (not
  `my-guard`) — like MyReporter, its default `Policy` trivially allows
  (opening a non-destructive PR needs no gate), and a real `Policy` (e.g.
  MyGuard's `Guard`) can be injected by the caller. Opens exactly one PR, never
  merges. If there are no new entries since the last changelog write,
  `outcome=skipped` — no worktree/PR side effects beyond that ledger entry.
- **Backlog label:** `my-changelogger`.
