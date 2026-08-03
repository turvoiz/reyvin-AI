import json
import os

os.environ["LLM_PROVIDER"] = "fake"

from fastapi.testclient import TestClient

from app.main import app
from app.workspace.cache import WorkspaceCache
from app.workspace.context.context_assembler import context_assembler
from app.workspace.context.context_compressor import context_compressor
from app.workspace.context.context_formatter import context_formatter
from app.workspace.planner.workspace_planner import workspace_planner

client = TestClient(app)


def test_reload():

    r = client.post("/api/v1/workspace/reload")

    assert r.status_code == 200


def test_explain():

    r = client.get(
        "/api/v1/workspace/explain/AIService.chat"
    )

    assert r.status_code == 200

    data = r.json()

    assert data["symbol"] == "AIService.chat"

    assert "answer" in data


def test_review():

    r = client.get(
        "/api/v1/workspace/review/AIService.chat"
    )

    assert r.status_code == 200

    review = r.json()["review"]

    assert "summary" in review

    assert "strengths" in review

    assert "weaknesses" in review


def test_knowledge():

    r = client.get(
        "/api/v1/workspace/knowledge/AIService.chat"
    )

    assert r.status_code == 200

    data = r.json()

    assert "symbol" in data

    assert "calls" in data

    assert "callers" in data

    assert "impact" in data


def test_impact():

    r = client.get(
        "/api/v1/workspace/impact/AIService.chat"
    )

    assert r.status_code == 200

    data = r.json()

    assert "affected_symbols" in data

def test_search():

    r = client.get(
        "/api/v1/workspace/search?q=chat"
    )

    assert r.status_code == 200

    data = r.json()

    assert len(data) > 0

    assert "symbol" in data[0]

    assert "score" in data[0]


def test_ask_with_unknown_symbol_returns_safe_response():

    r = client.post(
        "/api/v1/workspace/ask",
        json={"question": "Explain ZyqxwvUnmatchedSymbol"},
    )

    assert r.status_code == 200
    assert r.json()["answer"] == "Saya tidak menemukan symbol yang dimaksud."


def test_ask_with_known_symbol_runs_ai_pipeline():

    r = client.post(
        "/api/v1/workspace/ask",
        json={"question": "Explain AIService.chat"},
    )

    assert r.status_code == 200
    assert r.json()["answer"] == "FAKE RESPONSE"


def test_explain_with_unknown_symbol_returns_safe_response():

    r = client.get(
        "/api/v1/workspace/explain/ZyqxwvUnmatchedSymbol"
    )

    assert r.status_code == 200
    assert r.json() == {
        "symbol": "ZyqxwvUnmatchedSymbol",
        "error": "Symbol not found",
    }


def test_review_with_unknown_symbol_returns_safe_response():

    r = client.get(
        "/api/v1/workspace/review/ZyqxwvUnmatchedSymbol"
    )

    assert r.status_code == 200
    assert r.json() == {
        "symbol": "ZyqxwvUnmatchedSymbol",
        "review": {
            "summary": "Symbol not found",
            "strengths": [],
            "findings": [],
        },
    }


def test_planner_detects_intent_and_matches_qualified_symbol():

    class Cache:
        def symbols(self):
            return {
                "AIService.chat": {
                    "name": "AIService.chat",
                    "type": "method",
                },
            }

    plan = workspace_planner.plan(Cache(), "Trace AIService.chat")

    assert plan == {
        "intent": "trace",
        "symbols": ["AIService.chat"],
    }


def test_planner_rejects_low_confidence_fuzzy_match():

    class Cache:
        def symbols(self):
            return {
                "SymbolMatcher.match": {
                    "name": "SymbolMatcher.match",
                    "type": "method",
                },
            }

    plan = workspace_planner.plan(Cache(), "Explain ZyqxwvUnmatchedSymbol")

    assert plan["symbols"] == []


def test_context_formatting_preserves_impact_and_trace_evidence():

    context = {
        "symbol": {"name": "AIService.chat"},
        "source": "def chat(): pass",
        "calls": [{"call": "Provider.chat"}],
        "callers": [{"caller": "WorkspaceAIService.run"}],
        "impact": {
            "risk": "medium",
            "affected_symbols": ["WorkspaceAIService.run"],
            "affected_files": ["app/services/workspace_ai_service.py"],
        },
        "trace": {"Provider.chat": {}},
        "related_sources": [
            {
                "symbol": "Provider.chat",
                "type": "method",
                "source": "def chat(): pass",
            },
        ],
    }

    impact = context_compressor.compress(context, "impact")
    trace = context_compressor.compress(context, "trace")

    impact_formatted = context_formatter.format(impact)
    trace_formatted = context_formatter.format(trace)

    assert "RISK: medium" in impact_formatted
    assert "WorkspaceAIService.run" in impact_formatted
    assert "app/services/workspace_ai_service.py" in impact_formatted
    assert '"Provider.chat": {}' in trace_formatted
    assert "def chat(): pass" in trace_formatted


