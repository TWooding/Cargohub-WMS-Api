"""GET endpoints van v1: de vorm van de JSON moet gelijk blijven (rapport: hoofdstuk 3 Endpoints)."""
import pytest

from conftest import load_json


@pytest.mark.parametrize("path, expected", [
    ("/warehouses", 10),
    ("/locations", 400),
    ("/items", 600),
    ("/inventories", 4800),
    ("/suppliers", 21),
    ("/item_lines", 14),
    ("/item_groups", 3),
    ("/item_types", 3),
    ("/clients", 300),
])
def test_get_list(api, path, expected):
    response = api.get(path)
    assert response.status_code == 200
    assert len(response.json()) == expected


@pytest.mark.parametrize("resource, file", [
    ("warehouses", "warehouse"),
    ("locations", "location"),
    ("items", "item"),
    ("suppliers", "supplier"),
    ("clients", "client"),
    ("item_lines", "item_line"),
])
def test_get_one_returns_record_from_data(api, resource, file):
    response = api.get(f"/{resource}/1")
    assert response.json() == load_json(file)[0]


def test_get_locations_of_warehouse(api):
    locations = api.get("/warehouses/1/locations").json()
    assert len(locations) == 40
    assert all(x["warehouse_id"] == 1 for x in locations)


def test_get_inventory_of_item(api):
    inventories = api.get("/items/1/inventory").json()
    assert len(inventories) == 10
    assert all(x["item_id"] == 1 for x in inventories)


def test_get_inventory_totals_of_item(api):
    totals = api.get("/items/1/inventory/totals").json()
    assert set(totals.keys()) == {"total_expected", "total_ordered", "total_allocated", "total_available"}
    assert totals["total_available"] == 1018


def test_item_line_items_returns_only_ids(api):
    items = api.get("/item_lines/1/items").json()
    assert len(items) == 47
    assert all(isinstance(x, int) for x in items)


def test_supplier_items_returns_full_items(api):
    items = api.get("/suppliers/1/items").json()
    assert len(items) == 17
    assert all(x["supplier_id"] == 1 for x in items)


def test_get_transfer_with_items(api):
    transfer = api.get("/transfers/1").json()
    assert transfer["transfer_status"] == "Scheduled"
    assert transfer["items"] == [{"item_id": 190, "amount": 67}, {"item_id": 529, "amount": 58}]
    assert api.get("/transfers/1/items").json() == transfer["items"]


def test_get_order_with_items_without_unit_price(api):
    order = api.get("/orders/1").json()
    assert order["client_id"] == 123
    assert order["items"] == [{"item_id": 82, "amount": 24}]


def test_get_shipment_with_items(api):
    shipment = api.get("/shipments/1").json()
    assert shipment["shipment_type"] == "Outgoing"
    assert shipment["items"] == api.get("/shipments/1/items").json()


def test_shipment_orders_is_list_with_one_order(api):
    assert api.get("/shipments/1/orders").json() == [1]


def test_client_orders_also_returns_orders_as_receiver_or_payer(api):
    orders = api.get("/clients/1/orders").json()
    assert len(orders) == 57
    for order in orders:
        assert 1 in (order["client_id"], order["ship_to_client_id"], order["bill_to_client_id"])
    assert any(order["client_id"] != 1 for order in orders)
