# Summary - git-ops

git-ops is a Mistral Workflows application repo. It runs durable
Python worker deployments that perform gated git side effects on
behalf of chat agents, using credentials that the agents themselves
never hold.

## The problem it solves

The GitLab connector used from chat can create repositories and
commits but cannot create tags. Tags gate releases (pipeline on
tag, binaries). The chat sandbox also cannot hold user secrets:
workspace secrets are bound to deployments, not to agent
environments. So the one action that is missing needs both a
credential and a place where the credential can live safely.

## The answer

A worker deployment on the Mistral platform holds the tag-scoped
GitLab PAT as a bound secret. Chat agents call the deployed
workflow through the connector's execute_workflow. The workflow
validates, resolves, checks for existence, and mints or declines.
The developer gates every real mint in chat; the deployment only
provides the hands.

## Shape

Monorepo scaffolded by `mistral workflows init`:

- `apps/worker` - the workflow app; workflow code in
  `src/worker/workflows/`, GitLab plumbing in
  `src/worker/gitlab.py`, stdlib unit tests in `tests/`
- `packages/py` - scaffold support packages (cli, env, utils)
- `deploy/docker` - the worker image, built by the platform from
  the GitHub mirror
- `lode/` - this memory

Current workflow: `tag_minter` (ADR-2026-11-16-002). The backlog
holds `watch_pipeline` (BL-2026-11-16-001).

## Doctrine

GitLab is the primary, GitHub is the derived mirror. See
[ADR-2026-11-16-001](adr/ADR-2026-11-16-001.md). Deployments build
from the mirror; the mirror never leads.
