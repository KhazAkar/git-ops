# Practices - git-ops

Project actions and tooling. Four sections.

## Necessary and opt-in tooling

Necessary:
- `uv` - dependency management; the worker image runs
  `uv sync --frozen`, so `uv.lock` must exist and be current
- `mistral` CLI (v0.18+) - `mistral apps dev` for local serving,
  `mistral workflows init` for scaffold updates
- GitLab PAT `gitlab_tag_pat` (tag-scoped) in Secrets Manager,
  bound to the deployment as GITLAB_TAG_PAT

Opt-in:
- `lodectl check` - lint the lode/ structure
- `bltool` - GitLab release automation

## First setup

```
git clone git@gitlab.com:r3xxar/git-ops.git
cd git-ops
bash tools/uv.sh sync
cp .env.example .env   # fill GITLAB_TAG_PAT for local dev
```

The repo ships without `uv.lock` only on day one: run
`bash tools/uv.sh lock` once locally and commit it, because the
Docker build is frozen. See
[quirks-and-gotchas/README.md](quirks-and-gotchas/README.md).

## Running

Local worker: `mistral apps dev` from the repo root (uses
`apps/worker/src/worker/entrypoints/dev.py`).

Deployed worker: `git-ops-worker` on the Mistral platform, built
from the GitHub mirror `main`. Chat agents call it with
execute_workflow; revision pinning via expected_revision is
mandatory for mints.

## Testing

```
cd apps/worker
python3 -m unittest discover tests
```

`test_gitlab_logic.py` runs on the standard library alone: it
patches `gitlab._urlopen`, so it needs no PAT, no network, and no
SDK. The flow branches (exists / dry_run / create) are exercised
by the deployment smoke, not by unit tests; ADR-2026-11-16-002
marks which assertion is which.

Deployed verification: christening smoke (dry_run on
`r3xxar/lodectl`), then a real mint when the developer gates one.
