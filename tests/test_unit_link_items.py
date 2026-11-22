"""Unittests voor de koppeltabellen order_item, shipment_item en transfer_item (rapport: Data Model).

De drie models werken hetzelfde, alleen de naam van de sleutel verschilt.
"""
import pytest

from conftest import make_pool
from models.order_items import OrderItems
from models.shipment_items import ShipmentItems
from models.transfer_items import TransferItems

# model, bestandsnaam, naam van de sleutel en naam in de methodes
MODELS = [
    (OrderItems, "order_item", "order_id", "order"),
    (ShipmentItems, "shipment_item", "shipment_id", "shipment"),
    (TransferItems, "transfer_item", "transfer_id", "transfer"),
]


@pytest.fixture(params=MODELS, ids=[m[1] for m in MODELS])
def pool(request, tmp_path):
    cls, file, key, name = request.param
    rows = [
        {"id": 1, key: 1, "item_id": 10, "amount": 1},
        {"id": 5, key: 2, "item_id": 20, "amount": 2},
        {"id": 3, key: 1, "item_id": 30, "amount": 3},
    ]
    pool = make_pool(cls, file, rows, tmp_path)
    pool.key = key
    pool.get = getattr(pool, f"get_items_for_{name}")
    pool.set = getattr(pool, f"set_items_for_{name}")
    pool.remove = getattr(pool, f"remove_items_for_{name}")
    return pool


def test_get_items_for_parent(pool):
    assert [x["item_id"] for x in pool.get(1)] == [10, 30]
    assert pool.get(99) == []


def test_set_replaces_items_of_parent(pool):
    pool.set(1, [{"item_id": 40, "amount": 4}])

    assert [x["item_id"] for x in pool.get(1)] == [40]
    assert [x["item_id"] for x in pool.get(2)] == [20]


def test_set_gives_new_ids_after_highest_id(pool):
    pool.set(3, [{"item_id": 40, "amount": 4}, {"item_id": 50, "amount": 5}])
    assert [x["id"] for x in pool.get(3)] == [6, 7]


def test_set_on_empty_table_starts_at_id_1(pool):
    pool.data = []
    pool.set(1, [{"item_id": 40, "amount": 4}])
    assert pool.get(1)[0]["id"] == 1


def test_set_row_has_only_known_fields(pool):
    pool.set(3, [{"item_id": 40, "amount": 4, "foo": "bar"}])
    assert set(pool.get(3)[0].keys()) == {"id", pool.key, "item_id", "amount"}


def test_set_empty_list_removes_all_items(pool):
    pool.set(1, [])
    assert pool.get(1) == []


def test_set_without_amount_gives_error(pool):
    with pytest.raises(KeyError):
        pool.set(1, [{"item_id": 40}])


def test_remove_only_removes_items_of_parent(pool):
    pool.remove(1)

    assert pool.get(1) == []
    assert len(pool.get(2)) == 1


def test_debug_mode_starts_empty(tmp_path):
    for cls, _, _, _ in MODELS:
        assert cls(str(tmp_path) + "/", is_debug=True).data == []


def test_order_items_keep_unit_price(tmp_path):
    pool = make_pool(OrderItems, "order_item", [], tmp_path)
    pool.set_items_for_order(1, [{"item_id": 1, "amount": 2, "unit_price": 9.5}])
    assert pool.get_items_for_order(1)[0]["unit_price"] == 9.5


@pytest.mark.parametrize("cls, file, name", [
    (ShipmentItems, "shipment_item", "shipment"),
    (TransferItems, "transfer_item", "transfer"),
])
def test_shipment_and_transfer_items_drop_unit_price(tmp_path, cls, file, name):
    pool = make_pool(cls, file, [], tmp_path)
    getattr(pool, f"set_items_for_{name}")(1, [{"item_id": 1, "amount": 2, "unit_price": 9.5}])
    assert "unit_price" not in getattr(pool, f"get_items_for_{name}")(1)[0]
