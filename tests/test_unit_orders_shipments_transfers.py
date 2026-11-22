"""Unittests voor de Orders, Shipments en Transfers models (rapport: Orders, Shipments, Transfers en 5.3).

Deze models halen hun items en voorraad op via data_provider. Hier vervangen we die
door kleine pools met eigen data, zodat we alleen de logica van het model testen.
"""
import pytest

from conftest import make_pool
from models.inventories import Inventories
from models.order_items import OrderItems
from models.orders import Orders
from models.shipment_items import ShipmentItems
from models.shipments import Shipments
from models.transfer_items import TransferItems
from models.transfers import Transfers
from providers import data_provider


def inventory(item_id, location_id, on_hand, allocated=0, ordered=0):
    return {
        "item_id": item_id,
        "location_id": location_id,
        "quantity_on_hand": on_hand,
        "quantity_expected": 0,
        "quantity_ordered": ordered,
        "quantity_allocated": allocated,
    }


@pytest.fixture
def pools(tmp_path, monkeypatch):
    inventories = make_pool(Inventories, "inventory", [
        inventory(1, 1, on_hand=10, allocated=2, ordered=2),
        inventory(1, 2, on_hand=50, allocated=4, ordered=4),
        inventory(2, 1, on_hand=5, allocated=1, ordered=1),
    ], tmp_path)
    order_items = make_pool(OrderItems, "order_item", [
        {"id": 1, "order_id": 1, "item_id": 1, "amount": 3, "unit_price": 2.5},
    ], tmp_path)
    shipment_items = make_pool(ShipmentItems, "shipment_item", [
        {"id": 1, "shipment_id": 1, "item_id": 1, "amount": 3},
    ], tmp_path)
    transfer_items = make_pool(TransferItems, "transfer_item", [
        {"id": 1, "transfer_id": 1, "item_id": 1, "amount": 3},
    ], tmp_path)

    monkeypatch.setattr(data_provider, "fetch_inventory_pool", lambda: inventories)
    monkeypatch.setattr(data_provider, "fetch_order_item_pool", lambda: order_items)
    monkeypatch.setattr(data_provider, "fetch_shipment_item_pool", lambda: shipment_items)
    monkeypatch.setattr(data_provider, "fetch_transfer_item_pool", lambda: transfer_items)
    return inventories


def get(pool, item_id, location_id, field):
    return pool.get_inventory(item_id, location_id)[field]


# ---------- Orders ----------

@pytest.fixture
def orders(pools, tmp_path):
    return make_pool(Orders, "order", [
        {"id": 1, "client_id": 1, "ship_to_client_id": 2, "bill_to_client_id": 3},
        {"id": 2, "client_id": 4, "ship_to_client_id": 4, "bill_to_client_id": 1},
        {"id": 3, "client_id": 5, "ship_to_client_id": 5, "bill_to_client_id": 5},
    ], tmp_path)


def test_order_has_items_without_unit_price(orders):
    assert orders.get_order(1)["items"] == [{"item_id": 1, "amount": 3}]


def test_order_without_items_has_empty_list(orders):
    assert orders.get_order(2)["items"] == []


def test_get_order_returns_copy(orders):
    orders.get_order(1)["client_id"] = 999
    assert "items" not in orders.data[0]
    assert orders.data[0]["client_id"] == 1


def test_get_unknown_order_returns_none(orders):
    assert orders.get_order(999) is None


def test_get_orders_all_have_items(orders):
    assert all("items" in x for x in orders.get_orders())


@pytest.mark.parametrize("client_id, expected", [(1, [1, 2]), (2, [1]), (5, [3]), (99, [])])
def test_orders_for_client_as_client_receiver_or_payer(orders, client_id, expected):
    assert [x["id"] for x in orders.get_orders_for_client(client_id)] == expected


