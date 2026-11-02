"""Schrijven via POST, PUT en DELETE (rapport: A1, A3, 5.3 en 6.2)."""
import pytest

from providers import data_provider

A1 = "A1/R1: schrijven geeft 200/201 maar wordt niet opgeslagen (main.py:399-400)"


@pytest.mark.xfail(strict=True, reason=A1)
def test_post_warehouse_can_be_found_with_get(api):
    api.post("/warehouses", {"id": 11, "code": "TEST", "name": "Test magazijn"})
    assert api.get("/warehouses/11").json() is not None


@pytest.mark.xfail(strict=True, reason=A1)
def test_put_warehouse_changes_name(api):
    warehouse = api.get("/warehouses/1").json()
    warehouse["name"] = "Nieuwe naam"
    api.put("/warehouses/1", warehouse)
    assert api.get("/warehouses/1").json()["name"] == "Nieuwe naam"


@pytest.mark.xfail(strict=True, reason=A1)
def test_delete_warehouse_removes_it(api):
    api.delete("/warehouses/10")
    assert api.get("/warehouses/10").json() is None


@pytest.mark.xfail(strict=True, reason=A1)
def test_post_inventory_can_be_found_with_get(api):
    inventory = {
        "item_id": 1,
        "location_id": 1,
        "quantity_on_hand": 10,
        "quantity_expected": 0,
        "quantity_ordered": 0,
        "quantity_allocated": 0,
    }
    api.post("/inventories", inventory, app="receiving_station")
    location_ids = [x["location_id"] for x in api.get("/items/1/inventory").json()]
    assert 1 in location_ids


@pytest.mark.xfail(strict=True, reason=A1)
def test_commit_transfer_changes_status(api):
    api.put("/transfers/1/commit", None, app="smartglass_reader")
    assert api.get("/transfers/1").json()["transfer_status"] == "Processed"


@pytest.mark.xfail(strict=True, reason=A1)
def test_post_warehouse_is_written_to_data_file(api, data_dir):
    api.post("/warehouses", {"id": 11, "code": "TEST", "name": "Test magazijn"})
    assert '"code": "TEST"' in (data_dir / "warehouse.json").read_text()


@pytest.mark.parametrize("path", ["/clients/1", "/warehouses/1", "/suppliers/1", "/item_lines/1"])
def test_delete_with_linked_records_is_not_blocked(api, path):
    # Er hangen nog orders, locaties of artikelen aan, maar er komt geen 409
    assert api.delete(path).status_code == 200


def test_put_replaces_whole_record():
    warehouses = data_provider.fetch_warehouse_pool()
    warehouses.update_warehouse(1, {"id": 1, "name": "Alleen een naam"})
    warehouse = warehouses.get_warehouse(1)

    assert warehouse["name"] == "Alleen een naam"
    assert "code" not in warehouse
    assert "created_at" not in warehouse


def test_put_accepts_other_id_in_body_than_in_path():
    warehouses = data_provider.fetch_warehouse_pool()
    warehouses.update_warehouse(1, {"id": 99, "name": "Ander id"})

    assert warehouses.get_warehouse(1) is None
    assert warehouses.get_warehouse(99)["name"] == "Ander id"


def test_post_accepts_duplicate_id_and_get_returns_first():
    warehouses = data_provider.fetch_warehouse_pool()
    original_name = warehouses.get_warehouse(1)["name"]
    warehouses.add_warehouse({"id": 1, "name": "Dubbel"})

    assert len(warehouses.get_warehouses()) == 11
    assert warehouses.get_warehouse(1)["name"] == original_name
