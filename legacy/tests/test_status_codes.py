"""Statuscodes van v1 (rapport: A2, A3 en de tabel in 5.2).

Volgens het rapport blijft dit gedrag in /api/v1 bestaan en komt het nieuwe gedrag alleen in /api/v2.
Deze tests zorgen dat v1 hetzelfde blijft reageren.
"""
import pytest
import requests

from conftest import API_KEYS


def test_get_returns_json(api):
    response = api.get("/warehouses/1")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"


def test_unknown_id_gives_200_with_null(api):
    response = api.get("/warehouses/999")
    assert response.status_code == 200
    assert response.text == "null"


def test_post_gives_201_without_body(api):
    response = api.post("/warehouses", {"id": 11, "code": "TEST", "name": "Test"})
    assert response.status_code == 201
    assert response.text == ""


def test_put_unknown_id_gives_200(api):
    response = api.put("/warehouses/999", {"id": 999, "name": "Bestaat niet"})
    assert response.status_code == 200
    assert response.text == ""


def test_delete_unknown_id_gives_200(api):
    response = api.delete("/warehouses/999")
    assert response.status_code == 200
    assert response.text == ""


@pytest.mark.parametrize("path", ["/foo", "/users", "/warehouses?limit=2"])
def test_unknown_resource_gives_403(api, path):
    assert api.get(path).status_code == 403


@pytest.mark.parametrize("path", ["/warehouses/1/foo", "/warehouses/1/", "/inventories/1"])
def test_unknown_sub_path_gives_404(api, path):
    response = api.get(path)
    assert response.status_code == 404
    assert response.text == ""


def test_put_inventory_with_id_gives_404(api):
    response = api.put("/inventories/1", {"quantity_on_hand": 5}, app="receiving_station")
    assert response.status_code == 404


@pytest.mark.parametrize("path", ["/warehouses/abc", "/warehouses/", "/warehouses/1?x=1"])
def test_invalid_id_gives_500(api, path):
    response = api.get(path)
    assert response.status_code == 500
    assert response.text == ""


def test_broken_json_gives_500(server):
    headers = {"API_KEY": API_KEYS["facility_management"]}
    response = requests.post(server + "/api/v1/warehouses", data="{kapot", headers=headers)
    assert response.status_code == 500


@pytest.mark.parametrize("resource", ["orders", "transfers"])
def test_post_without_id_gives_500(api, resource):
    response = api.post(f"/{resource}", {"reference": "Zonder id"}, app="receiving_station")
    assert response.status_code == 500


@pytest.mark.parametrize("path", ["/api/v5/warehouses", "/warehouses"])
def test_path_outside_api_v1_gives_no_response(server, path):
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get(server + path, headers={"API_KEY": API_KEYS["facility_management"]})


def test_patch_gives_html_error_page(server):
    response = requests.patch(server + "/api/v1/warehouses/1", headers={"API_KEY": API_KEYS["facility_management"]})
    assert response.status_code == 501
    assert response.headers["Content-Type"].startswith("text/html")