def test_context_assembler_filters_impact_sources_by_symbol_name():

    target = {
        "name": "Target.run",
        "type": "method",
        "class": "Target",
        "file": "target.py",
    }
    caller = {
        "name": "Caller.run",
        "type": "method",
        "class": "Caller",
        "file": "caller.py",
    }

    class Cache:
        def __init__(self):
            self.symbols = {target["name"]: target, caller["name"]: caller}
            self.knowledge_by_symbol = {
                target["name"]: {
                    "symbol": target,
                    "source": "def target(): pass",
                    "calls": [],
                    "callers": [{"caller": caller["name"]}],
                    "references": [],
                    "dependencies": [],
                    "impact": {
                        "affected_symbols": [caller["name"]],
                        "affected_files": [caller["file"]],
                        "risk": "low",
                    },
                    "trace": {},
                },
                caller["name"]: {
                    "symbol": caller,
                    "source": "def caller(): pass",
                    "calls": [],
                    "callers": [],
                    "references": [],
                    "dependencies": [],
                    "impact": {},
                    "trace": {},
                },
            }

        def get(self, symbol):
            return self.symbols.get(symbol)

        def knowledge(self, symbol):
            return self.knowledge_by_symbol.get(symbol)

        def context(self, symbol):
            return self.knowledge_by_symbol[symbol]["source"]

        def graph(self):
            return {"imports": {}, "reverse": {}}

    context = context_assembler.build(Cache(), target["name"], "impact")

    assert [source["symbol"] for source in context["related_sources"]] == [
        caller["name"],
    ]


def test_workspace_cache_rebuilds_changed_and_removed_files(tmp_path):

    source = tmp_path / "module.py"
    source.write_text("def first():\n    return 1\n")

    cache = WorkspaceCache()
    cache.load(str(tmp_path))

    assert "first" in cache.symbols()
    assert (tmp_path / ".workspace_snapshot.json").exists()

    source.write_text("def second():\n    return 2\n")

    changed = cache.rebuild()

    assert changed["rebuilt"] == ["module.py"]
    assert "first" not in cache.symbols()
    assert "second" in cache.symbols()

    source.unlink()

    removed = cache.rebuild()

    assert removed["rebuilt"] == ["module.py"]
    assert "second" not in cache.symbols()


def test_project_registry_indexes_typescript_workspace(tmp_path):

    (tmp_path / "web.ts").write_text(
        "import { helper } from './helper'\n"
        "export function greet(name: string) {\n"
        "  return helper(name)\n"
        "}\n"
    )
    (tmp_path / "helper.ts").write_text(
        "export const helper = (name: string) => name.toUpperCase()\n"
    )

    r = client.post(
        "/api/v1/workspace/projects",
        json={"project_id": "frontend", "workspace": str(tmp_path)},
    )

    assert r.status_code == 200
    assert r.json()["project_id"] == "frontend"
    assert r.json()["symbols"] == 2

    search = client.post(
        "/api/v1/workspace/search",
        json={"query": "greet", "project": "frontend"},
    )

    assert search.status_code == 200
    assert search.json()["symbol"]["file"] == "web.ts"

    graph = client.get("/api/v1/workspace/graph?project=frontend")

    assert graph.status_code == 200
    assert graph.json()["imports"]["web.ts"] == ["./helper"]


def test_unknown_project_returns_not_found_response():

    r = client.get("/api/v1/workspace/stats?project=missing")

    assert r.status_code == 404


def test_project_id_accepts_hyphens_and_underscores(tmp_path):

    (tmp_path / "module.py").write_text("def helper():\n    pass\n")

    for project_id in ("developer-api", "my_project", "my-project_v2"):

        r = client.post(
            "/api/v1/analyze",
            json={"project_id": project_id, "workspace": str(tmp_path)},
        )

        assert r.status_code == 200
        assert r.json()["project_id"] == project_id


def test_project_id_rejects_invalid_characters(tmp_path):

    (tmp_path / "module.py").write_text("def helper():\n    pass\n")

    for project_id in ("bad id", "path/here", "with@symbol", ""):

        r = client.post(
            "/api/v1/analyze",
            json={"project_id": project_id, "workspace": str(tmp_path)},
        )

        assert r.status_code == 422



