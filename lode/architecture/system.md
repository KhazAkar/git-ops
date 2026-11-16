# Architecture - git-ops system

System model: how a chat-gated tag request becomes a tag on GitLab.

## Model

```mermaid
flowchart LR
    subgraph chat["Chat (Vibe session)"]
        dev[Developer gate]
        agent[Agent]
    end
    subgraph platform["Mistral platform"]
        exec[execute_workflow]
        dep["git-ops-worker deployment<br/>(built from GitHub mirror)"]
        secret["Secret gitlab_tag_pat<br/>bound to env GITLAB_TAG_PAT"]
    end
    subgraph gitlab["GitLab"]
        repo["r3xxar/* projects"]
        tag["Release tag vX.Y.Z"]
    end
    gh["GitHub mirror<br/>KhazAkar/git-ops"]
    gl["GitLab primary<br/>r3xxar/git-ops"]

    dev -->|intent| agent
    agent -->|presents plan| dev
    agent -->|gated call, expected_revision| exec
    exec --> dep
    secret ---|boot binding| dep
    dep -->|validate, resolve, check| repo
    dep -->|mint (not dry_run)| tag

    gl -->|"connector dual-write (parity)"| gh
    gh -->|"build source"| dep
```

## Elements

- **Developer gate** - every real mint is approved in chat first.
  The deployment provides hands, not judgment.
- **Deployment** - `git-ops-worker`, a durable Python process.
  Workflow code auto-discovered from `worker.workflows`.
- **Secret binding** - name-only in config, value injected at boot.
  The PAT exists only inside the deployment environment and inside
  each activity call, never in a workflow boundary, an output, or
  a log line.
- **Primary and mirror** - commits land on GitLab `main`, are
  dual-written to GitHub `main`, and the deployment pins a GitHub
  revision. The mirror never leads.

## Connections and dependencies

- Chat agent depends on the deployed revision being the revision
  it reviewed: pin with `expected_revision` on every call.
- The Docker build depends on `uv.lock` (frozen sync). Dependency
  changes without a re-lock break the deployment build, loudly.
- tag_minter depends only on the GitLab REST v4 API and the
  standard library; see [ADR-2026-11-16-002](../adr/ADR-2026-11-16-002.md).
