"""Reserveren van voorraad bij orders en shipments (rapport: Orders, Shipments en 5.3).

Deze tests gebruiken fixed_storage, omdat je door A1 anders niks van de wijziging terugziet.
"""
import pytest

from providers import data_provider


def get_inventory(item_id, location_id):
    return data_provider.fetch_inventory_pool().get_inventory(item_id, location_id)


def location_with_most_stock(item_id):
    inventories = data_provider.fetch_inventory_pool().get_inventories_for_item(item_id)
    return max(inventories, key=lambda x: x["quantity_on_hand"])["location_id"]


def test_put_order_items_allocates_on_location_with_most_stock(api, fixed_storage):
    location_id = location_with_most_stock(1)
    allocated_before = get_inventory(1, location_id)["quantity_allocated"]

    response = api.put("/orders/1/items", [{"item_id": 1, "amount": 5}], app="order_picker")

    assert response.status_code == 200
    assert get_inventory(1, location_id)["quantity_allocated"] == allocated_before + 5


@pytest.mark.xfail(strict=True, reason="Orders: POST /orders met items reserveert niks, alleen PUT /orders/{id}/items doet dat")
def test_post_order_allocates_same_as_put_order_items(api, fixed_storage):
    location_id = location_with_most_stock(1)
    allocated_before = get_inventory(1, location_id)["quantity_allocated"]
    order = {
        "id": 99999,
        "client_id": 1,
        "ship_to_client_id": 1,
        "bill_to_client_id": 1,
        "warehouse_id": 1,
        "order_status": "Pending",
        "items": [{"item_id": 1, "amount": 5}],
    }

    api.post("/orders", order, app="receiving_station")

    assert get_inventory(1, location_id)["quantity_allocated"] == allocated_before + 5


@pytest.mark.xfail(strict=True, reason="Orders: je kunt meer reserveren dan er op voorraad ligt")
def test_cannot_allocate_more_than_on_hand(api, fixed_storage):
    location_id = location_with_most_stock(1)
    inventory = get_inventory(1, location_id)
    amount = inventory["quantity_on_hand"] + 100

    api.put("/orders/1/items", [{"item_id": 1, "amount": amount}], app="order_picker")

    inventory = get_inventory(1, location_id)
    assert inventory["quantity_allocated"] <= inventory["quantity_on_hand"]


def test_put_shipment_items_changes_ordered_on_location_with_most_stock(api, fixed_storage):
    location_id = location_with_most_stock(1)
    ordered_before = get_inventory(1, location_id)["quantity_ordered"]

    response = api.put("/shipments/1/items", [{"item_id": 1, "amount": 5}], app="shipping_station")

    assert response.status_code == 200
    assert get_inventory(1, location_id)["quantity_ordered"] == ordered_before + 5


def test_put_shipment_orders_only_keeps_first_order(api, fixed_storage):
    # Shipments: de rest van de lijst wordt zonder melding genegeerd
    response = api.put("/shipments/1/orders", [10, 11], app="shipping_station")

    assert response.status_code == 200
    assert api.get("/shipments/1/orders").json() == [10]


@pytest.mark.xfail(strict=True, reason="Shipments: status mag vrij gekozen worden, Delivered kan terug naar Scheduled")
def test_delivered_shipment_cannot_go_back_to_scheduled(api, fixed_storage):
    shipment = api.get("/shipments/1").json()
    shipment["shipment_status"] = "Delivered"
    api.put("/shipments/1", shipment, app="shipping_station")

    shipment["shipment_status"] = "Scheduled"
    api.put("/shipments/1", shipment, app="shipping_station")

    assert api.get("/shipments/1").json()["shipment_status"] == "Delivered"
