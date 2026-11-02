"""Transfers en de commit (rapport: Transfers, 5.3 en risico R2).

De meeste tests gebruiken fixed_storage, omdat je door A1 anders niks van de commit terugziet.
"""
import pytest

from providers import data_provider


def get_on_hand(item_id, location_id):
    inventory = data_provider.fetch_inventory_pool().get_inventory(item_id, location_id)
    if inventory is None:
        return None
    return inventory["quantity_on_hand"]


def create_transfer(api, transfer_id, from_location_id, to_location_id, amount):
    transfer = {
        "id": transfer_id,
        "reference": f"TRF-TEST-{transfer_id}",
        "from_location_id": from_location_id,
        "to_location_id": to_location_id,
        "items": [{"item_id": 1, "amount": amount}],
    }
    return api.post("/transfers", transfer, app="receiving_station")


def test_new_transfer_always_gets_status_scheduled(api, fixed_storage):
    transfer = {
        "id": 9001,
        "reference": "TRF-TEST",
        "from_location_id": 171,
        "to_location_id": 154,
        "transfer_status": "Processed",
        "items": [{"item_id": 1, "amount": 10}],
    }
    api.post("/transfers", transfer, app="receiving_station")
    assert api.get("/transfers/9001").json()["transfer_status"] == "Scheduled"


def test_commit_moves_inventory(api, fixed_storage):
    source_before = get_on_hand(1, 171)
    target_before = get_on_hand(1, 154)
    create_transfer(api, 9001, 171, 154, 10)
    response = api.put("/transfers/9001/commit", None, app="smartglass_reader")

    assert response.status_code == 200
    assert get_on_hand(1, 171) == source_before - 10
    assert get_on_hand(1, 154) == target_before + 10
    assert api.get("/transfers/9001").json()["transfer_status"] == "Processed"


def test_commit_to_location_without_inventory_creates_row(api, fixed_storage):
    assert get_on_hand(1, 1) is None
    create_transfer(api, 9001, 171, 1, 10)
    api.put("/transfers/9001/commit", None, app="smartglass_reader")
    assert get_on_hand(1, 1) == 10


@pytest.mark.xfail(strict=True, reason="R2: dezelfde transfer kan meerdere keren uitgevoerd worden")
def test_commit_twice_moves_inventory_once(api, fixed_storage):
    source_before = get_on_hand(1, 171)
    create_transfer(api, 9001, 171, 154, 10)
    api.put("/transfers/9001/commit", None, app="smartglass_reader")
    api.put("/transfers/9001/commit", None, app="smartglass_reader")
    assert get_on_hand(1, 171) == source_before - 10


@pytest.mark.xfail(strict=True, reason="R2: geen check op genoeg voorraad, bronlocatie kan negatief worden")
def test_commit_with_too_little_inventory_does_not_go_negative(api, fixed_storage):
    create_transfer(api, 9001, 171, 154, get_on_hand(1, 171) + 100)
    api.put("/transfers/9001/commit", None, app="smartglass_reader")
    assert get_on_hand(1, 171) >= 0


@pytest.mark.xfail(strict=True, reason="R2: bronlocatie zonder voorraadregel, toch voorraad op de doellocatie")
def test_commit_from_empty_location_does_not_create_inventory(api, fixed_storage):
    target_before = get_on_hand(1, 154)
    create_transfer(api, 9001, 1, 154, 10)
    api.put("/transfers/9001/commit", None, app="smartglass_reader")
    assert get_on_hand(1, 154) == target_before


@pytest.mark.xfail(strict=True, reason="Transfers: PUT laat elke status toe, ook Processed zonder dat voorraad beweegt")
def test_put_transfer_cannot_set_status_processed(api, fixed_storage):
    transfer = api.get("/transfers/1").json()
    transfer["transfer_status"] = "Processed"
    api.put("/transfers/1", transfer, app="order_picker")
    assert api.get("/transfers/1").json()["transfer_status"] == "Scheduled"
