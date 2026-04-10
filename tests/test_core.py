"""Tests for codename inventory core business logic."""

from pathlib import Path
import tempfile

import pytest

from codename_generator.core import CodenameManager
from codename_generator.models import CodenameInput


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


# ------------------------------------------------------------------
# add_codenames
# ------------------------------------------------------------------


class TestAddCodenames:
    def test_add_single(self, manager, sample_person):
        result = manager.add_codenames([sample_person])
        assert result["added"] == 1
        assert result["duplicates"] == []
        assert result["errors"] == []

    def test_add_batch(self, manager, sample_person, sample_animal):
        result = manager.add_codenames([sample_person, sample_animal])
        assert result["added"] == 2

    def test_duplicate_rejected(self, manager, sample_person):
        manager.add_codenames([sample_person])
        result = manager.add_codenames([sample_person])
        assert result["added"] == 0
        assert result["duplicates"] == ["Einstein"]

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
        manager.add_codenames([sample_person, sample_animal])
        manager.assign_codename("Einstein", "Project-A")
        results = manager.draw_random(count=10)
        assert len(results) == 1
        assert results[0].name == "Falcon"

    def test_draw_with_theme_filter(self, manager, sample_person, sample_animal):
        manager.add_codenames([sample_person, sample_animal])
        results = manager.draw_random(theme="animal", count=10)
        assert len(results) == 1
        assert results[0].theme == "animal"


# ------------------------------------------------------------------
# assign_codename (irreversible)
# ------------------------------------------------------------------


class TestAssignCodename:
    def test_assign_success(self, manager, sample_person):
        manager.add_codenames([sample_person])
        assignment = manager.assign_codename("Einstein", "Project-X")
        assert assignment.codename_name == "Einstein"
        assert assignment.project_name == "Project-X"

    def test_assign_changes_status(self, manager, sample_person):
        manager.add_codenames([sample_person])
        manager.assign_codename("Einstein", "Project-X")
        inventory = manager.list_inventory(status="available")
        assert len(inventory) == 0
        inventory = manager.list_inventory(status="assigned")
        assert len(inventory) == 1

    def test_assign_nonexistent_fails(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.assign_codename("Ghost", "Project-X")

    def test_assign_already_assigned_fails(self, manager, sample_person):
        manager.add_codenames([sample_person])
        manager.assign_codename("Einstein", "Project-X")
        with pytest.raises(ValueError, match="already assigned"):
            manager.assign_codename("Einstein", "Project-Y")

    def test_assign_project_already_has_codename(self, manager, sample_person, sample_animal):
        manager.add_codenames([sample_person, sample_animal])
        manager.assign_codename("Einstein", "Project-X")
        with pytest.raises(ValueError, match="already has codename"):
            manager.assign_codename("Falcon", "Project-X")


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
        manager.add_codenames([sample_person])
        logs = manager.get_logs()
        assert len(logs) == 1
        assert logs[0].action == "added"
        assert logs[0].codename == "Einstein"

    def test_assign_creates_log(self, manager, sample_person):
        manager.add_codenames([sample_person])
        manager.assign_codename("Einstein", "Project-X")
        logs = manager.get_logs(action="assigned")
        assert len(logs) == 1
        assert logs[0].codename == "Einstein"

    def test_log_filter_by_action(self, manager, sample_person):
        manager.add_codenames([sample_person])
        manager.assign_codename("Einstein", "Project-X")
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
