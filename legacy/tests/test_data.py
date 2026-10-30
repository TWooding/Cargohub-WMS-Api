"""Huidige staat van de data in de data map (rapport: Endpoints, Data Model en 5.3)."""
from collections import Counter

import pytest

from conftest import load_json


@pytest.mark.parametrize("name, expected", [
    ("warehouse", 10),
    ("location", 400),
    ("item", 600),
    ("inventory", 4800),
    ("supplier", 21),
    ("item_line", 14),
    ("item_group", 3),
    ("item_type", 3),
    ("client", 300),
    ("order", 4854),
    ("shipment", 6132),
    ("transfer", 800),
    ("user", 6),
])
def test_amount_of_records(name, expected):
    assert len(load_json(name)) == expected


@pytest.mark.parametrize("name", ["warehouse", "location", "item", "supplier", "client", "order", "shipment", "transfer"])
def test_ids_are_unique(name):
    ids = [x["id"] for x in load_json(name)]
    assert len(ids) == len(set(ids))


def test_every_warehouse_has_40_locations():
    counts = Counter(x["warehouse_id"] for x in load_json("location"))
    assert len(counts) == 10
    assert all(count == 40 for count in counts.values())


def test_inventory_has_no_id_but_item_and_location_are_unique():
    inventories = load_json("inventory")
    keys = {(x["item_id"], x["location_id"]) for x in inventories}

    assert all("id" not in x for x in inventories)
    assert len(keys) == len(inventories)


def test_no_negative_inventory():
    for x in load_json("inventory"):
        assert x["quantity_on_hand"] >= 0
        assert x["quantity_allocated"] >= 0


def test_statuses_in_data():
    assert {x["order_status"] for x in load_json("order")} == {"Pending", "Shipped"}
    assert {x["transfer_status"] for x in load_json("transfer")} == {"Scheduled", "Processed"}

    shipments = load_json("shipment")
    assert {x["shipment_status"] for x in shipments} == {"Scheduled", "Transit", "Delivered"}
    assert {x["shipment_type"] for x in shipments} == {"Incoming", "Outgoing"}


def test_orders_shared_by_multiple_shipments():
    counts = Counter(x["order_id"] for x in load_json("shipment"))
    shared = [order_id for order_id, count in counts.items() if count > 1]
    assert len(shared) == 2263


def test_order_has_three_clients():
    order = load_json("order")[0]
    assert "client_id" in order
    assert "ship_to_client_id" in order
    assert "bill_to_client_id" in order


def test_supplier_uses_other_field_names_than_client_and_warehouse():
    supplier = load_json("supplier")[0]
    client = load_json("client")[0]
    warehouse = load_json("warehouse")[0]

    assert "phone_number" in supplier
    assert "contact_phone" not in supplier
    assert "contact_email" not in supplier
    assert "contact_phone" in client
    assert "contact_phone" in warehouse


def test_references_between_data_are_valid():
    warehouse_ids = {x["id"] for x in load_json("warehouse")}
    location_ids = {x["id"] for x in load_json("location")}
    item_ids = {x["id"] for x in load_json("item")}
    client_ids = {x["id"] for x in load_json("client")}

    for location in load_json("location"):
        assert location["warehouse_id"] in warehouse_ids
    for inventory in load_json("inventory"):
        assert inventory["item_id"] in item_ids
        assert inventory["location_id"] in location_ids
    for order in load_json("order"):
        assert order["client_id"] in client_ids
        assert order["warehouse_id"] in warehouse_ids
    for transfer in load_json("transfer"):
        assert transfer["from_location_id"] in location_ids
        assert transfer["to_location_id"] in location_ids


def test_users_are_six_apps_with_plain_api_key():
    users = load_json("user")
    apps = {x["app"] for x in users}

    assert apps == {
        "analytics_dashboard",
        "smartglass_reader",
        "order_picker",
        "receiving_station",
        "shipping_station",
        "facility_management",
    }
    for user in users:
        assert set(user.keys()) == {"api_key", "app", "endpoint_access"}
