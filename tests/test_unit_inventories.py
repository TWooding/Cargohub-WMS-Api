"""Unittests voor het Inventories model (rapport: Data Model en 5.3).

Een voorraadregel heeft geen id, de sleutel is de combinatie item_id en location_id.
"""
import pytest

from conftest import make_pool
from models.inventories import Inventories


def row(item_id, location_id, on_hand=10, expected=0, ordered=0, allocated=0):
    return {
        "item_id": item_id,
        "location_id": location_id,
        "quantity_on_hand": on_hand,
        "quantity_expected": expected,
        "quantity_ordered": ordered,
        "quantity_allocated": allocated,
    }


@pytest.fixture
def inventories(tmp_path):
    rows = [
        row(1, 1, on_hand=10, expected=1, ordered=2, allocated=3),
        row(1, 2, on_hand=20, expected=4, ordered=5, allocated=6),
        row(2, 1, on_hand=30),
    ]
    return make_pool(Inventories, "inventory", rows, tmp_path)


def test_get_inventory_by_item_and_location(inventories):
    assert inventories.get_inventory(1, 2)["quantity_on_hand"] == 20


def test_get_inventory_unknown_combination_returns_none(inventories):
    assert inventories.get_inventory(2, 2) is None


def test_inventories_for_item(inventories):
    assert [x["location_id"] for x in inventories.get_inventories_for_item(1)] == [1, 2]
    assert inventories.get_inventories_for_item(99) == []


def test_totals_for_item(inventories):
    assert inventories.get_inventory_totals_for_item(1) == {
        "total_expected": 5,
        "total_ordered": 7,
        "total_allocated": 9,
        "total_available": (10 - 3) + (20 - 6),
    }


def test_totals_for_unknown_item_are_zero(inventories):
    assert set(inventories.get_inventory_totals_for_item(99).values()) == {0}


def test_total_available_can_be_negative(tmp_path):
    # Er wordt niet gecontroleerd of er meer gereserveerd is dan er ligt
    inventories = make_pool(Inventories, "inventory", [row(1, 1, on_hand=5, allocated=8)], tmp_path)
    assert inventories.get_inventory_totals_for_item(1)["total_available"] == -3


def test_add_new_combination_appends_row(inventories):
    inventories.add_inventory(row(2, 2, on_hand=7))

    assert len(inventories.get_inventories()) == 4
    inventory = inventories.get_inventory(2, 2)
    assert inventory["quantity_on_hand"] == 7
    assert "created_at" in inventory and "updated_at" in inventory


def test_add_existing_combination_updates_row(inventories):
    inventories.add_inventory(row(1, 1, on_hand=99))

    assert len(inventories.get_inventories()) == 3
    assert inventories.get_inventory(1, 1)["quantity_on_hand"] == 99


@pytest.mark.xfail(strict=True, reason="add_inventory overschrijft created_at van een bestaande voorraadregel")
def test_add_existing_combination_keeps_created_at(inventories):
    inventories.get_inventory(1, 1)["created_at"] = "2000-01-01T00:00:00Z"
    inventories.add_inventory(row(1, 1, on_hand=99))
    assert inventories.get_inventory(1, 1)["created_at"] == "2000-01-01T00:00:00Z"


def test_update_replaces_row(inventories):
    inventories.update_inventory(1, 1, {"item_id": 1, "location_id": 1, "quantity_on_hand": 0})

    inventory = inventories.get_inventory(1, 1)
    assert inventory["quantity_on_hand"] == 0
    assert "quantity_allocated" not in inventory
    assert "updated_at" in inventory


def test_update_unknown_combination_changes_nothing(inventories):
    before = [dict(x) for x in inventories.get_inventories()]
    inventories.update_inventory(9, 9, row(9, 9))
    assert inventories.get_inventories() == before


def test_remove_only_removes_that_combination(inventories):
    inventories.remove_inventory(1, 1)

    assert inventories.get_inventory(1, 1) is None
    assert inventories.get_inventory(1, 2) is not None
    assert inventories.get_inventory(2, 1) is not None


def test_save_and_load_again(inventories, tmp_path):
    inventories.add_inventory(row(3, 3))
    inventories.save()

    again = Inventories(str(tmp_path / "unit") + "/")
    assert again.get_inventory(3, 3) is not None
