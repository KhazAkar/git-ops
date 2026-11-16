# Terminology - git-ops

ELI5-level definitions. One word, one meaning.

- **git-ops** - this repo and its deployed worker. Not a generic
  term here: the name of the fleet's git side-effect service.
- **tag_minter** - the workflow that creates a GitLab release tag
  on a project, or reports that the tag exists. The only workflow
  today.
- **mint** - create a tag. A mint is a write; everything else the
  workflow does is read.
- **PAT** - personal access token. In this repo always the
  tag-scoped GitLab token, never a broader one.
- **tag-scoped PAT** - a GitLab access token whose scope is only
  write_repository, aimed at one group of projects. Its blast
  radius is one wrong tag, not one wrong force-push.
- **binding** - the deployment config stores the NAME of a secret,
  not its value. At boot the platform puts the value into the
  environment variable. Complete-set semantics: all bound secrets
  resolve or the deployment fails to serve.
- **dry_run** - a run that validates and reads, but never writes.
  The default mode of tag_minter. The christening smoke is always
  a dry_run.
- **christening smoke** - the first execute_workflow call after a
  deployment, always dry_run, proving the PAT binds and the
  workflow answers.
- **primary** - GitLab, `r3xxar/git-ops`. Where commits land first
  and where review happens.
- **mirror** - GitHub, `KhazAkar/git-ops`. A derived copy that
  exists because managed deployments build from GitHub. It never
  leads; parity is checked, not assumed.
- **parity** - the state where mirror file contents equal primary
  file contents. Content parity, not SHA parity: the two hosts
  compute different SHAs for the same bytes.
- **connector dual-write** - the push step writes the same file
  contents to both hosts through their connectors, because no git
  remote with credentials exists in the agent environment.
