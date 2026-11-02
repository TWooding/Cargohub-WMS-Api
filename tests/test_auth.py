"""Authenticatie en autorisatie met de API_KEY header (rapport: A4, 5.2 en Authenticatie en autorisatie)."""
import pytest
import requests

from conftest import load_json
from providers import auth_provider

# Rechten per app zoals in de tabel van 5.2: R = get, C = post, U = put, D = delete
EXPECTED_ACCESS = {
    "analytics_dashboard": {
        "warehouses": "R", "locations": "R", "clients": "R", "suppliers": "R",
        "item_lines": "R", "item_groups": "R", "item_types": "R", "items": "R",
        "inventories": "R", "transfers": "R", "orders": "R", "shipments": "R",
    },
    "facility_management": {
        "warehouses": "CRUD", "locations": "CRUD", "clients": "CRUD", "suppliers": "CRUD",
        "item_lines": "CRUD", "item_groups": "CRUD", "item_types": "CRUD", "items": "R",
        "inventories": "R", "transfers": "R", "orders": "R", "shipments": "R",
    },
    "receiving_station": {
        "warehouses": "R", "locations": "R", "clients": "R", "suppliers": "CRU",
        "item_lines": "CRU", "item_groups": "CRU", "item_types": "CRU", "items": "CRU",
        "inventories": "CRU", "transfers": "CRU", "orders": "CRU", "shipments": "CRU",
    },
    "shipping_station": {
        "warehouses": "R", "locations": "R", "clients": "CRU", "suppliers": "R",
        "item_lines": "R", "item_groups": "R", "item_types": "R", "items": "R",
        "inventories": "RU", "transfers": "CRU", "orders": "RU", "shipments": "CRU",
    },
    "order_picker": {
        "warehouses": "R", "locations": "R", "clients": "R", "suppliers": "R",
        "item_lines": "R", "item_groups": "R", "item_types": "R", "items": "R",
        "inventories": "RU", "transfers": "RU", "orders": "RU", "shipments": "R",
    },
    "smartglass_reader": {
        "warehouses": "R", "locations": "R", "clients": "R", "suppliers": "R",
        "item_lines": "R", "item_groups": "R", "item_types": "R", "items": "R",
        "inventories": "RU", "transfers": "RU", "orders": "R", "shipments": "R",
    },
}

LETTERS = {"get": "R", "post": "C", "put": "U", "delete": "D"}


def get_user(app):
    for user in load_json("user"):
        if user["app"] == app:
            return user


def test_missing_api_key_gives_401(server):
    response = requests.get(server + "/api/v1/warehouses")
    assert response.status_code == 401
    assert response.text == ""


def test_wrong_api_key_gives_401(server):
    response = requests.get(server + "/api/v1/warehouses", headers={"API_KEY": "fout"})
    assert response.status_code == 401


@pytest.mark.parametrize("app", EXPECTED_ACCESS.keys())
def test_rights_per_app(app):
    user = get_user(app)
    for resource, letters in EXPECTED_ACCESS[app].items():
        for method, letter in LETTERS.items():
            assert auth_provider.has_access(user, [resource], method) == (letter in letters), f"{app} {method} {resource}"


def test_nobody_can_delete_items_inventories_transfers_orders_or_shipments():
    for user in load_json("user"):
        for resource in ["items", "inventories", "transfers", "orders", "shipments"]:
            assert not auth_provider.has_access(user, [resource], "delete")


def test_read_only_app_gets_403_on_post(api):
    response = api.post("/clients", {"id": 999, "name": "Test"}, app="analytics_dashboard")
    assert response.status_code == 403
    assert response.text == ""


def test_delete_item_gives_403_for_facility_management(api):
    assert api.delete("/items/1", app="facility_management").status_code == 403


def test_rights_only_look_at_first_part_of_path():
    user = get_user("smartglass_reader")
    assert auth_provider.has_access(user, ["transfers", "1", "commit"], "put")


def test_smartglass_can_commit_any_transfer(api):
    # R4: commit valt onder transfers put, dus elke app met dat recht mag committen
    assert api.put("/transfers/1/commit", None, app="smartglass_reader").status_code == 200


def test_removed_key_in_user_file_is_refused_directly(api, data_dir):
    # Een sleutel intrekken kan alleen door user.json aan te passen (A4)
    user_file = data_dir / "user.json"
    key = get_user("analytics_dashboard")["api_key"]
    user_file.write_text(user_file.read_text().replace(key, "ingetrokken"))

    assert api.get("/warehouses", app="analytics_dashboard").status_code == 401