def test_add_order_stores_items_separately(orders):
    orders.add_order({"id": 4, "client_id": 1, "items": [{"item_id": 2, "amount": 1}]})

    assert "items" not in orders.data[-1]
    assert "created_at" in orders.data[-1]
    assert orders.get_order(4)["items"] == [{"item_id": 2, "amount": 1}]


def test_add_order_does_not_allocate(orders, pools):
    # Alleen update_items_in_order past quantity_allocated aan
    orders.add_order({"id": 4, "client_id": 1, "items": [{"item_id": 1, "amount": 5}]})
    assert get(pools, 1, 2, "quantity_allocated") == 4


def test_update_order_without_items_keeps_items(orders):
    orders.update_order(1, {"id": 1, "client_id": 7})

    assert orders.get_order(1)["client_id"] == 7
    assert orders.get_order(1)["items"] == [{"item_id": 1, "amount": 3}]


def test_update_order_with_items_replaces_items(orders):
    orders.update_order(1, {"id": 1, "client_id": 1, "items": [{"item_id": 2, "amount": 1}]})
    assert orders.get_order(1)["items"] == [{"item_id": 2, "amount": 1}]


def test_more_items_allocates_on_location_with_most_stock(orders, pools):
    orders.update_items_in_order(1, [{"item_id": 1, "amount": 8}])

    assert get(pools, 1, 2, "quantity_allocated") == 4 + 5
    assert get(pools, 1, 1, "quantity_allocated") == 2


def test_fewer_items_lowers_allocation(orders, pools):
    orders.update_items_in_order(1, [{"item_id": 1, "amount": 1}])
    assert get(pools, 1, 2, "quantity_allocated") == 4 - 2


def test_removed_item_releases_allocation(orders, pools):
    orders.update_items_in_order(1, [{"item_id": 2, "amount": 1}])

    assert get(pools, 1, 2, "quantity_allocated") == 4 - 3
    assert get(pools, 2, 1, "quantity_allocated") == 1 + 1


def test_same_amount_changes_nothing(orders, pools):
    orders.update_items_in_order(1, [{"item_id": 1, "amount": 3}])
    assert get(pools, 1, 2, "quantity_allocated") == 4


def test_allocation_never_goes_below_zero(orders, pools):
    pools.get_inventory(1, 2)["quantity_allocated"] = 1
    orders.update_items_in_order(1, [])
    assert get(pools, 1, 2, "quantity_allocated") == 0


def test_item_without_inventory_is_ignored(orders, pools):
    before = [dict(x) for x in pools.get_inventories()]
    orders.update_items_in_order(2, [{"item_id": 99, "amount": 5}])

    assert pools.get_inventories() == before
    assert orders.get_order(2)["items"] == [{"item_id": 99, "amount": 5}]


def test_remove_order_also_removes_items(orders):
    orders.remove_order(1)

    assert orders.get_order(1) is None
    assert data_provider.fetch_order_item_pool().get_items_for_order(1) == []


# ---------- Shipments ----------

@pytest.fixture
def shipments(pools, tmp_path):
    return make_pool(Shipments, "shipment", [
        {"id": 1, "order_id": 1, "shipment_status": "Scheduled"},
        {"id": 2, "order_id": None, "shipment_status": "Transit"},
        {"id": 3, "shipment_status": "Delivered"},
    ], tmp_path)


def test_shipment_has_items(shipments):
    assert shipments.get_shipment(1)["items"] == [{"item_id": 1, "amount": 3}]


def test_get_unknown_shipment_returns_none(shipments):
    assert shipments.get_shipment(999) is None


@pytest.mark.parametrize("shipment_id, expected", [(1, [1]), (2, []), (3, []), (999, [])])
def test_order_ids_in_shipment(shipments, shipment_id, expected):
    assert shipments.get_order_ids_in_shipment(shipment_id) == expected


def test_update_orders_keeps_first_order(shipments):
    shipments.update_orders_in_shipment(1, [7, 8, 9])

    assert shipments.get_order_ids_in_shipment(1) == [7]
    assert "updated_at" in shipments.data[0]


