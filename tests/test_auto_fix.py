import json
import os

os.environ["LLM_PROVIDER"] = "fake"

from fastapi.testclient import TestClient

from app.main import app
from app.services import ai_service as ai_module
from app.services.diagnose_service import diagnose_service
from app.services.fix_service import fix_service
from app.services.web_search_service import web_search_service

client = TestClient(app)


def _git(workspace, *args):
    import subprocess

    proc = subprocess.run(
        ["git", "-C", str(workspace), *args],
        capture_output=True,
        text=True,
        check=False,
    )

    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _init_git_repo(tmp_path, filename="greeter.ts", content=None):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@reyvin.dev")
    _git(tmp_path, "config", "user.name", "Reyvin Test")

    if content is None:
        content = (
            "export function greet(name: string) {\n"
            "  return name.toUpperCase()\n"
            "}\n"
        )

    (tmp_path / filename).write_text(content)

    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "initial")

    return content


GREETER_DIFF = (
    "```diff\n"
    "--- a/greeter.ts\n"
    "+++ b/greeter.ts\n"
    "@@ -1,3 +1,3 @@\n"
    " export function greet(name: string) {\n"
    "-  return name.toUpperCase()\n"
    "+  return String(name).toUpperCase()\n"
    " }\n"
    "```"
)


def test_web_search_service_detects_library_errors():

    assert web_search_service.needs_search(
        "App must use Google Play Billing Library version 8.0.0 or later"
    )

    assert not web_search_service.needs_search("TypeError: x is not a function")


def test_web_search_service_cleans_and_returns_results(monkeypatch):

    web_search_service._search_func = lambda query, limit: [
        {
            "title": "Play Billing 8 in Purchases SDK v9",
            "href": "https://example.com/blog",
            "body": "Google Play Billing Library 8 support",
        },
        {
            "title": "Broken",
            "href": "",
            "body": "",
        },
        "not a dict",
    ]

    try:
        results = web_search_service.search(
            web_search_service.build_query(
                "Google Play Billing Library version 8.0.0 required"
            )
        )
    finally:
        web_search_service._search_func = None

    assert len(results) == 1

    assert results[0]["url"] == "https://example.com/blog"


def test_diagnose_includes_web_evidence_for_library_errors(monkeypatch):

    captured = {}

    def fake_chat(model, message, thinking):
        captured["message"] = message

        return {
            "response": json.dumps(
                {
                    "root_cause": "outdated billing library",
                    "location": "package.json",
                    "explanation": "version bump needed",
                    "fixes": [
                        {
                            "description": "bump version",
                            "file": "package.json",
                            "symbol": "",
                            "suggestion": "update version",
                        },
                    ],
                }
            ),
            "model": "qwen",
            "thinking": False,
            "elapsed_ms": 1,
        }

    web_search_service._search_func = lambda query, limit: [
        {
            "title": "Play Billing 8 support",
            "url": "https://example.com/blog",
            "body": "Purchases SDK v9 bundles billing 8",
        },
    ]

    try:
        monkeypatch.setattr(
            ai_module.ai_service,
            "chat",
            fake_chat,
        )

        diagnose_service.diagnose(
            "App must use Google Play Billing Library version 8.0.0 or later",
            file="",
            model="qwen",
            thinking=False,
        )
    finally:
        web_search_service._search_func = None

    message = captured["message"]

    assert "WEB EVIDENCE" in message

    assert "Play Billing 8 support" in message

    assert "primary evidence" in message


def test_diagnose_skips_web_search_for_plain_errors(monkeypatch):

    searched = []

    def fake_chat(model, message, thinking):
        return {
            "response": json.dumps(
                {
                    "root_cause": "type error",
                    "location": "greeter.ts:2",
                    "explanation": "x",
                    "fixes": [],
                }
            ),
            "model": "qwen",
            "thinking": False,
            "elapsed_ms": 1,
        }

    def fake_search(query, limit):
        searched.append(query)

        return []

    monkeypatch.setattr(ai_module.ai_service, "chat", fake_chat)

    monkeypatch.setattr(web_search_service, "_search_func", fake_search)

    diagnose_service.diagnose(
        "TypeError: name.toUpperCase is not a function",
        file="",
        model="qwen",
        thinking=False,
    )

    assert not searched


