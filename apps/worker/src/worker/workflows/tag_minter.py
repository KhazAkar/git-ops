"""tag_minter: mint a GitLab tag on a project, or report an existing one.

Contract (ADR-2026-11-16-002):
- Input is ONE Pydantic model (HTTP API schema comes from its hints).
- All network I/O lives in activities; each operation is its own
  activity so retries are per-operation, not per-run.
- create_tag runs with retry_policy_max_attempts=1: a write must
  never replay after a partial failure.
- The PAT is read inside each activity. It never crosses the
  workflow boundary and never appears in any output.
- dry_run defaults to True: an unspecified caller gets a safe run.
- Existing tag = idempotent success, not an error.
"""

from __future__ import annotations

import asyncio

import mistralai.workflows as workflows
from pydantic import BaseModel

from worker import gitlab


class TagMinterInput(BaseModel):
    """One model in, per the platform schema convention."""

    project_path: str
    tag_name: str
    ref: str = "main"
    message: str | None = None
    dry_run: bool = True


class TagMinterOutput(BaseModel):
    """Deterministic summary; buildable identically on every path."""

    tag_name: str
    created: bool
    existing: bool
    dry_run: bool
    commit_sha: str
    web_url: str
    detail: str


@workflows.activity()
async def resolve_project(project_path: str) -> dict:
    token = gitlab.pat()
    return await asyncio.to_thread(gitlab.resolve_project, project_path, token)


@workflows.activity()
async def get_commit(project_id: int, ref: str) -> dict:
    token = gitlab.pat()
    return await asyncio.to_thread(gitlab.get_commit, project_id, ref, token)


@workflows.activity()
async def get_tag(project_id: int, tag_name: str) -> dict | None:
    token = gitlab.pat()
    return await asyncio.to_thread(gitlab.get_tag, project_id, tag_name, token)


@workflows.activity(retry_policy_max_attempts=1)
async def create_tag(
    project_id: int, tag_name: str, ref: str, message: str | None
) -> dict:
    token = gitlab.pat()
    return await asyncio.to_thread(
        gitlab.create_tag, project_id, tag_name, ref, message, token
    )


@workflows.workflow.define(name="tag_minter")
class TagMinterWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, data: TagMinterInput) -> TagMinterOutput:
        # Pure validation, deterministic, safe directly in workflow code.
        gitlab.validate_tag_name(data.tag_name)
        gitlab.validate_project_path(data.project_path)

        project = await resolve_project(data.project_path)
        commit = await get_commit(project["id"], data.ref)

        existing = await get_tag(project["id"], data.tag_name)
        if existing is not None:
            return TagMinterOutput(
                tag_name=data.tag_name,
                created=False,
                existing=True,
                dry_run=data.dry_run,
                commit_sha=commit["id"],
                web_url=project["web_url"] + "/-/tags/" + data.tag_name,
                detail=(
                    "tag already exists on " + data.ref + " @ "
                    + commit["id"][:12] + " (" + commit["title"] + ")"
                ),
            )

        if data.dry_run:
            return TagMinterOutput(
                tag_name=data.tag_name,
                created=False,
                existing=False,
                dry_run=True,
                commit_sha=commit["id"],
                web_url=project["web_url"] + "/-/tags/" + data.tag_name,
                detail=(
                    "would create tag on " + data.ref + " @ "
                    + commit["id"][:12] + " (" + commit["title"] + ")"
                ),
            )

        await create_tag(project["id"], data.tag_name, data.ref, data.message)
        return TagMinterOutput(
            tag_name=data.tag_name,
            created=True,
            existing=False,
            dry_run=False,
            commit_sha=commit["id"],
            web_url=project["web_url"] + "/-/tags/" + data.tag_name,
            detail=(
                "tag created on " + data.ref + " @ "
                + commit["id"][:12] + " (" + commit["title"] + ")"
            ),
        )
