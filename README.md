# git-ops

Gated git side effects as durable Mistral Workflows. Chat agents
get hands for fleet git operations; the credentials stay in the
deployment, the judgment stays with the developer.

First workflow: `tag_minter`, the one gap the GitLab chat
connector has. It mints a release tag on a GitLab project, or
reports the tag already exists, behind a dry_run default that
makes every unspecified call safe.

## Layout

```
apps/worker/           the workflow app
  src/worker/gitlab.py           stdlib GitLab REST plumbing
  src/worker/workflows/          workflows (auto-discovered)
  tests/                         stdlib unit tests
packages/py/           scaffold support packages
deploy/docker/         the worker image (platform-built)
lode/                  project memory (start: lode/lode-map.md)
```

Project memory and decisions live in `lode/`; start at
`lode/lode-map.md`. The repo doctrine (GitLab primary, GitHub
mirror, secret binding) is `lode/adr/ADR-2026-11-16-001.md`.

## Local development

```
git clone git@gitlab.com:r3xxar/git-ops.git
cd git-ops
bash tools/uv.sh sync
cp .env.example .env    # fill GITLAB_TAG_PAT
mistral apps dev
```

Tests run on a bare interpreter, no credentials, no network:

```
cd apps/worker
python3 -m unittest discover tests
```

## Deployment

The worker deploys as `git-ops-worker`, built from the GitHub
mirror (`KhazAkar/git-ops`). The tag-scoped secret
`gitlab_tag_pat` binds to `GITLAB_TAG_PAT` at boot; the value
never lives in this repo.

## License

GPL-3.0, see LICENSE.
