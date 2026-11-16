"""Unit tests for worker.gitlab, the pure plumbing behind tag_minter.

One test per ADR-2026-11-16-002 Verification assertion marked [unit].
The flow assertions (exists / dry_run / create) are covered by the
deployment smoke run marked [deployment] in the ADR: they need the
workflows SDK and a live PAT, neither of which exists in this
test environment.

Runs with the standard library alone: no pytest, no pydantic, no
SDK. The fake transport patches gitlab._urlopen, so no socket is
ever opened.
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker import gitlab  # noqa: E402

TOKEN = "glpat-fake-token-value"


class FakeResponse:
    """Minimal stand-in for the object urllib.request.urlopen returns."""

    def __init__(self, payload: dict, status: int = 200) -> None:
        self._buffer = io.BytesIO(json.dumps(payload).encode())
        self.status = status

    def read(self) -> bytes:
        return self._buffer.read()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class FakeTransport:
    """Records the last request; answers from a scripted queue."""

    def __init__(self) -> None:
        self.requests: list[urllib.request.Request] = []
        self.queue: list[object] = []

    def __call__(self, request: urllib.request.Request, timeout: float | None = None):
        self.requests.append(request)
        if not self.queue:
            raise AssertionError("unexpected request: " + request.full_url)
        item = self.queue.pop(0)
        if isinstance(item, urllib.error.HTTPError):
            raise item
        return item

    @property
    def last(self) -> urllib.request.Request:
        return self.requests[-1]

    def enqueue_json(self, payload: dict, status: int = 200) -> None:
        self.queue.append(FakeResponse(payload, status))

    def enqueue_http_error(self, status: int, url: str) -> None:
        error = urllib.error.HTTPError(
            url=url, code=status, msg="err", hdrs={}, fp=io.BytesIO(b"{}")
        )
        self.queue.append(error)


class GitLabTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = FakeTransport()
        self._original_urlopen = gitlab._urlopen
        gitlab._urlopen = self.transport
        self._original_pat = os.environ.get(gitlab.PAT_ENV_VAR)
        os.environ[gitlab.PAT_ENV_VAR] = TOKEN

    def tearDown(self) -> None:
        gitlab._urlopen = self._original_urlopen
        if self._original_pat is None:
            os.environ.pop(gitlab.PAT_ENV_VAR, None)
        else:
            os.environ[gitlab.PAT_ENV_VAR] = self._original_pat

    def http_error(self, status: int, path: str) -> urllib.error.HTTPError:
        return urllib.error.HTTPError(
            url=gitlab.API_BASE + path,
            code=status,
            msg="err",
            hdrs={},
            fp=io.BytesIO(b"{}"),
        )


class TestValidation(GitLabTestCase):
    def test_invalid_tag_name_rejected(self) -> None:
        for bad in ("0.1.3", "v1.2", "v1.2.3.4", "v1.2.x", "latest", ""):
            with self.assertRaises(gitlab.GitLabError):
                gitlab.validate_tag_name(bad)
        gitlab.validate_tag_name("v0.1.3")
        gitlab.validate_tag_name("v12.34.56")

    def test_invalid_project_path_rejected(self) -> None:
        for bad in ("lodectl", "r3xxar/", "/lodectl", "a/b/c", "", "sp ace/x"):
            with self.assertRaises(gitlab.GitLabError):
                gitlab.validate_project_path(bad)
        gitlab.validate_project_path("r3xxar/lodectl")


class TestPat(GitLabTestCase):
    def test_missing_pat_raises_binding_hint(self) -> None:
        os.environ.pop(gitlab.PAT_ENV_VAR, None)
        with self.assertRaises(gitlab.GitLabError) as caught:
            gitlab.pat()
        self.assertIn("GITLAB_TAG_PAT", str(caught.exception))
        self.assertIn("gitlab_tag_pat", str(caught.exception))


class TestRequests(GitLabTestCase):
    def test_private_token_header_present(self) -> None:
        self.transport.enqueue_json({"id": 42, "web_url": "https://x/y"})
        gitlab.resolve_project("r3xxar/lodectl", TOKEN)
        # urllib capitalizes header names internally, so compare case-insensitively.
        headers = {key.lower(): value for key, value in self.transport.last.headers.items()}
        self.assertEqual(headers["private-token"], TOKEN)

    def test_401_message_excludes_pat_value(self) -> None:
        self.transport.enqueue_http_error(401, gitlab.API_BASE + "/projects/x")
        with self.assertRaises(gitlab.GitLabError) as caught:
            gitlab._request("GET", "/projects/x", TOKEN)
        message = str(caught.exception)
        self.assertIn("401", message)
        self.assertNotIn(TOKEN, message)

    def test_project_404(self) -> None:
        self.transport.enqueue_http_error(404, gitlab.API_BASE + "/projects/x")
        with self.assertRaises(gitlab.GitLabError) as caught:
            gitlab.resolve_project("r3xxar/nope", TOKEN)
        self.assertIn("project not found", str(caught.exception))

    def test_ref_404(self) -> None:
        self.transport.enqueue_http_error(404, gitlab.API_BASE + "/p/c")
        with self.assertRaises(gitlab.GitLabError) as caught:
            gitlab.get_commit(7, "ghost-branch", TOKEN)
        self.assertIn("ref not found", str(caught.exception))

    def test_get_tag_404_returns_none(self) -> None:
        self.transport.enqueue_http_error(404, gitlab.API_BASE + "/p/t")
        self.assertIsNone(gitlab.get_tag(7, "v9.9.9", TOKEN))

    def test_create_tag_post_body_and_method(self) -> None:
        self.transport.enqueue_json(
            {
                "name": "v0.1.3",
                "message": None,
                "commit": {"id": "deadbeefcafe"},
            }
        )
        result = gitlab.create_tag(7, "v0.1.3", "main", None, TOKEN)
        request = self.transport.last
        self.assertEqual(request.get_method(), "POST")
        body = json.loads(request.data.decode())
        self.assertEqual(body, {"tag_name": "v0.1.3", "ref": "main"})
        self.assertEqual(result["name"], "v0.1.3")
        self.assertEqual(result["commit_id"], "deadbeefcafe")

    def test_create_tag_message_makes_annotated_body(self) -> None:
        self.transport.enqueue_json(
            {"name": "v0.1.3", "message": "note", "commit": {"id": "abc"}}
        )
        gitlab.create_tag(7, "v0.1.3", "main", "note", TOKEN)
        body = json.loads(self.transport.last.data.decode())
        self.assertEqual(
            body, {"tag_name": "v0.1.3", "ref": "main", "message": "note"}
        )

    def test_project_path_is_url_quoted(self) -> None:
        self.transport.enqueue_json({"id": 1, "web_url": "https://x/y"})
        gitlab.resolve_project("r3xxar/lodectl", TOKEN)
        self.assertIn("/projects/r3xxar%2Flodectl", self.transport.last.full_url)


if __name__ == "__main__":
    unittest.main()
