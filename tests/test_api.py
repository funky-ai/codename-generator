"""Tests for the FastAPI REST API layer."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_db_path(tmp_path, monkeypatch):
    """Point the API to a temporary database for every test."""
    monkeypatch.setenv("CODENAME_DB_PATH", str(tmp_path / "test.db"))
    # Reset the singleton so each test gets a fresh manager
    import codename_generator.api as api_module

    api_module._manager = None


@pytest.fixture
def client():
    from codename_generator.api import app

    return TestClient(app)


SAMPLE_PERSON = {
    "name": "Einstein",
    "name_en": "Einstein",
    "name_zh": "爱因斯坦",
    "theme": "person",
    "sub_theme": "science",
    "brief": "Theoretical physicist",
}

SAMPLE_ANIMAL = {
    "name": "Falcon",
    "name_en": "Falcon",
    "name_zh": "猎隼",
    "theme": "animal",
    "brief": "A fast bird of prey",
}


def _add_one(client: TestClient, codename: dict = SAMPLE_PERSON) -> str:
    """Add a single codename and return its codename_id."""
    res = client.post("/api/codenames", json={"codenames": [codename]})
    assert res.status_code == 200
    data = res.json()
    assert data["added"] == 1
    return data["codename_ids"][0]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestStats:
    def test_empty_stats(self, client: TestClient):
        res = client.get("/api/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["available"] == 0
        assert data["assigned"] == 0

    def test_stats_after_add(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/stats")
        data = res.json()
        assert data["total"] == 1
        assert data["available"] == 1


# ---------------------------------------------------------------------------
# Add codenames
# ---------------------------------------------------------------------------


class TestAddCodenames:
    def test_add_single(self, client: TestClient):
        res = client.post("/api/codenames", json={"codenames": [SAMPLE_PERSON]})
        assert res.status_code == 200
        data = res.json()
        assert data["added"] == 1
        assert len(data["codename_ids"]) == 1
        assert data["codename_ids"][0].startswith("CN-")

    def test_add_batch(self, client: TestClient):
        res = client.post(
            "/api/codenames",
            json={"codenames": [SAMPLE_PERSON, SAMPLE_ANIMAL]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["added"] == 2

    def test_add_person_without_sub_theme(self, client: TestClient):
        bad = {**SAMPLE_PERSON, "sub_theme": None}
        res = client.post("/api/codenames", json={"codenames": [bad]})
        data = res.json()
        assert data["added"] == 0
        assert len(data["errors"]) == 1


# ---------------------------------------------------------------------------
# List codenames
# ---------------------------------------------------------------------------


class TestListCodenames:
    def test_list_empty(self, client: TestClient):
        res = client.get("/api/codenames")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_with_data(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/codenames")
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "Einstein"

    def test_filter_by_theme(self, client: TestClient):
        _add_one(client, SAMPLE_PERSON)
        _add_one(client, SAMPLE_ANIMAL)
        res = client.get("/api/codenames?theme=person")
        assert len(res.json()) == 1
        assert res.json()[0]["theme"] == "person"

    def test_filter_by_status(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/codenames?status=assigned")
        assert len(res.json()) == 0


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_search(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/codenames/search?q=Einstein")
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_search_no_results(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/codenames/search?q=nonexistent")
        assert res.json() == []


# ---------------------------------------------------------------------------
# Draw random
# ---------------------------------------------------------------------------


class TestDrawRandom:
    def test_draw_empty(self, client: TestClient):
        res = client.get("/api/codenames/random")
        assert res.status_code == 200
        assert res.json() == []

    def test_draw_with_data(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/codenames/random?count=1")
        data = res.json()
        assert len(data) == 1
        assert data[0]["status"] == "available"


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_update_name(self, client: TestClient):
        cid = _add_one(client)
        res = client.put(f"/api/codenames/{cid}", json={"name": "Albert"})
        assert res.status_code == 200
        assert res.json()["name"] == "Albert"

    def test_update_not_found(self, client: TestClient):
        res = client.put("/api/codenames/CN-nonexist", json={"name": "X"})
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# Assign
# ---------------------------------------------------------------------------


class TestAssign:
    def test_assign(self, client: TestClient):
        cid = _add_one(client)
        res = client.post(
            f"/api/codenames/{cid}/assign",
            json={"description": "Project Alpha"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["codename_id"] == cid
        assert data["assignment_id"].startswith("ASN-")

    def test_assign_already_assigned(self, client: TestClient):
        cid = _add_one(client)
        client.post(f"/api/codenames/{cid}/assign", json={})
        res = client.post(f"/api/codenames/{cid}/assign", json={})
        assert res.status_code == 400

    def test_assign_not_found(self, client: TestClient):
        res = client.post("/api/codenames/CN-nonexist/assign", json={})
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


class TestAssignments:
    def test_list_empty(self, client: TestClient):
        res = client.get("/api/assignments")
        assert res.json() == []

    def test_list_after_assign(self, client: TestClient):
        cid = _add_one(client)
        client.post(f"/api/codenames/{cid}/assign", json={"description": "Test"})
        res = client.get("/api/assignments")
        data = res.json()
        assert len(data) == 1
        assert data[0]["description"] == "Test"


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


class TestLogs:
    def test_logs_empty(self, client: TestClient):
        res = client.get("/api/logs")
        assert res.json() == []

    def test_logs_after_add(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/logs")
        data = res.json()
        assert len(data) == 1
        assert data[0]["action"] == "added"

    def test_logs_filter_by_action(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/logs?action=assigned")
        assert res.json() == []


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------


class TestStaticFiles:
    def test_root_returns_html(self, client: TestClient):
        # Only works if static/index.html exists
        static_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "codename_generator",
            "static",
        )
        if os.path.isfile(os.path.join(static_dir, "index.html")):
            res = client.get("/")
            assert res.status_code == 200
            assert "html" in res.headers.get("content-type", "")
