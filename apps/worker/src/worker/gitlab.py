"""GitLab REST operations for the tag_minter workflow.

This module holds the pure validation and HTTP plumbing so tests
run with the standard library alone, without the workflows SDK.
The workflow activities in worker.workflows.tag_minter call these
functions through asyncio.to_thread, so the sync urllib calls never
block the worker event loop.

The PAT is read from the GITLAB_TAG_PAT environment variable inside
each operation. It never appears in a message, a return value, or
an exception, on any path.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://gitlab.com/api/v4"
PAT_ENV_VAR = "GITLAB_TAG_PAT"
PAT_BINDING_HINT = (
    "GITLAB_TAG_PAT is not set; bind the workspace secret "
    "gitlab_tag_pat to it on the deployment"
)

_TAG_NAME_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
_PROJECT_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_REQUEST_TIMEOUT_SECONDS = 10.0

# Patchable in tests: points at urllib.request.urlopen.
_urlopen = urllib.request.urlopen


class GitLabError(Exception):
    """A GitLab operation failed. The message never carries the PAT."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def pat() -> str:
    """Return the tag-scoped PAT from the environment, or fail loudly."""
    value = os.environ.get(PAT_ENV_VAR, "").strip()
    if not value:
        raise GitLabError(PAT_BINDING_HINT)
    return value


def validate_tag_name(tag_name: str) -> None:
    """Require the fleet tag convention: vX.Y.Z, ASCII digits and dots."""
    if not _TAG_NAME_PATTERN.match(tag_name):
        raise GitLabError(
            "tag_name must match vX.Y.Z (for example v0.1.3), got: "
            + repr(tag_name)
        )


def validate_project_path(project_path: str) -> None:
    """Require a single-slash namespace/project path."""
    if not _PROJECT_PATH_PATTERN.match(project_path):
        raise GitLabError(
            "project_path must look like namespace/project "
            "(for example r3xxar/lodectl), got: " + repr(project_path)
        )


def _request(method: str, path: str, token: str, body: dict | None = None) -> dict:
    """Run one GitLab API request and return the parsed JSON object.

    Raises GitLabError with a clean, PAT-free message on any failure.
    """
    url = API_BASE + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"PRIVATE-TOKEN": token, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        raise _http_error(error) from None
    except OSError as error:
        # Class name only: the string form can embed the URL, which is
        # fine, but never the headers. Keep it short and predictable.
        raise GitLabError(
            "GitLab unreachable (" + type(error).__name__ + "), path: " + path
        ) from None


def _http_error(error: urllib.error.HTTPError) -> GitLabError:
    """Map an HTTPError to a clean message. The PAT never leaks."""
    if error.code == 401:
        return GitLabError(
            "GitLab rejected the PAT (401): check that the tag-scoped "
            "token is valid and not expired",
            status=401,
        )
    return GitLabError(
        "GitLab returned HTTP " + str(error.code) + " for path: "
        + urllib.parse.urlsplit(error.url).path,
        status=error.code,
    )


def resolve_project(project_path: str, token: str) -> dict:
    """Look up a project by path; return {"id": int, "web_url": str}."""
    quoted = urllib.parse.quote(project_path, safe="")
    try:
        found = _request("GET", "/projects/" + quoted, token)
    except GitLabError as error:
        if error.status == 404:
            raise GitLabError("project not found: " + project_path, status=404) from None
        raise
    return {"id": found["id"], "web_url": found["web_url"]}


def get_commit(project_id: int, ref: str, token: str) -> dict:
    """Resolve a ref to a commit; return {"id": sha, "title": str}."""
    quoted = urllib.parse.quote(ref, safe="")
    try:
        commit = _request(
            "GET", "/projects/" + str(project_id) + "/repository/commits/" + quoted, token
        )
    except GitLabError as error:
        if error.status == 404:
            raise GitLabError(
                "ref not found: " + ref + " in project " + str(project_id), status=404
            ) from None
        raise
    return {"id": commit["id"], "title": commit["title"]}


def get_tag(project_id: int, tag_name: str, token: str) -> dict | None:
    """Return the tag object, or None when the tag does not exist."""
    quoted = urllib.parse.quote(tag_name, safe="")
    try:
        return _request(
            "GET", "/projects/" + str(project_id) + "/repository/tags/" + quoted, token
        )
    except GitLabError as error:
        if error.status == 404:
            return None
        raise


def create_tag(
    project_id: int, tag_name: str, ref: str, message: str | None, token: str
) -> dict:
    """Create the tag; return {"name", "commit_id", "detail-free extras"}.

    A non-empty message makes the tag annotated; without one the tag
    is lightweight, matching `git tag vX.Y.Z` on the command line.
    """
    body: dict = {"tag_name": tag_name, "ref": ref}
    if message:
        body["message"] = message
    created = _request(
        "POST", "/projects/" + str(project_id) + "/repository/tags", token, body
    )
    return {
        "name": created["name"],
        "commit_id": created["commit"]["id"],
        "message": created.get("message"),
    }
