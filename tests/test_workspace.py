import os

os.environ["LLM_PROVIDER"] = "fake"

from fastapi.testclient import TestClient

from app.main import app

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
