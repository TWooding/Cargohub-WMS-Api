"""Unittests voor de simpele models zonder koppeltabel (rapport: Endpoints en Data Model).

Elk model krijgt eigen, kleine data via make_pool, zodat we de logica los van de API testen.
"""
import json
from datetime import datetime

import pytest

from conftest import make_pool
from models.base import Base
from models.clients import Clients
from models.item_groups import ItemGroups
from models.item_lines import ItemLines
from models.item_types import ItemTypes
from models.items import Items
from models.locations import Locations
from models.suppliers import Suppliers
from models.warehouses import Warehouses

# model, bestandsnaam en naam in de methodes (get_<naam>s, get_<naam>, add_<naam>, ...)
MODELS = [
    (Warehouses, "warehouse", "warehouse"),
    (Locations, "location", "location"),
    (Items, "item", "item"),
    (Clients, "client", "client"),
    (Suppliers, "supplier", "supplier"),
    (ItemLines, "item_line", "item_line"),
    (ItemGroups, "item_group", "item_group"),
    (ItemTypes, "item_type", "item_type"),
]

ROWS = [{"id": 1, "name": "Een"}, {"id": 2, "name": "Twee"}, {"id": 3, "name": "Drie"}]


def call(pool, action, name, *args):
    return getattr(pool, f"{action}_{name}")(*args)


@pytest.fixture(params=MODELS, ids=[m[1] for m in MODELS])
def model(request, tmp_path):
    cls, file, name = request.param
    rows = [dict(x) for x in ROWS]
    return make_pool(cls, file, rows, tmp_path), name, tmp_path / "unit" / f"{file}.json"


def test_timestamp_is_utc_iso_with_z():
    timestamp = Base.get_timestamp(None)
    assert timestamp.endswith("Z")
    datetime.fromisoformat(timestamp[:-1])


def test_base_cannot_be_created_directly():
    # Base.__init__ mist self, de models roepen hem daarom ook nooit aan
    with pytest.raises(TypeError):
        Base()


def test_load_reads_data_file(model):
    pool, name, _ = model
    assert call(pool, "get", name + "s") == ROWS


def test_get_one_by_id(model):
    pool, name, _ = model
    assert call(pool, "get", name, 2) == {"id": 2, "name": "Twee"}


def test_get_unknown_id_returns_none(model):
    pool, name, _ = model
    assert call(pool, "get", name, 999) is None


def test_get_id_as_string_returns_none(model):
    # Het id wordt niet omgezet, "1" is iets anders dan 1
    pool, name, _ = model
    assert call(pool, "get", name, "1") is None


def test_add_sets_created_and_updated_at(model):
    pool, name, _ = model
    call(pool, "add", name, {"id": 4, "name": "Vier"})

    record = call(pool, "get", name, 4)
    assert record["created_at"].endswith("Z")
    assert record["updated_at"].endswith("Z")
    assert len(call(pool, "get", name + "s")) == 4


def test_add_overwrites_created_at_from_body(model):
    pool, name, _ = model
    call(pool, "add", name, {"id": 4, "created_at": "2000-01-01T00:00:00Z"})
    assert call(pool, "get", name, 4)["created_at"] != "2000-01-01T00:00:00Z"


def test_update_sets_updated_at_and_keeps_position(model):
    pool, name, _ = model
    call(pool, "update", name, 2, {"id": 2, "name": "Nieuw"})

    records = call(pool, "get", name + "s")
    assert records[1]["name"] == "Nieuw"
    assert "updated_at" in records[1]
    assert "created_at" not in records[1]


def test_update_unknown_id_changes_nothing(model):
    pool, name, _ = model
    call(pool, "update", name, 999, {"id": 999, "name": "Bestaat niet"})
    assert call(pool, "get", name + "s") == ROWS


def test_remove_by_id(model):
    pool, name, _ = model
    call(pool, "remove", name, 2)
    assert [x["id"] for x in call(pool, "get", name + "s")] == [1, 3]


def test_remove_unknown_id_changes_nothing(model):
    pool, name, _ = model
    call(pool, "remove", name, 999)
    assert call(pool, "get", name + "s") == ROWS


@pytest.mark.xfail(strict=True, reason="remove_* haalt items weg tijdens het itereren, een dubbel id direct erna wordt overgeslagen")
def test_remove_removes_all_duplicate_ids(model):
    pool, name, _ = model
    pool.data = [{"id": 1}, {"id": 1}, {"id": 2}]
    call(pool, "remove", name, 1)
    assert call(pool, "get", name, 1) is None


def test_save_writes_data_file(model):
    pool, name, path = model
    call(pool, "add", name, {"id": 4, "name": "Vier"})
    pool.save()

    saved = json.loads(path.read_text())
    assert [x["id"] for x in saved] == [1, 2, 3, 4]


def test_debug_mode_shares_one_list_between_objects(tmp_path):
    # Met is_debug=True gebruiken alle objecten dezelfde lijst uit de module
    first = Warehouses(str(tmp_path) + "/", is_debug=True)
    second = Warehouses(str(tmp_path) + "/", is_debug=True)
    try:
        first.add_warehouse({"id": 1})
        assert second.get_warehouse(1) is not None
    finally:
        first.data.clear()


def test_missing_data_file_gives_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        Warehouses(str(tmp_path) + "/")


def test_locations_in_warehouse(tmp_path):
    rows = [
        {"id": 1, "warehouse_id": 1},
        {"id": 2, "warehouse_id": 2},
        {"id": 3, "warehouse_id": 1},
    ]
    locations = make_pool(Locations, "location", rows, tmp_path)

    assert [x["id"] for x in locations.get_locations_in_warehouse(1)] == [1, 3]
    assert locations.get_locations_in_warehouse(99) == []


ITEM_ROWS = [
    {"id": 1, "item_line_id": 1, "item_group_id": 1, "item_type_id": 1, "supplier_id": 1},
    {"id": 2, "item_line_id": 1, "item_group_id": 2, "item_type_id": 2, "supplier_id": 2},
    {"id": 3, "item_line_id": 2, "item_group_id": 1, "item_type_id": 1, "supplier_id": 1},
]


@pytest.mark.parametrize("method, expected", [
    ("get_items_for_item_line", [1, 2]),
    ("get_items_for_item_group", [1, 3]),
    ("get_items_for_item_type", [1, 3]),
])
def test_items_for_line_group_and_type_return_only_ids(tmp_path, method, expected):
    items = make_pool(Items, "item", ITEM_ROWS, tmp_path)
    assert getattr(items, method)(1) == expected


def test_items_for_supplier_return_full_items(tmp_path):
    items = make_pool(Items, "item", ITEM_ROWS, tmp_path)
    assert items.get_items_for_supplier(1) == [ITEM_ROWS[0], ITEM_ROWS[2]]


@pytest.mark.parametrize("method", [
    "get_items_for_item_line",
    "get_items_for_item_group",
    "get_items_for_item_type",
    "get_items_for_supplier",
])
def test_items_for_unknown_id_is_empty(tmp_path, method):
    items = make_pool(Items, "item", ITEM_ROWS, tmp_path)
    assert getattr(items, method)(99) == []
