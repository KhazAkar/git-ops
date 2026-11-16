# Lode Map - git-ops

Index of durable project memory. Start here, then follow links.

## Purpose

One place for the fleet's gated git side effects that no chat
connector covers. Today: minting GitLab release tags with a
tag-scoped PAT held by a Mistral Workflow deployment.

## Decision index

- [ADR-2026-11-16-001](adr/ADR-2026-11-16-001.md) - GitLab primary,
  GitHub mirror doctrine (Accepted; point 3 superseded by
  ADR-2026-11-16-003)
- [ADR-2026-11-16-002](adr/ADR-2026-11-16-002.md) - tag_minter
  workflow specification (Accepted)
- [ADR-2026-11-16-003](adr/ADR-2026-11-16-003.md) - automated
  mirror: schedule-driven pull (Accepted)
- [TASKLIST-ADR-2026-11-16-001](adr/TASKLIST-ADR-2026-11-16-001.md)
- [TASKLIST-ADR-2026-11-16-002](adr/TASKLIST-ADR-2026-11-16-002.md)
- [TASKLIST-ADR-2026-11-16-003](adr/TASKLIST-ADR-2026-11-16-003.md)

## Plan and backlog

- [BL-2026-11-16-001](plan/BL-2026-11-16-001.md) - watch_pipeline
  workflow (Backlog)

## Architecture

- [architecture/system.md](architecture/system.md) - deployment,
  secret binding, mirror flow

## Reference

- [summary.md](summary.md) - what this project is
- [terminology.md](terminology.md) - names and verbs
- [practices.md](practices.md) - tooling, setup, running, testing
- [quirks-and-gotchas/README.md](quirks-and-gotchas/README.md)
- [osmm.md](osmm.md) - latest OSMM pass
