"""Tests for codename inventory core business logic."""

from pathlib import Path
import json
import tempfile

import pytest

from codename_generator.core import CodenameManager
from codename_generator.models import CodenameInput, CodenameUpdate


@pytest.fixture
def manager(tmp_path):
    """Create a manager with a temporary database."""
    db_path = tmp_path / "test.db"
    return CodenameManager(db_path)


@pytest.fixture
def sample_person():
    return CodenameInput(
        name="Einstein",
        name_en="Einstein",
        name_zh="爱因斯坦",
        theme="person",
        sub_theme="science",
        brief="Theoretical physicist who developed the theory of relativity",
    )


@pytest.fixture
def sample_animal():
    return CodenameInput(
        name="Falcon",
        name_en="Falcon",
        name_zh="猎隼",
        theme="animal",
        brief="A fast bird of prey known for incredible diving speed",
    )


def _add_one(manager, item):
    """Add a single codename and return its codename_id."""
    result = manager.add_codenames([item])
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

    def test_person_requires_sub_theme(self, manager):
        item = CodenameInput(
            name="Curie",
            name_en="Curie",
            name_zh="居里",
            theme="person",
            sub_theme=None,
            brief="Physicist and chemist",
        )
        result = manager.add_codenames([item])
        assert result["added"] == 0
        assert len(result["errors"]) == 1
        assert "sub_theme" in result["errors"][0]

    def test_animal_no_sub_theme_needed(self, manager, sample_animal):
        result = manager.add_codenames([sample_animal])
        assert result["added"] == 1


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
        assert results[0].name == "Falcon"

    def test_draw_with_theme_filter(self, manager, sample_person, sample_animal):
        manager.add_codenames([sample_person, sample_animal])
        results = manager.draw_random(theme="animal", count=10)
        assert len(results) == 1
        assert results[0].theme == "animal"

    def test_draw_returns_codename_id(self, manager, sample_person):
        manager.add_codenames([sample_person])
        results = manager.draw_random(count=1)
        assert results[0].codename_id.startswith("CN-")


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

    def test_stats_after_add(self, manager, sample_person, sample_animal):
        manager.add_codenames([sample_person, sample_animal])
        stats = manager.get_inventory_stats()
        assert stats.total == 2
        assert stats.available == 2
        assert stats.assigned == 0
        assert stats.by_theme == {"person": 1, "animal": 1}

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
        logs = manager.get_logs()
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
        assert len(all_logs) == 2
        added_logs = manager.get_logs(action="added")
        assert len(added_logs) == 1


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

    def test_update_nonexistent_fails(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.update_codename(CodenameUpdate(codename_id="CN-NOTEXIST", brief="New brief"))

    def test_update_no_fields_fails(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        with pytest.raises(ValueError, match="No fields to update"):
            manager.update_codename(CodenameUpdate(codename_id=cid))

    def test_update_person_to_animal_clears_sub_theme(self, manager, sample_person):
        cid = _add_one(manager, sample_person)
        result = manager.update_codename(CodenameUpdate(codename_id=cid, theme="animal"))
        assert result.theme == "animal"
        assert result.sub_theme is None

    def test_update_animal_to_person_requires_sub_theme(self, manager, sample_animal):
        cid = _add_one(manager, sample_animal)
        with pytest.raises(ValueError, match="sub_theme"):
            manager.update_codename(CodenameUpdate(codename_id=cid, theme="person"))

    def test_update_animal_to_person_with_sub_theme(self, manager, sample_animal):
        cid = _add_one(manager, sample_animal)
        result = manager.update_codename(
            CodenameUpdate(codename_id=cid, theme="person", sub_theme="science")
        )
        assert result.theme == "person"
        assert result.sub_theme == "science"

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
        assert logs[0].action == "updated"

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

    def test_uses_alphanumeric_only(self, manager):
        """codename_id should only contain CN- prefix + alphanumeric chars."""
        import string
        items = [
            CodenameInput(
                name=f"Test{i}", name_en=f"Test{i}", name_zh=f"测试{i}",
                theme="animal", brief=f"Test animal {i}",
            )
            for i in range(20)
        ]
        result = manager.add_codenames(items)
        valid_chars = set(string.ascii_letters + string.digits)
        for cid in result["codename_ids"]:
            random_part = cid[3:]  # strip CN-
            assert all(c in valid_chars for c in random_part)

    def test_uniqueness(self, manager):
        """All generated codename_ids should be unique."""
        items = [
            CodenameInput(
                name=f"Animal{i}", name_en=f"Animal{i}", name_zh=f"动物{i}",
                theme="animal", brief=f"Animal number {i}",
            )
            for i in range(50)
        ]
        result = manager.add_codenames(items)
        ids = result["codename_ids"]
        assert len(ids) == len(set(ids))
