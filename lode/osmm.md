# OSMM - git-ops

Latest dated pass. The developer judges content; the agent runs
the checklist.

## 2026-11-16 (initial pass, at repo creation)

| Area | State | Note |
| --- | --- | --- |
| Memory | pass | lode/ complete: map, summary, terminology, practices, quirks, 2 ADRs + TASKLISTs, 1 backlog item, architecture/system.md |
| ADRs before code | pass | ADR-001 doctrine and ADR-002 tag_minter written before the workflow code landed |
| Executable specs | pass | every ADR Verification assertion maps to a unit test or a marked deployment smoke; 11/11 green |
| Model files | pass | every ADR and architecture file carries its mermaid model in a Model section |
| Contracts bound | pass | AGENTS.md present from the LodeStack template |
| ASCII discipline | pass | all generated files ASCII-only |
| Traceability | partial | lode-map links all decisions and plans; grow as files land |
| Release readiness | partial | uv.lock delegated (dev-side), deployment and smoke pending |

Open items are tracked in the TASKLISTs and the quirks file.