def test_developer_api_analyzes_and_queries_project(tmp_path):

    (tmp_path / "service.py").write_text(
        "def process():\n"
        "    return 'ok'\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "developer-api", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200
    assert analyze.json()["symbols"] == 1

    symbol = client.get("/api/v1/symbol/process?project=developer-api")

    assert symbol.status_code == 200
    assert symbol.json()["file"] == "service.py"

    impact = client.get("/api/v1/impact/process?project=developer-api")

    assert impact.status_code == 200
    assert impact.json()["risk"] == "none"


def test_developer_api_requires_api_key_when_configured(tmp_path, monkeypatch):

    from app.core.settings import settings

    (tmp_path / "service.py").write_text("def process():\n    return 'ok'\n")

    monkeypatch.setattr(settings, "API_KEY", "secret-token")

    try:
        analyze = client.post(
            "/api/v1/analyze",
            json={"project_id": "auth-api", "workspace": str(tmp_path)},
        )

        assert analyze.status_code == 401

        analyze = client.post(
            "/api/v1/analyze",
            json={"project_id": "auth-api", "workspace": str(tmp_path)},
            headers={"X-API-Key": "secret-token"},
        )

        assert analyze.status_code == 200

        symbol = client.get("/api/v1/symbol/process?project=auth-api")

        assert symbol.status_code == 401

        symbol = client.get(
            "/api/v1/symbol/process?project=auth-api",
            headers={"X-API-Key": "wrong-token"},
        )

        assert symbol.status_code == 401

        symbol = client.get(
            "/api/v1/symbol/process?project=auth-api",
            headers={"X-API-Key": "secret-token"},
        )

        assert symbol.status_code == 200
        assert symbol.json()["file"] == "service.py"
    finally:
        monkeypatch.undo()


def test_developer_api_explains_selected_code(tmp_path):

    source = tmp_path / "module.py"
    source.write_text(
        "def greet(name: str) -> str:\n"
        "    return f'hello {name}'\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "code-api", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200

    selected = "return f'hello {name}'"

    r = client.post(
        "/api/v1/explain-code",
        json={
            "code": selected,
            "file": "module.py",
            "start_line": 1,
            "end_line": 2,
            "project": "code-api",
        },
    )

    assert r.status_code == 200

    data = r.json()

    assert data["code"] == selected
    assert data["answer"] == "FAKE RESPONSE"
    assert data["related_symbols"] == ["greet"]


def test_developer_api_explains_selected_code_without_symbol(tmp_path):

    r = client.post(
        "/api/v1/explain-code",
        json={
            "code": "print('hello')",
            "file": "",
            "start_line": 0,
            "end_line": 0,
            "project": "default",
        },
    )

    assert r.status_code == 200

    data = r.json()

    assert data["code"] == "print('hello')"
    assert data["answer"] == "FAKE RESPONSE"
    assert data["related_symbols"] == []


def test_developer_api_knowledge_and_search(tmp_path):

    (tmp_path / "service.py").write_text(
        "def process():\n"
        "    return 'ok'\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "nav-api", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200

    knowledge = client.get("/api/v1/knowledge/process?project=nav-api")

    assert knowledge.status_code == 200
    assert knowledge.json()["symbol"]["file"] == "service.py"
    assert knowledge.json()["calls"] == []
    assert knowledge.json()["callers"] == []

    search = client.get("/api/v1/search?q=proc&project=nav-api")

    assert search.status_code == 200
    assert search.json()[0]["symbol"] == "process"


def test_javascript_call_graph_links_cross_module_and_this_calls(tmp_path):

    (tmp_path / "helper.ts").write_text(
        "export const helper = (name: string) => name.toUpperCase()\n"
    )
    (tmp_path / "web.ts").write_text(
        "import { helper } from './helper'\n"
        "export function greet(name: string) {\n"
        "  return helper(name)\n"
        "}\n"
    )
    (tmp_path / "service.ts").write_text(
        "export class Service {\n"
        "  run() {\n"
        "    return this.work()\n"
        "  }\n"
        "  work() {\n"
        "    return 1\n"
        "  }\n"
        "}\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "js-graph", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200
    assert analyze.json()["symbols"] == 5

    greet = client.get("/api/v1/knowledge/greet?project=js-graph")

    assert greet.status_code == 200
    assert [c["call"] for c in greet.json()["calls"]] == ["helper"]

    helper = client.get("/api/v1/knowledge/helper?project=js-graph")

    assert helper.status_code == 200
    assert [c["caller"] for c in helper.json()["callers"]] == ["greet"]

    run = client.get("/api/v1/knowledge/Service.run?project=js-graph")

    assert run.status_code == 200
    assert [c["call"] for c in run.json()["calls"]] == ["Service.work"]

    work = client.get("/api/v1/knowledge/Service.work?project=js-graph")

    assert work.status_code == 200
    assert [c["caller"] for c in work.json()["callers"]] == ["Service.run"]


def test_javascript_call_graph_ignores_builtin_and_unresolved_calls(tmp_path):

    (tmp_path / "main.js").write_text(
        "function main() {\n"
        "  console.log('hi')\n"
        "  missingFunction()\n"
        "  return 1\n"
        "}\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "js-builtins", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200

    knowledge = client.get("/api/v1/knowledge/main?project=js-builtins")

    assert knowledge.status_code == 200
    assert knowledge.json()["calls"] == []


def test_architecture_explains_whole_repository(tmp_path):

    (tmp_path / "main.py").write_text(
        "from helper import run\n"
        "def main():\n"
        "    return run()\n"
    )
    (tmp_path / "helper.py").write_text(
        "def run():\n"
        "    return 'ok'\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "arch-api", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200

    r = client.get("/api/v1/architecture?project=arch-api")

    assert r.status_code == 200

    data = r.json()

    assert data["answer"] == "FAKE RESPONSE"
    assert data["summary"]["total_symbols"] == 2
    assert data["summary"]["total_files"] == 2
    assert ".py" in data["summary"]["languages"]
    assert [item["symbol"] for item in data["summary"]["hotspots"]] == ["run"]


def test_deadcode_reports_unused_symbols(tmp_path):

    (tmp_path / "module.py").write_text(
        "def used():\n"
        "    return 1\n"
        "def orphan():\n"
        "    return 2\n"
    )
    (tmp_path / "caller.py").write_text(
        "from module import used\n"
        "def call():\n"
        "    return used()\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "deadcode-api", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200

    deadcode = client.get("/api/v1/workspace/deadcode?project=deadcode-api")

    assert deadcode.status_code == 200
    assert [item["symbol"] for item in deadcode.json()] == ["call", "orphan"]


def test_code_service_falls_back_when_llm_returns_empty(monkeypatch, tmp_path):

    (tmp_path / "module.py").write_text(
        "def greet():\n"
        "    return 'hi'\n"
    )

    client.post(
        "/api/v1/analyze",
        json={"project_id": "empty-llm", "workspace": str(tmp_path)},
    )

    from app.services import code_service

    monkeypatch.setattr(
        code_service.ai_service,
        "chat",
        lambda **kwargs: {"response": "", "model": "qwen", "thinking": False, "elapsed_ms": 1},
    )

    r = client.post(
        "/api/v1/explain-code",
        json={
            "code": "return 'hi'",
            "file": "module.py",
            "start_line": 1,
            "end_line": 2,
            "project": "empty-llm",
        },
    )

    assert r.status_code == 200
    assert r.json()["answer"] == "No explanation could be generated from the supplied context."


def test_workspace_ai_service_falls_back_when_llm_returns_empty(monkeypatch):

    from app.services import workspace_ai_service

    monkeypatch.setattr(
        workspace_ai_service.ai_service,
        "chat",
        lambda **kwargs: {"response": "", "model": "qwen", "thinking": False, "elapsed_ms": 1},
    )

    r = client.get("/api/v1/workspace/explain/AIService.chat")

    assert r.status_code == 200
    assert r.json()["answer"] == "No explanation could be generated from the supplied context."


def test_diagnose_service_extracts_stack_frames():

    from app.services.diagnose_service import diagnose_service

    frames = diagnose_service._extract_frames(
        """
        at greet (src/utils/greeter.ts:12:9)
        at Object.run (src/screens/HomeScreen.tsx:45:13)
        at renderItem (node_modules/.../flatlist.js:10:5)
        """,
        "",
    )

    assert frames[0]["file"] == "src/utils/greeter.ts"
    assert frames[0]["line"] == 12
    assert frames[0]["function"] == "greet"

    python = diagnose_service._extract_frames(
        '  File "/workspace/app/services/foo.py", line 8, in run\n'
        '    return helper()\n'
        "TypeError: unsupported operand type(s)",
        "",
    )

    assert python[0]["function"] == "run"
    assert python[0]["line"] == 8


def test_developer_api_diagnoses_error_with_matched_symbol(tmp_path):

    (tmp_path / "greeter.ts").write_text(
        "export function greet(name: string) {\n"
        "  return name.toUpperCase()\n"
        "}\n"
    )

    analyze = client.post(
        "/api/v1/analyze",
        json={"project_id": "diag-api", "workspace": str(tmp_path)},
    )

    assert analyze.status_code == 200

    r = client.post(
        "/api/v1/diagnose-error",
        json={
            "error": (
                "TypeError: name.toUpperCase is not a function\n"
                "    at greet (greeter.ts:2:16)\n"
                "    at Object.<anonymous> (index.ts:10:5)"
            ),
            "file": "",
            "project": "diag-api",
        },
    )

    assert r.status_code == 200

    data = r.json()

    assert any(
        frame["symbol"] == "greet"
        for frame in data["frames"]
    )

    assert data["diagnosis"]["root_cause"] == "fake root cause"
    assert data["diagnosis"]["fixes"][0]["symbol"] == "greet"


def test_diagnose_service_falls_back_when_llm_returns_empty(monkeypatch, tmp_path):

    (tmp_path / "module.py").write_text(
        "def run():\n"
        "    return 'ok'\n"
    )

    client.post(
        "/api/v1/analyze",
        json={"project_id": "diag-empty", "workspace": str(tmp_path)},
    )

    from app.services import diagnose_service

    monkeypatch.setattr(
        diagnose_service.ai_service,
        "chat",
        lambda **kwargs: {"response": "", "model": "qwen", "thinking": False, "elapsed_ms": 1},
    )

    r = client.post(
        "/api/v1/diagnose-error",
        json={
            "error": 'File "module.py", line 1, in run\nRuntimeError: boom',
            "file": "",
            "project": "diag-empty",
        },
    )

    assert r.status_code == 200

    diagnosis = r.json()["diagnosis"]

    assert diagnosis["root_cause"] == (
        "Could not determine the root cause from the supplied workspace context."
    )


def test_error_search_traces_non_stack_trace_error(tmp_path):

    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "finvoiz",
                "dependencies": {
                    "react-native-purchases": "8.9.5",
                },
            }
        )
    )

    (tmp_path / "billing.ts").write_text(
        "export function getBillingInfo() {\n"
        "  return { provider: 'play' }\n"
        "}\n"
    )

    cache = WorkspaceCache()

    cache.load(str(tmp_path))

    from app.workspace.search.error_search import error_search

    evidence = error_search.search(
        cache,
        "App must use Google Play Billing Library version 8.0.0 or later",
    )

    files = [item["file"] for item in evidence]

    assert "package.json" in files

    assert "billing.ts" in files

    assert files.index("package.json") < files.index("billing.ts")

    billing_item = next(
        item for item in evidence
        if item["file"] == "billing.ts"
    )

    assert "billing" in billing_item["hits"]


def test_diagnose_fallback_context_uses_workspace_evidence(tmp_path):

    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "finvoiz",
                "dependencies": {
                    "react-native-purchases": "8.9.5",
                },
            }
        )
    )

    (tmp_path / "billing.ts").write_text(
        "export function getBillingInfo() {\n"
        "  return { provider: 'play' }\n"
        "}\n"
    )

    cache = WorkspaceCache()

    cache.load(str(tmp_path))

    from app.services.diagnose_service import diagnose_service

    context = diagnose_service._build_context(
        cache,
        [],
        "App must use Google Play Billing Library version 8.0.0 or later",
    )

    sources = context["related_sources"]

    files = [item["symbol"] for item in sources]

    assert "package.json" in files

    assert "billing.ts" in files

    assert context["trace"]["keywords"]


def test_diagnose_parses_json_embedded_in_model_noise():

    from app.services.diagnose_service import diagnose_service

    diagnosis = diagnose_service._parse_response(
        (
            "Here is my analysis:\n"
            "```json\n"
            '{"root_cause": "old billing library", "location": "a.ts:1", '
            '"explanation": "first draft", "fixes": []}\n'
            "```\n"
            "Actually the correct one is:\n"
            '{"root_cause": "new billing library", "location": "package.json", '
            '"explanation": "final answer", "fixes": '
            '[{"description": "upgrade", "file": "package.json"}]}'
        ),
        "",
        [],
    )

    assert diagnosis["root_cause"] == "new billing library"

    assert diagnosis["location"] == "package.json"

    assert diagnosis["fixes"][0]["file"] == "package.json"

