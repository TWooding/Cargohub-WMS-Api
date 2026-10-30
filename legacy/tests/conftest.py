import json
import os
import shutil
import socketserver
import threading
from pathlib import Path

import pytest
import requests

import main
from providers import auth_provider, data_provider

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "user.json") as f:
    API_KEYS = {user["app"]: user["api_key"] for user in json.load(f)}


def load_json(name):
    with open(DATA_DIR / f"{name}.json") as f:
        return json.load(f)


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def request(self, method, path, app="analytics_dashboard", body=None):
        headers = {"API_KEY": API_KEYS[app]}
        return requests.request(method, self.base_url + path, headers=headers, json=body, timeout=30)

    def get(self, path, app="analytics_dashboard"):
        return self.request("GET", path, app)

    def post(self, path, body, app="facility_management"):
        return self.request("POST", path, app, body)

    def put(self, path, body, app="facility_management"):
        return self.request("PUT", path, app, body)

    def delete(self, path, app="facility_management"):
        return self.request("DELETE", path, app)


@pytest.fixture(scope="session")
def server():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), main.ApiRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


# Elke test krijgt een eigen kopie van de data, zodat de echte data map nooit wordt aangepast
@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    copy = tmp_path / "data"
    shutil.copytree(DATA_DIR, copy)
    monkeypatch.setattr(data_provider, "ROOT_PATH", str(copy) + os.sep)
    monkeypatch.setattr(auth_provider, "ROOT_PATH", str(copy) + os.sep)
    return copy


@pytest.fixture
def api(server):
    return ApiClient(server + "/api/v1")


# Simuleert de fix voor A1: data_provider geeft steeds hetzelfde object terug.
# Hiermee kunnen we testen wat de API zou doen als schrijven wel werkt.
@pytest.fixture
def fixed_storage(data_dir, monkeypatch):
    transfers = data_provider.fetch_transfer_pool()
    transfer_items = data_provider.fetch_transfer_item_pool()
    inventories = data_provider.fetch_inventory_pool()
    orders = data_provider.fetch_order_pool()
    order_items = data_provider.fetch_order_item_pool()
    shipments = data_provider.fetch_shipment_pool()
    shipment_items = data_provider.fetch_shipment_item_pool()

    monkeypatch.setattr(data_provider, "fetch_transfer_pool", lambda: transfers)
    monkeypatch.setattr(data_provider, "fetch_transfer_item_pool", lambda: transfer_items)
    monkeypatch.setattr(data_provider, "fetch_inventory_pool", lambda: inventories)
    monkeypatch.setattr(data_provider, "fetch_order_pool", lambda: orders)
    monkeypatch.setattr(data_provider, "fetch_order_item_pool", lambda: order_items)
    monkeypatch.setattr(data_provider, "fetch_shipment_pool", lambda: shipments)
    monkeypatch.setattr(data_provider, "fetch_shipment_item_pool", lambda: shipment_items)
