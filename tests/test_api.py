"""Tests for the FastAPI REST API layer."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_db_path(tmp_path, monkeypatch):
    """Point the API to a temporary database for every test."""
    monkeypatch.setenv("CODENAME_DB_PATH", str(tmp_path / "test.db"))
    import codename_generator.api as api_module

    api_module._manager = None


@pytest.fixture
def client():
    from codename_generator.api import app

    return TestClient(app)


@pytest.fixture
def admin_client():
    """A separate admin-mode app — same code, mounts static_admin/."""
    from codename_generator.api import create_app

    return TestClient(create_app("admin"))


def _leaf_id(client: TestClient, slug: str) -> str:
    """Resolve the public CAT- id for a seeded leaf category by slug."""
    res = client.get("/api/categories")
    assert res.status_code == 200
    for c in res.json():
        if c["slug"] == slug and c["parent_category_id"] is not None:
            return c["category_id"]
    raise KeyError(f"Leaf '{slug}' not found in seed")


def _top_id(client: TestClient, slug: str) -> str:
    res = client.get("/api/categories")
    for c in res.json():
        if c["slug"] == slug and c["parent_category_id"] is None:
            return c["category_id"]
    raise KeyError(f"Top '{slug}' not found")


def _sample_person(client: TestClient) -> dict:
    return {
        "name": "Einstein",
        "name_en": "Einstein",
        "name_zh": "爱因斯坦",
        "category_id": _leaf_id(client, "science"),
        "brief": "Theoretical physicist",
    }


def _sample_animal(client: TestClient) -> dict:
    return {
        "name": "Panda",
        "name_en": "Panda",
        "name_zh": "熊猫",
        "category_id": _leaf_id(client, "mammal"),
        "brief": "Bamboo-eating mammal",
    }


def _add_one(client: TestClient, codename: dict | None = None) -> str:
    """Add a single codename and return its codename_id."""
    if codename is None:
        codename = _sample_person(client)
    res = client.post("/api/codenames", json={"codenames": [codename]})
    assert res.status_code == 200
    data = res.json()
    assert data["added"] == 1, f"add failed: {data}"
    return data["codename_ids"][0]


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class TestListCategories:
    def test_flat_includes_seeded(self, client: TestClient):
        res = client.get("/api/categories")
        assert res.status_code == 200
        cats = res.json()
        slugs = {c["slug"] for c in cats}
        assert "person" in slugs and "animal" in slugs
        assert "science" in slugs and "mammal" in slugs
        assert len(cats) == 15

    def test_tree_nests_children(self, client: TestClient):
        res = client.get("/api/categories?tree=1")
        assert res.status_code == 200
        roots = res.json()
        top_slugs = {r["slug"] for r in roots}
        assert top_slugs == {"person", "animal"}
        person = next(r for r in roots if r["slug"] == "person")
        assert person["children"] is not None
        assert {c["slug"] for c in person["children"]} >= {"science", "mathematics"}

    def test_parent_filter_top_level(self, client: TestClient):
        res = client.get("/api/categories?parent_category_id=")
        cats = res.json()
        assert len(cats) == 2
        assert {c["slug"] for c in cats} == {"person", "animal"}

    def test_parent_filter_by_parent(self, client: TestClient):
        person_top = _top_id(client, "person")
        res = client.get(f"/api/categories?parent_category_id={person_top}")
        cats = res.json()
        assert len(cats) == 10
        assert all(c["parent_category_id"] == person_top for c in cats)

    def test_get_by_id(self, client: TestClient):
        cat_id = _leaf_id(client, "science")
        res = client.get(f"/api/categories/{cat_id}")
        assert res.status_code == 200
        assert res.json()["slug"] == "science"

    def test_get_by_id_not_found(self, client: TestClient):
        res = client.get("/api/categories/CAT-nonexist")
        assert res.status_code == 404


class TestCreateCategory:
    def test_create_top_level(self, client: TestClient):
        res = client.post(
            "/api/categories",
            json={"slug": "mythic", "name_en": "Mythic", "name_zh": "神话"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["slug"] == "mythic"
        assert data["depth"] == 1
        assert data["parent_category_id"] is None

    def test_create_child(self, client: TestClient):
        animal_top = _top_id(client, "animal")
        res = client.post(
            "/api/categories",
            json={
                "slug": "cetacean",
                "name_en": "Cetacean",
                "name_zh": "鲸目",
                "parent_category_id": animal_top,
            },
        )
        assert res.status_code == 200
        assert res.json()["depth"] == 2

    def test_duplicate_slug_rejected(self, client: TestClient):
        res = client.post(
            "/api/categories",
            json={"slug": "person", "name_en": "Person2", "name_zh": "人2"},
        )
        assert res.status_code == 400
        assert "already exists" in res.json()["detail"].lower()

    def test_depth_four_rejected(self, client: TestClient):
        mammal_id = _leaf_id(client, "mammal")
        r = client.post(
            "/api/categories",
            json={"slug": "whale", "name_en": "Whale", "name_zh": "鲸",
                  "parent_category_id": mammal_id},
        )
        assert r.status_code == 200
        whale_id = r.json()["category_id"]
        r2 = client.post(
            "/api/categories",
            json={"slug": "bluewhale", "name_en": "Blue", "name_zh": "蓝",
                  "parent_category_id": whale_id},
        )
        assert r2.status_code == 400
        assert "depth" in r2.json()["detail"].lower()


class TestUpdateCategory:
    def test_rename(self, client: TestClient):
        cat_id = _leaf_id(client, "science")
        res = client.put(
            f"/api/categories/{cat_id}",
            json={"name_en": "Natural Science"},
        )
        assert res.status_code == 200
        assert res.json()["name_en"] == "Natural Science"

    def test_reparent(self, client: TestClient):
        animal_top = _top_id(client, "animal")
        eng_id = _leaf_id(client, "engineering")
        res = client.put(
            f"/api/categories/{eng_id}",
            json={"parent_category_id": animal_top},
        )
        assert res.status_code == 200
        assert res.json()["parent_category_id"] == animal_top

    def test_reparent_to_top_level(self, client: TestClient):
        eng_id = _leaf_id(client, "engineering")
        res = client.put(
            f"/api/categories/{eng_id}",
            json={"parent_category_id": ""},
        )
        assert res.status_code == 200
        assert res.json()["parent_category_id"] is None
        assert res.json()["depth"] == 1

    def test_reparent_cycle_rejected(self, client: TestClient):
        person_top = _top_id(client, "person")
        science_id = _leaf_id(client, "science")
        res = client.put(
            f"/api/categories/{person_top}",
            json={"parent_category_id": science_id},
        )
        assert res.status_code == 400
        assert "cycle" in res.json()["detail"].lower()

    def test_archive_with_codenames_rejected(self, client: TestClient):
        _add_one(client)
        science_id = _leaf_id(client, "science")
        res = client.put(
            f"/api/categories/{science_id}",
            json={"is_archived": True},
        )
        assert res.status_code == 400
        assert "codenames" in res.json()["detail"].lower()

    def test_archive_empty_leaf(self, client: TestClient):
        math_id = _leaf_id(client, "mathematics")
        res = client.put(
            f"/api/categories/{math_id}",
            json={"is_archived": True},
        )
        assert res.status_code == 200
        assert res.json()["is_archived"] is True

    def test_not_found(self, client: TestClient):
        res = client.put(
            "/api/categories/CAT-nonexist", json={"name_en": "x"}
        )
        assert res.status_code == 400


class TestDeleteCategory:
    def test_delete_empty_leaf(self, client: TestClient):
        math_id = _leaf_id(client, "mathematics")
        res = client.delete(f"/api/categories/{math_id}")
        assert res.status_code == 200
        assert res.json() == {"deleted": math_id}

    def test_delete_with_codenames_rejected(self, client: TestClient):
        _add_one(client)
        science_id = _leaf_id(client, "science")
        res = client.delete(f"/api/categories/{science_id}")
        assert res.status_code == 400
        assert "codenames" in res.json()["detail"].lower()

    def test_delete_with_children_rejected(self, client: TestClient):
        person_top = _top_id(client, "person")
        res = client.delete(f"/api/categories/{person_top}")
        assert res.status_code == 400
        assert "subcategories" in res.json()["detail"].lower()


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
        assert "by_category" in data
        assert len(data["by_category"]) == 15

    def test_stats_after_add(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/stats")
        data = res.json()
        assert data["total"] == 1
        assert data["available"] == 1
        per_slug = {c["slug"]: c for c in data["by_category"]}
        assert per_slug["science"]["total"] == 1


# ---------------------------------------------------------------------------
# Add codenames
# ---------------------------------------------------------------------------


class TestAddCodenames:
    def test_add_single(self, client: TestClient):
        res = client.post("/api/codenames", json={"codenames": [_sample_person(client)]})
        assert res.status_code == 200
        data = res.json()
        assert data["added"] == 1
        assert len(data["codename_ids"]) == 1
        assert data["codename_ids"][0].startswith("CN-")

    def test_add_batch(self, client: TestClient):
        res = client.post(
            "/api/codenames",
            json={"codenames": [_sample_person(client), _sample_animal(client)]},
        )
        assert res.status_code == 200
        assert res.json()["added"] == 2

    def test_add_non_leaf_rejected(self, client: TestClient):
        bad = {**_sample_person(client), "category_id": _top_id(client, "person")}
        res = client.post("/api/codenames", json={"codenames": [bad]})
        data = res.json()
        assert data["added"] == 0
        assert "not a leaf" in data["errors"][0]

    def test_add_unknown_category_rejected(self, client: TestClient):
        bad = {**_sample_person(client), "category_id": "CAT-nonexist"}
        res = client.post("/api/codenames", json={"codenames": [bad]})
        data = res.json()
        assert data["added"] == 0
        assert "not found" in data["errors"][0]


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
        assert data[0]["category_path"] == ["person", "science"]

    def test_filter_by_category_subtree(self, client: TestClient):
        _add_one(client, _sample_person(client))
        _add_one(client, _sample_animal(client))
        person_top = _top_id(client, "person")
        res = client.get(f"/api/codenames?category_id={person_top}")
        assert len(res.json()) == 1
        assert res.json()[0]["category_path"][0] == "person"

    def test_filter_direct_only_excludes_descendants(self, client: TestClient):
        _add_one(client)
        person_top = _top_id(client, "person")
        res = client.get(
            f"/api/codenames?category_id={person_top}&include_descendants=false"
        )
        assert res.json() == []

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

    def test_draw_with_category_filter(self, client: TestClient):
        _add_one(client, _sample_person(client))
        _add_one(client, _sample_animal(client))
        animal_top = _top_id(client, "animal")
        res = client.get(f"/api/codenames/random?count=10&category_id={animal_top}")
        data = res.json()
        assert len(data) == 1
        assert data[0]["category_path"][0] == "animal"


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_update_name(self, client: TestClient):
        cid = _add_one(client)
        res = client.put(f"/api/codenames/{cid}", json={"name": "Albert"})
        assert res.status_code == 200
        assert res.json()["name"] == "Albert"

    def test_update_category(self, client: TestClient):
        cid = _add_one(client)
        mammal_id = _leaf_id(client, "mammal")
        res = client.put(f"/api/codenames/{cid}", json={"category_id": mammal_id})
        assert res.status_code == 200
        assert res.json()["category_id"] == mammal_id
        assert res.json()["category_path"] == ["animal", "mammal"]

    def test_update_category_non_leaf_rejected(self, client: TestClient):
        cid = _add_one(client)
        person_top = _top_id(client, "person")
        res = client.put(f"/api/codenames/{cid}", json={"category_id": person_top})
        assert res.status_code == 400

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
    def test_logs_after_add(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/logs?action=added")
        data = res.json()
        assert len(data) == 1
        assert data[0]["action"] == "added"

    def test_logs_filter_by_action(self, client: TestClient):
        _add_one(client)
        res = client.get("/api/logs?action=assigned")
        assert res.json() == []

    def test_category_added_logged(self, client: TestClient):
        client.post(
            "/api/categories",
            json={"slug": "mythic", "name_en": "Mythic", "name_zh": "神话"},
        )
        res = client.get("/api/logs?action=category_added")
        # Seed doesn't log; only the manual create does.
        data = res.json()
        assert len(data) == 1


# ---------------------------------------------------------------------------
# Static files (user and admin modes)
# ---------------------------------------------------------------------------


class TestStaticFiles:
    def test_root_returns_html_user_mode(self, client: TestClient):
        static_dir = os.path.join(
            os.path.dirname(__file__), "..", "src", "codename_generator", "static_user",
        )
        if os.path.isfile(os.path.join(static_dir, "index.html")):
            res = client.get("/")
            assert res.status_code == 200
            assert "html" in res.headers.get("content-type", "")

    def test_root_returns_html_admin_mode(self, admin_client: TestClient):
        static_dir = os.path.join(
            os.path.dirname(__file__), "..", "src", "codename_generator", "static_admin",
        )
        if os.path.isfile(os.path.join(static_dir, "index.html")):
            res = admin_client.get("/")
            assert res.status_code == 200
            assert "html" in res.headers.get("content-type", "")

    def test_serve_svg_exists(self, client: TestClient):
        static_dir = os.path.join(
            os.path.dirname(__file__), "..", "src", "codename_generator", "static_user",
        )
        if os.path.isfile(os.path.join(static_dir, "logo.svg")):
            res = client.get("/logo.svg")
            assert res.status_code == 200
            assert "image/svg+xml" in res.headers.get("content-type", "")

    def test_serve_svg_not_found(self, client: TestClient):
        res = client.get("/nonexistent.svg")
        assert res.status_code == 404
