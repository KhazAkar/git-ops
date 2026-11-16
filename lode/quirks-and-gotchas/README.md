# Quirks and Gotchas - git-ops

Unexpected or live-behaviour findings. One topic per entry.

## uv.lock is required by the build but not generatable in every dev environment

`deploy/docker/Dockerfile.worker` runs `uv sync --frozen`, which
fails without `uv.lock`. The repo was first pushed from an
environment where package installation is blocked, so the lock
could not be generated there. Day-one state: no `uv.lock`. Fix:
one local `bash tools/uv.sh lock`, then commit and push. After
that, never edit dependencies without re-locking; the frozen
build is the gate that keeps the mirror honest about the
dependency set.

## The scaffold's vendored capability references were dropped

`.agents/skills/capability-workflows/references/*` (the .mdx guide
documents) are regenerable with the `mistral` CLI. They are not in
this repo on purpose: ADR-2026-11-16-001 records the drop. If a
guide doc is needed, regenerate it; do not re-vendor and do not
edit the regenerated copies by hand. The SKILL.md and the
`scripts/` lint rules stay, because the semgrep rules target
`scripts/linting/rules` by path.

## urllib capitalizes header names internally

`urllib.request.Request.headers` stores `PRIVATE-TOKEN` as
`Private-token`. Tests that read the header dict must compare
case-insensitively. Recorded in
`apps/worker/tests/test_gitlab_logic.py` + `test_private_token_header_present`.

## No git remote with credentials in the agent environment

The push flow is connector dual-write (GitLab add_commit, GitHub
push_files) with content parity, not a git push. Consequence: no
commit SHAs are ever identical across hosts, and branch protection
or tag rules on the mirror cannot be exercised through this flow.
See [ADR-2026-11-16-001](adr/ADR-2026-11-16-001.md).

## Upstream scaffold files are exempt from the ASCII rule

Two scaffold-generated files contain em-dashes (a UTF-8 dash):
`.agents/skills/capability-workflows/SKILL.md` (several) and
`packages/py/utils/src/utils/logging.py` (line 45). The ASCII-only
rule in AGENTS.md applies to files authored in this repo. Scaffold
bytes are kept verbatim: mutating them would churn against every
regeneration with `mistral workflows init`. Do not "fix" them.

