"""Tests for codename inventory core business logic."""

import json

import pytest

from codename_generator.core import CodenameManager
from codename_generator.models import CodenameInput, CodenameUpdate


@pytest.fixture
def manager(tmp_path):
    """Create a manager with a temporary database (15 default categories seeded)."""
    db_path = tmp_path / "test.db"
    return CodenameManager(db_path)


def _leaf_id(manager: CodenameManager, slug: str) -> str:
    """Resolve the public CAT- id of a seeded leaf by its slug."""
    cats = manager.list_categories()
    for c in cats:
        if c.slug == slug and c.parent_category_id is not None:
            return c.category_id
    raise KeyError(f"Leaf '{slug}' not found in seeded categories")


def _top_id(manager: CodenameManager, slug: str) -> str:
    """Resolve the public CAT- id of a top-level category by slug."""
    cats = manager.list_categories()
    for c in cats:
        if c.slug == slug and c.parent_category_id is None:
            return c.category_id
    raise KeyError(f"Top-level '{slug}' not found")


@pytest.fixture
def science_id(manager):
    return _leaf_id(manager, "science")


@pytest.fixture
def mammal_id(manager):
    return _leaf_id(manager, "mammal")


@pytest.fixture
def sample_person(science_id):
    return CodenameInput(
        name="Einstein",
        name_en="Einstein",
        name_zh="爱因斯坦",
        category_id=science_id,
        brief="Theoretical physicist who developed the theory of relativity",
    )


@pytest.fixture
def sample_animal(mammal_id):
    return CodenameInput(
        name="Panda",
        name_en="Panda",
        name_zh="熊猫",
        category_id=mammal_id,
        brief="Bamboo-eating mammal native to central China",
    )


def _add_one(manager, item):
    """Add a single codename and return its codename_id."""
    result = manager.add_codenames([item])
    assert result["added"] == 1, f"add failed: {result}"
    return result["codename_ids"][0]


# ------------------------------------------------------------------
# add_codenames
# ------------------------------------------------------------------