def test_fix_service_applies_diff_with_git_checkpoint(tmp_path, monkeypatch):

    project_id = "fix-apply"
    _init_git_repo(tmp_path)

    client.post(
        "/api/v1/analyze",
        json={"project_id": project_id, "workspace": str(tmp_path)},
    )

    def fake_chat(model, message, thinking):
        return {
            "response": GREETER_DIFF,
            "model": "qwen",
            "thinking": False,
            "elapsed_ms": 1,
        }


    monkeypatch.setattr(
        ai_module.ai_service,
        "chat",
        fake_chat,
    )

    result = fix_service.apply(
        {
            "description": "guard the input type",
            "file": "greeter.ts",
            "symbol": "greet",
            "suggestion": "wrap in String()",
        },
        project=project_id,
        model="qwen",
        thinking=False,
    )

    assert result["applied"] is True

    assert result["method"] == "diff"

    assert len(result["checkpoint_commit"]) == 40

    assert result["fix_commit"]

    assert result["fix_commit"] != result["checkpoint_commit"]

    content = (tmp_path / "greeter.ts").read_text()

    assert "String(name).toUpperCase()" in content

    assert "+  return String(name).toUpperCase()" in result["diff"]

    _, log, _ = _git(tmp_path, "log", "--oneline", "-1")

    assert "reyvin: apply fix" in log


def test_fix_service_reverts_to_checkpoint(tmp_path, monkeypatch):

    project_id = "fix-revert"
    original = _init_git_repo(tmp_path)

    client.post(
        "/api/v1/analyze",
        json={"project_id": project_id, "workspace": str(tmp_path)},
    )

    def fake_chat(model, message, thinking):
        return {
            "response": GREETER_DIFF,
            "model": "qwen",
            "thinking": False,
            "elapsed_ms": 1,
        }


    monkeypatch.setattr(
        ai_module.ai_service,
        "chat",
        fake_chat,
    )

    fix_service.apply(
        {
            "description": "guard the input type",
            "file": "greeter.ts",
            "symbol": "greet",
            "suggestion": "wrap in String()",
        },
        project=project_id,
        model="qwen",
        thinking=False,
    )

    assert "String(name)" in (tmp_path / "greeter.ts").read_text()

    revert = fix_service.revert(project_id)

    assert revert["reverted"] is True

    assert (tmp_path / "greeter.ts").read_text() == original


def test_apply_fix_endpoint_returns_applied(tmp_path, monkeypatch):

    project_id = "fix-api"
    _init_git_repo(tmp_path)

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": project_id, "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200


    monkeypatch.setattr(
        ai_module.ai_service,
        "chat",
        lambda model, message, thinking: {
            "response": GREETER_DIFF,
            "model": "qwen",
            "thinking": False,
            "elapsed_ms": 1,
        },
    )

    r = client.post(
        "/api/v1/apply-fix",
        json={
            "fix": {
                "description": "guard the input type",
                "file": "greeter.ts",
                "symbol": "greet",
                "suggestion": "wrap in String()",
            },
            "project": project_id,
        },
    )

    assert r.status_code == 200

    data = r.json()

    assert data["applied"] is True

    assert data["file"] == "greeter.ts"

    assert "String(name)" in (tmp_path / "greeter.ts").read_text()


def test_fix_service_rejects_non_git_workspace(tmp_path):

    project_id = "fix-no-git"

    (tmp_path / "a.ts").write_text("export const a = 1\n")

    client.post(
        "/api/v1/analyze",
        json={"project_id": project_id, "workspace": str(tmp_path)},
    )

    from app.services.fix_service import fix_service as service

    try:
        service.apply(
            {
                "description": "x",
                "file": "a.ts",
                "symbol": "",
                "suggestion": "y",
            },
            project=project_id,
            model="qwen",
            thinking=False,
        )

        raised = False
    except ValueError:
        raised = True

    assert raised