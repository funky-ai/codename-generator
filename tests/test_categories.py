"""Tests for category CRUD, tree invariants, and re-parenting rules."""

import pytest

from codename_generator.core import CodenameManager
from codename_generator.models import (
    CategoryInput,
    CategoryUpdate,
    CodenameInput,
)


@pytest.fixture
def manager(tmp_path):
    """Manager with seeded default categories."""
    return CodenameManager(tmp_path / "test.db")


def _by_slug(manager: CodenameManager, slug: str, top_level: bool):
    """Resolve a seeded category by slug + whether it's top-level."""
    for c in manager.list_categories():
        is_top = c.parent_category_id is None
        if c.slug == slug and is_top == top_level:
            return c
    raise KeyError(f"Category slug={slug} top={top_level} not found")


# ------------------------------------------------------------------
# TestCreateCategory
# ------------------------------------------------------------------


class TestCreateCategory:
    def test_create_top_level(self, manager):
        cat = manager.create_category(
            CategoryInput(slug="mythic", name_en="Mythic", name_zh="神话")
        )
        assert cat.slug == "mythic"
        assert cat.depth == 1
        assert cat.parent_category_id is None
        assert cat.is_archived is False
        assert cat.category_id.startswith("CAT-")

    def test_create_child(self, manager):
        person_top = _by_slug(manager, "person", top_level=True)
        cat = manager.create_category(
            CategoryInput(
                slug="martial_arts",
                name_en="Martial Arts",
                name_zh="武术",
                parent_category_id=person_top.category_id,
            )
        )
        assert cat.depth == 2
        assert cat.parent_category_id == person_top.category_id

    def test_duplicate_slug_same_parent_rejected(self, manager):
        with pytest.raises(ValueError, match="already exists"):
            manager.create_category(
                CategoryInput(slug="person", name_en="P2", name_zh="人2")
            )

    def test_duplicate_slug_different_parent_ok(self, manager):
        # slug 'science' exists under 'person'; can we also put it under 'animal'?
        animal_top = _by_slug(manager, "animal", top_level=True)
        cat = manager.create_category(
            CategoryInput(
                slug="science",
                name_en="Science-A",
                name_zh="科学-A",
                parent_category_id=animal_top.category_id,
            )
        )
        assert cat.parent_category_id == animal_top.category_id

    def test_depth_limit_on_create(self, manager):
        mammal = _by_slug(manager, "mammal", top_level=False)
        whale = manager.create_category(
            CategoryInput(
                slug="whale", name_en="Whale", name_zh="鲸",
                parent_category_id=mammal.category_id,
            )
        )
        assert whale.depth == 3
        with pytest.raises(ValueError, match="depth"):
            manager.create_category(
                CategoryInput(
                    slug="bluewhale", name_en="Blue", name_zh="蓝",
                    parent_category_id=whale.category_id,
                )
            )

    def test_create_under_archived_parent_rejected(self, manager):
        math = _by_slug(manager, "mathematics", top_level=False)
        manager.update_category(math.category_id, CategoryUpdate(is_archived=True))
        with pytest.raises(ValueError, match="archived"):
            manager.create_category(
                CategoryInput(
                    slug="algebra", name_en="Algebra", name_zh="代数",
                    parent_category_id=math.category_id,
                )
            )

    def test_create_unknown_parent_rejected(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.create_category(
                CategoryInput(
                    slug="x", name_en="X", name_zh="X",
                    parent_category_id="CAT-nonexist",
                )
            )


# ------------------------------------------------------------------
# TestUpdateCategory
# ------------------------------------------------------------------


class TestUpdateCategory:
    def test_rename(self, manager):
        sci = _by_slug(manager, "science", top_level=False)
        result = manager.update_category(
            sci.category_id, CategoryUpdate(name_en="Natural Science")
        )
        assert result.name_en == "Natural Science"
        assert result.slug == "science"  # unchanged

    def test_slug_rename(self, manager):
        sci = _by_slug(manager, "science", top_level=False)
        result = manager.update_category(
            sci.category_id, CategoryUpdate(slug="natural-science")
        )
        assert result.slug == "natural-science"

    def test_slug_rename_conflict(self, manager):
        sci = _by_slug(manager, "science", top_level=False)
        with pytest.raises(ValueError, match="already exists"):
            manager.update_category(
                sci.category_id, CategoryUpdate(slug="art")
            )

    def test_reparent(self, manager):
        eng = _by_slug(manager, "engineering", top_level=False)
        animal_top = _by_slug(manager, "animal", top_level=True)
        result = manager.update_category(
            eng.category_id,
            CategoryUpdate(parent_category_id=animal_top.category_id),
        )
        assert result.parent_category_id == animal_top.category_id

    def test_reparent_to_top_level(self, manager):
        eng = _by_slug(manager, "engineering", top_level=False)
        result = manager.update_category(
            eng.category_id, CategoryUpdate(parent_category_id="")
        )
        assert result.parent_category_id is None
        assert result.depth == 1

    def test_reparent_cycle_self(self, manager):
        person_top = _by_slug(manager, "person", top_level=True)
        with pytest.raises(ValueError, match="cycle"):
            manager.update_category(
                person_top.category_id,
                CategoryUpdate(parent_category_id=person_top.category_id),
            )

    def test_reparent_cycle_descendant(self, manager):
        person_top = _by_slug(manager, "person", top_level=True)
        sci = _by_slug(manager, "science", top_level=False)
        with pytest.raises(ValueError, match="cycle"):
            manager.update_category(
                person_top.category_id,
                CategoryUpdate(parent_category_id=sci.category_id),
            )

    def test_reparent_depth_exceeded(self, manager):
        # Set up: animal > mammal > whale (depth 3). Try to move mammal subtree
        # under person's science leaf — new_parent_depth=2, subtree_height=2,
        # total=4 → reject.
        mammal = _by_slug(manager, "mammal", top_level=False)
        manager.create_category(
            CategoryInput(
                slug="whale", name_en="Whale", name_zh="鲸",
                parent_category_id=mammal.category_id,
            )
        )
        sci = _by_slug(manager, "science", top_level=False)
        with pytest.raises(ValueError, match="depth"):
            manager.update_category(
                mammal.category_id,
                CategoryUpdate(parent_category_id=sci.category_id),
            )

    def test_reparent_allowed_same_tree_top_to_top_valid(self, manager):
        # Build a 3-deep chain: root1 > midA > leafA. Detach midA → top-level.
        root = manager.create_category(
            CategoryInput(slug="root1", name_en="R1", name_zh="根1")
        )
        mid = manager.create_category(
            CategoryInput(
                slug="midA", name_en="Mid", name_zh="中",
                parent_category_id=root.category_id,
            )
        )
        manager.create_category(
            CategoryInput(
                slug="leafA", name_en="Leaf", name_zh="叶",
                parent_category_id=mid.category_id,
            )
        )
        result = manager.update_category(
            mid.category_id, CategoryUpdate(parent_category_id="")
        )
        assert result.parent_category_id is None
        assert result.depth == 1

    def test_archive_toggle(self, manager):
        math = _by_slug(manager, "mathematics", top_level=False)
        result = manager.update_category(
            math.category_id, CategoryUpdate(is_archived=True)
        )
        assert result.is_archived is True
        result = manager.update_category(
            math.category_id, CategoryUpdate(is_archived=False)
        )
        assert result.is_archived is False

    def test_archive_refuses_when_codenames_bound(self, manager):
        sci = _by_slug(manager, "science", top_level=False)
        manager.add_codenames(
            [CodenameInput(
                name="E", name_en="E", name_zh="E",
                category_id=sci.category_id, brief="x",
            )]
        )
        with pytest.raises(ValueError, match="codenames"):
            manager.update_category(
                sci.category_id, CategoryUpdate(is_archived=True)
            )

    def test_no_fields_rejected(self, manager):
        sci = _by_slug(manager, "science", top_level=False)
        with pytest.raises(ValueError, match="No fields"):
            manager.update_category(sci.category_id, CategoryUpdate())

    def test_not_found(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.update_category(
                "CAT-nonexist", CategoryUpdate(name_en="x")
            )


# ------------------------------------------------------------------
# TestDeleteCategory
# ------------------------------------------------------------------


class TestDeleteCategory:
    def test_delete_empty_leaf(self, manager):
        math = _by_slug(manager, "mathematics", top_level=False)
        manager.delete_category(math.category_id)
        with pytest.raises(KeyError):
            _by_slug(manager, "mathematics", top_level=False)

    def test_delete_top_with_children_rejected(self, manager):
        person_top = _by_slug(manager, "person", top_level=True)
        with pytest.raises(ValueError, match="subcategories"):
            manager.delete_category(person_top.category_id)

    def test_delete_leaf_with_codenames_rejected(self, manager):
        sci = _by_slug(manager, "science", top_level=False)
        manager.add_codenames(
            [CodenameInput(
                name="E", name_en="E", name_zh="E",
                category_id=sci.category_id, brief="x",
            )]
        )
        with pytest.raises(ValueError, match="codenames"):
            manager.delete_category(sci.category_id)

    def test_delete_archived_children_also_rejects(self, manager):
        # Even though archived, subcategories still block delete since we
        # only allow delete when zero non-archived children AND zero codenames.
        # This test ensures the non-archived check actually filters archived.
        mammal = _by_slug(manager, "mammal", top_level=False)
        whale = manager.create_category(
            CategoryInput(
                slug="whale", name_en="Whale", name_zh="鲸",
                parent_category_id=mammal.category_id,
            )
        )
        manager.update_category(
            whale.category_id, CategoryUpdate(is_archived=True)
        )
        # mammal now has one archived child — delete should succeed? Actually
        # we require archiving the child doesn't unblock deletion because the
        # FK RESTRICT still catches it. Confirm we get a friendly error.
        with pytest.raises(ValueError):
            manager.delete_category(mammal.category_id)

    def test_not_found(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.delete_category("CAT-nonexist")


# ------------------------------------------------------------------
# TestCategoryTree
# ------------------------------------------------------------------


class TestCategoryTree:
    def test_tree_shape(self, manager):
        roots = manager.get_category_tree()
        assert len(roots) == 2
        top_slugs = {r.slug for r in roots}
        assert top_slugs == {"person", "animal"}
        person = next(r for r in roots if r.slug == "person")
        assert person.children is not None
        leaf_slugs = {c.slug for c in person.children}
        assert "science" in leaf_slugs

    def test_tree_excludes_archived_by_default(self, manager):
        math = _by_slug(manager, "mathematics", top_level=False)
        manager.update_category(math.category_id, CategoryUpdate(is_archived=True))
        roots = manager.get_category_tree()
        person = next(r for r in roots if r.slug == "person")
        leaf_slugs = {c.slug for c in (person.children or [])}
        assert "mathematics" not in leaf_slugs

    def test_tree_includes_archived_when_requested(self, manager):
        math = _by_slug(manager, "mathematics", top_level=False)
        manager.update_category(math.category_id, CategoryUpdate(is_archived=True))
        roots = manager.get_category_tree(include_archived=True)
        person = next(r for r in roots if r.slug == "person")
        leaf_slugs = {c.slug for c in (person.children or [])}
        assert "mathematics" in leaf_slugs