def test_update_orders_with_empty_list_removes_link(shipments):
    shipments.update_orders_in_shipment(1, [])
    assert shipments.get_order_ids_in_shipment(1) == []


def test_add_shipment_stores_items_separately(shipments):
    shipments.add_shipment({"id": 4, "items": [{"item_id": 2, "amount": 1}]})

    assert "items" not in shipments.data[-1]
    assert shipments.get_shipment(4)["items"] == [{"item_id": 2, "amount": 1}]


def test_shipment_more_items_changes_ordered_on_location_with_most_stock(shipments, pools):
    shipments.update_items_in_shipment(1, [{"item_id": 1, "amount": 8}])

    assert get(pools, 1, 2, "quantity_ordered") == 4 + 5
    assert get(pools, 1, 2, "quantity_allocated") == 4


def test_shipment_removed_item_lowers_ordered(shipments, pools):
    shipments.update_items_in_shipment(1, [])
    assert get(pools, 1, 2, "quantity_ordered") == 4 - 3


def test_shipment_ordered_never_goes_below_zero(shipments, pools):
    pools.get_inventory(1, 2)["quantity_ordered"] = 0
    shipments.update_items_in_shipment(1, [])
    assert get(pools, 1, 2, "quantity_ordered") == 0


def test_update_shipment_with_items_changes_ordered(shipments, pools):
    shipments.update_shipment(1, {"id": 1, "order_id": 1, "items": [{"item_id": 1, "amount": 4}]})
    assert get(pools, 1, 2, "quantity_ordered") == 4 + 1


def test_remove_shipment_also_removes_items(shipments):
    shipments.remove_shipment(1)

    assert shipments.get_shipment(1) is None
    assert data_provider.fetch_shipment_item_pool().get_items_for_shipment(1) == []


# ---------- Transfers ----------

@pytest.fixture
def transfers(pools, tmp_path):
    return make_pool(Transfers, "transfer", [
        {"id": 1, "from_location_id": 1, "to_location_id": 2, "transfer_status": "Scheduled"},
    ], tmp_path)


def test_transfer_has_items(transfers):
    assert transfers.get_transfer(1)["items"] == [{"item_id": 1, "amount": 3}]


def test_get_unknown_transfer_returns_none(transfers):
    assert transfers.get_transfer(999) is None


def test_add_transfer_sets_status_scheduled(transfers):
    transfers.add_transfer({"id": 2, "transfer_status": "Processed"})

    transfer = transfers.get_transfer(2)
    assert transfer["transfer_status"] == "Scheduled"
    assert transfer["items"] == []


def test_add_transfer_does_not_touch_inventory(transfers, pools):
    before = [dict(x) for x in pools.get_inventories()]
    transfers.add_transfer({"id": 2, "items": [{"item_id": 1, "amount": 5}]})
    assert pools.get_inventories() == before


def test_update_transfer_keeps_given_status(transfers):
    # De status wordt bij een update niet gecontroleerd
    transfers.update_transfer(1, {"id": 1, "transfer_status": "Processed"})
    assert transfers.get_transfer(1)["transfer_status"] == "Processed"


def test_update_transfer_without_items_keeps_items(transfers):
    transfers.update_transfer(1, {"id": 1, "transfer_status": "Scheduled"})
    assert transfers.get_transfer(1)["items"] == [{"item_id": 1, "amount": 3}]


def test_update_transfer_with_items_replaces_items(transfers):
    transfers.update_transfer(1, {"id": 1, "items": [{"item_id": 2, "amount": 9}]})
    assert transfers.get_transfer(1)["items"] == [{"item_id": 2, "amount": 9}]


def test_remove_transfer_also_removes_items(transfers):
    transfers.remove_transfer(1)

    assert transfers.get_transfer(1) is None
    assert data_provider.fetch_transfer_item_pool().get_items_for_transfer(1) == []