class TestAddCodenames:
    def test_add_single(self, manager, sample_person):
        result = manager.add_codenames([sample_person])
        assert result["added"] == 1
        assert len(result["codename_ids"]) == 1
        assert result["codename_ids"][0].startswith("CN-")
        assert result["errors"] == []

    def test_add_batch(self, manager, sample_person, sample_animal):
        result = manager.add_codenames([sample_person, sample_animal])
        assert result["added"] == 2
        assert len(result["codename_ids"]) == 2

    def test_codename_ids_are_unique(self, manager, sample_person, sample_animal):
        result = manager.add_codenames([sample_person, sample_animal])
        assert result["codename_ids"][0] != result["codename_ids"][1]

    def test_add_non_leaf_category_fails(self, manager):
        top_id = _top_id(manager, "person")
        item = CodenameInput(
            name="Curie", name_en="Curie", name_zh="居里",
            category_id=top_id, brief="Chemist",
        )
        result = manager.add_codenames([item])
        assert result["added"] == 0
        assert len(result["errors"]) == 1
        assert "not a leaf" in result["errors"][0]

    def test_add_unknown_category_fails(self, manager):
        item = CodenameInput(
            name="Ghost", name_en="Ghost", name_zh="幻",
            category_id="CAT-nonexist", brief="test",
        )
        result = manager.add_codenames([item])
        assert result["added"] == 0
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0]

    def test_add_archived_category_fails(self, manager, science_id):
        # Archive 'mathematics' (no codenames bound) and try to add under it
        math_id = _leaf_id(manager, "mathematics")
        from codename_generator.models import CategoryUpdate
        manager.update_category(math_id, CategoryUpdate(is_archived=True))
        item = CodenameInput(
            name="Gauss", name_en="Gauss", name_zh="高斯",
            category_id=math_id, brief="mathematician",
        )
        result = manager.add_codenames([item])
        assert result["added"] == 0
        assert "archived" in result["errors"][0]

    def test_added_codename_hydrates_path(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        inv = manager.list_inventory()
        found = next(c for c in inv if c.codename_id == cid)
        assert found.category_path == ["person", "science"]


# ------------------------------------------------------------------
# draw_random
# ------------------------------------------------------------------


class TestDrawRandom:
    def test_draw_from_empty(self, manager):
        results = manager.draw_random(count=3)
        assert results == []

    def test_draw_returns_available_only(self, manager, sample_person, sample_animal):
        result = manager.add_codenames([sample_person, sample_animal])
        cid_person = result["codename_ids"][0]
        manager.assign_codename(cid_person)
        results = manager.draw_random(count=10)
        assert len(results) == 1
        assert results[0].name == "Panda"

    def test_draw_with_subtree_filter(self, manager, sample_person, sample_animal):
        manager.add_codenames([sample_person, sample_animal])
        animal_top = _top_id(manager, "animal")
        results = manager.draw_random(category_id=animal_top, count=10)
        assert len(results) == 1
        assert results[0].category_path[0] == "animal"

    def test_draw_direct_only_excludes_descendants(
        self, manager, sample_person, sample_animal
    ):
        # All default animal codenames live on leaves (mammal/...), not on the
        # top-level animal row, so include_descendants=False should return nothing.
        manager.add_codenames([sample_animal])
        animal_top = _top_id(manager, "animal")
        results = manager.draw_random(
            category_id=animal_top, include_descendants=False, count=10
        )
        assert results == []

    def test_draw_returns_codename_id(self, manager, sample_person):
        manager.add_codenames([sample_person])
        results = manager.draw_random(count=1)
        assert results[0].codename_id.startswith("CN-")
        assert results[0].category_path == ["person", "science"]


# ------------------------------------------------------------------
# assign_codename (irreversible)
# ------------------------------------------------------------------


class TestAssignCodename:
    def test_assign_success(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        assignment = manager.assign_codename(cid)
        assert assignment.assignment_id.startswith("ASN-")
        assert assignment.codename_id == cid
        assert assignment.codename_name == "Einstein"
        assert assignment.description is None

    def test_assign_with_description(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        assignment = manager.assign_codename(cid, description="Internal auth service")
        assert assignment.codename_id == cid
        assert assignment.description == "Internal auth service"

    def test_assign_returns_assigned_at(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        assignment = manager.assign_codename(cid)
        assert assignment.assigned_at != ""

    def test_assign_changes_status(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.assign_codename(cid)
        inventory = manager.list_inventory(status="available")
        assert len(inventory) == 0
        inventory = manager.list_inventory(status="assigned")
        assert len(inventory) == 1

    def test_assign_nonexistent_fails(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.assign_codename("CN-NOTEXIST")

    def test_assign_already_assigned_fails(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.assign_codename(cid)
        with pytest.raises(ValueError, match="already assigned"):
            manager.assign_codename(cid)


# ------------------------------------------------------------------
# inventory_stats
# ------------------------------------------------------------------


class TestInventoryStats:
    def test_empty_stats(self, manager):
        stats = manager.get_inventory_stats()
        assert stats.total == 0
        assert stats.available == 0
        assert stats.low_stock_warning is True
        # 15 seeded categories contribute rows with zero counts
        assert len(stats.by_category) == 15

    def test_stats_after_add(self, manager, sample_person, sample_animal):
        manager.add_codenames([sample_person, sample_animal])
        stats = manager.get_inventory_stats()
        assert stats.total == 2
        assert stats.available == 2
        assert stats.assigned == 0
        per_slug = {c.slug: c for c in stats.by_category}
        assert per_slug["science"].total == 1
        assert per_slug["mammal"].total == 1
        # Top-level categories should remain empty (codenames are on leaves)
        assert per_slug["person"].total == 0
        assert per_slug["animal"].total == 0

    def test_by_category_includes_depth(self, manager):
        stats = manager.get_inventory_stats()
        per_slug = {c.slug: c for c in stats.by_category}
        assert per_slug["person"].depth == 1
        assert per_slug["science"].depth == 2

    def test_low_stock_warning(self, manager, sample_person):
        manager.add_codenames([sample_person])
        stats = manager.get_inventory_stats()
        assert stats.low_stock_warning is True
        assert stats.warning_message is not None


# ------------------------------------------------------------------
# logs
# ------------------------------------------------------------------


class TestLogs:
    def test_add_creates_log(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        logs = manager.get_logs(action="added")
        assert len(logs) == 1
        assert logs[0].action == "added"
        assert logs[0].codename_id == cid

    def test_assign_creates_log(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.assign_codename(cid)
        logs = manager.get_logs(action="assigned")
        assert len(logs) == 1
        assert logs[0].codename_id == cid

    def test_log_filter_by_action(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.assign_codename(cid)
        all_logs = manager.get_logs()
        # Two logs from this test plus none others (migrations don't log).
        assert len([log for log in all_logs if log.codename_id == cid]) == 2
        added_logs = manager.get_logs(action="added")
        assert any(log.codename_id == cid for log in added_logs)


# ------------------------------------------------------------------
# search
# ------------------------------------------------------------------


class TestSearch:
    def test_search_by_english_name(self, manager, sample_person):
        manager.add_codenames([sample_person])
        results = manager.search("Einstein")
        assert len(results) == 1

    def test_search_by_chinese_name(self, manager, sample_person):
        manager.add_codenames([sample_person])
        results = manager.search("爱因斯坦")
        assert len(results) == 1

    def test_search_by_brief(self, manager, sample_person):
        manager.add_codenames([sample_person])
        results = manager.search("relativity")
        assert len(results) == 1

    def test_search_no_match(self, manager, sample_person):
        manager.add_codenames([sample_person])
        results = manager.search("nonexistent")
        assert len(results) == 0

    def test_search_result_has_category_path(self, manager, sample_person):
        manager.add_codenames([sample_person])
        results = manager.search("Einstein")
        assert results[0].category_path == ["person", "science"]


# ------------------------------------------------------------------
# update_codename
# ------------------------------------------------------------------


class TestUpdateCodename:
    def test_update_single_field(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        result = manager.update_codename(CodenameUpdate(codename_id=cid, brief="Updated brief"))
        assert result.brief == "Updated brief"
        assert result.name_en == "Einstein"  # unchanged
        assert result.codename_id == cid  # unchanged

    def test_update_multiple_fields(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        result = manager.update_codename(
            CodenameUpdate(codename_id=cid, name_en="A. Einstein", name_zh="阿尔伯特")
        )
        assert result.name_en == "A. Einstein"
        assert result.name_zh == "阿尔伯特"

    def test_update_name_field(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        result = manager.update_codename(CodenameUpdate(codename_id=cid, name="Albert Einstein"))
        assert result.name == "Albert Einstein"
        assert result.codename_id == cid  # ID doesn't change

    def test_update_category_to_another_leaf(self, manager, sample_person, mammal_id):
        cid = _add_one(manager, sample_person)
        result = manager.update_codename(
            CodenameUpdate(codename_id=cid, category_id=mammal_id)
        )
        assert result.category_id == mammal_id
        assert result.category_path == ["animal", "mammal"]

    def test_update_category_to_non_leaf_fails(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        top_id = _top_id(manager, "person")
        with pytest.raises(ValueError, match="not a leaf"):
            manager.update_codename(
                CodenameUpdate(codename_id=cid, category_id=top_id)
            )

    def test_update_nonexistent_fails(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.update_codename(CodenameUpdate(codename_id="CN-NOTEXIST", brief="New brief"))

    def test_update_no_fields_fails(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        with pytest.raises(ValueError, match="No fields to update"):
            manager.update_codename(CodenameUpdate(codename_id=cid))

    def test_update_assigned_codename_allowed(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.assign_codename(cid)
        result = manager.update_codename(CodenameUpdate(codename_id=cid, brief="Corrected brief"))
        assert result.brief == "Corrected brief"
        assert result.status == "assigned"

    def test_update_creates_log(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.update_codename(CodenameUpdate(codename_id=cid, brief="New brief"))
        logs = manager.get_logs(action="updated")
        assert len(logs) == 1
        assert logs[0].codename_id == cid

    def test_update_log_details_structure(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.update_codename(
            CodenameUpdate(codename_id=cid, name_en="A. Einstein", brief="New")
        )
        logs = manager.get_logs(action="updated")
        details = json.loads(logs[0].details)
        assert details["name"] == "Einstein"
        assert set(details["changed_fields"]) == {"name_en", "brief"}
        assert details["old_values"]["name_en"] == "Einstein"
        assert details["new_values"]["name_en"] == "A. Einstein"


# ------------------------------------------------------------------
# codename_id format
# ------------------------------------------------------------------


class TestCodenameId:
    def test_format(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        assert cid.startswith("CN-")
        assert len(cid) == 11  # CN- + 8 chars

    def test_uses_alphanumeric_only(self, manager, mammal_id):
        """codename_id should only contain CN- prefix + alphanumeric chars."""
        import string
        items = [
            CodenameInput(
                name=f"Test{i}", name_en=f"Test{i}", name_zh=f"测试{i}",
                category_id=mammal_id, brief=f"Test {i}",
            )
            for i in range(20)
        ]
        result = manager.add_codenames(items)
        valid_chars = set(string.ascii_letters + string.digits)
        for cid in result["codename_ids"]:
            random_part = cid[3:]
            assert all(c in valid_chars for c in random_part)

    def test_uniqueness(self, manager, mammal_id):
        """All generated codename_ids should be unique."""
        items = [
            CodenameInput(
                name=f"Animal{i}", name_en=f"Animal{i}", name_zh=f"动物{i}",
                category_id=mammal_id, brief=f"Animal {i}",
            )
            for i in range(50)
        ]
        result = manager.add_codenames(items)
        ids = result["codename_ids"]
        assert len(ids) == len(set(ids))


# ------------------------------------------------------------------
# list_inventory
# ------------------------------------------------------------------


class TestListInventory:
    def test_list_all(self, manager, sample_person, sample_animal):
        manager.add_codenames([sample_person, sample_animal])
        results = manager.list_inventory()
        assert len(results) == 2

    def test_filter_by_category_subtree(
        self, manager, sample_person, sample_animal
    ):
        manager.add_codenames([sample_person, sample_animal])
        person_top = _top_id(manager, "person")
        results = manager.list_inventory(category_id=person_top)
        assert len(results) == 1
        assert results[0].category_path[0] == "person"

    def test_filter_by_category_direct_only(
        self, manager, sample_person, sample_animal
    ):
        manager.add_codenames([sample_person, sample_animal])
        person_top = _top_id(manager, "person")
        # Direct-only on top-level excludes codenames on leaves
        results = manager.list_inventory(
            category_id=person_top, include_descendants=False
        )
        assert results == []

    def test_filter_by_status(self, manager, sample_person, sample_animal):
        result = manager.add_codenames([sample_person, sample_animal])
        manager.assign_codename(result["codename_ids"][0])
        available = manager.list_inventory(status="available")
        assigned = manager.list_inventory(status="assigned")
        assert len(available) == 1
        assert len(assigned) == 1

    def test_filter_by_leaf(self, manager, sample_person, science_id):
        manager.add_codenames([sample_person])
        results = manager.list_inventory(category_id=science_id)
        assert len(results) == 1

    def test_combined_filters(self, manager, sample_person, sample_animal):
        result = manager.add_codenames([sample_person, sample_animal])
        manager.assign_codename(result["codename_ids"][0])  # assign person
        person_top = _top_id(manager, "person")
        animal_top = _top_id(manager, "animal")
        results = manager.list_inventory(category_id=person_top, status="assigned")
        assert len(results) == 1
        results = manager.list_inventory(category_id=animal_top, status="assigned")
        assert len(results) == 0


# ------------------------------------------------------------------
# list_assignments
# ------------------------------------------------------------------


class TestListAssignments:
    def test_empty_assignments(self, manager):
        results = manager.list_assignments()
        assert results == []

    def test_list_after_assign(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        manager.assign_codename(cid, description="Test project")
        results = manager.list_assignments()
        assert len(results) == 1
        assert results[0].codename_id == cid
        assert results[0].description == "Test project"

    def test_multiple_assignments(self, manager, sample_person, sample_animal):
        result = manager.add_codenames([sample_person, sample_animal])
        for cid in result["codename_ids"]:
            manager.assign_codename(cid)
        results = manager.list_assignments()
        assert len(results) == 2


# ------------------------------------------------------------------
# boundary inputs
# ------------------------------------------------------------------


class TestBoundaryInputs:
    def test_search_sql_special_chars(self, manager, sample_person):
        """SQL LIKE wildcards % and _ should not cause errors."""
        manager.add_codenames([sample_person])
        results = manager.search("%")
        assert isinstance(results, list)
        results = manager.search("_")
        assert isinstance(results, list)

    def test_empty_string_brief(self, manager, mammal_id):
        """Empty string brief should be accepted by the model."""
        item = CodenameInput(
            name="Panda2", name_en="Panda2", name_zh="熊猫2",
            category_id=mammal_id, brief="",
        )
        result = manager.add_codenames([item])
        assert result["added"] == 1

    def test_long_name(self, manager, mammal_id):
        """Very long names should not cause errors."""
        long_name = "A" * 1000
        item = CodenameInput(
            name=long_name, name_en=long_name, name_zh="测试",
            category_id=mammal_id, brief="Test",
        )
        result = manager.add_codenames([item])
        assert result["added"] == 1
        results = manager.search(long_name[:50])
        assert len(results) == 1

    def test_unicode_names(self, manager, mammal_id):
        """Special Unicode characters should work."""
        item = CodenameInput(
            name="Phoenix", name_en="Phoenix", name_zh="凤凰",
            category_id=mammal_id, brief="A mythical bird of rebirth",
        )
        result = manager.add_codenames([item])
        assert result["added"] == 1
        results = manager.search("凤凰")
        assert len(results) == 1
