"""Unittests voor auth_provider, data_provider en notification_processor (rapport: A1, A4 en 5.2)."""
import pytest

from conftest import load_json
from models.warehouses import Warehouses
from processors import notification_processor
from providers import auth_provider, data_provider

# ---------- auth_provider ----------

USER = {
    "api_key": "abc",
    "app": "test",
    "endpoint_access": {
        "warehouses": {"get": True, "post": False},
        "clients": {"get": True, "post": True, "put": True, "delete": True},
    },
}


def test_get_user_with_valid_key():
    user = load_json("user")[0]
    assert auth_provider.get_user(user["api_key"]) == user


@pytest.mark.parametrize("key", [None, "", "fout"])
def test_get_user_with_invalid_key_returns_none(key):
    assert auth_provider.get_user(key) is None


def test_get_user_reads_file_every_time(data_dir):
    # Er wordt niks gecached, een nieuwe gebruiker in user.json werkt meteen
    user_file = data_dir / "user.json"
    user_file.write_text('[{"api_key": "nieuw", "app": "x", "endpoint_access": {}}]')
    assert auth_provider.get_user("nieuw")["app"] == "x"


@pytest.mark.parametrize("paths, method, expected", [
    (["warehouses"], "get", True),
    (["warehouses", "1"], "post", False),
    (["warehouses"], "delete", False),
    (["clients", "1", "orders"], "delete", True),
    (["foo"], "get", False),
    ([""], "get", False),
])
def test_has_access(paths, method, expected):
    assert auth_provider.has_access(USER, paths, method) == expected


def test_has_access_with_unknown_method_is_false():
    assert not auth_provider.has_access(USER, ["clients"], "patch")


def test_has_access_without_paths_gives_error():
    with pytest.raises(IndexError):
        auth_provider.has_access(USER, [], "get")


# ---------- data_provider ----------

def test_fetch_uses_root_path(data_dir):
    pool = data_provider.fetch_warehouse_pool()
    assert isinstance(pool, Warehouses)
    assert pool.data_path == str(data_dir / "warehouse.json")


@pytest.mark.parametrize("name", [
    "warehouse", "location", "transfer", "transfer_item", "item", "item_line", "item_group",
    "item_type", "inventory", "supplier", "order", "order_item", "client", "shipment", "shipment_item",
])
def test_every_fetch_returns_a_new_object(name):
    # Dit is de oorzaak van A1: elke fetch leest het bestand opnieuw in
    fetch = getattr(data_provider, f"fetch_{name}_pool")
    assert fetch() is not fetch()


def test_change_on_one_object_is_not_seen_by_next_fetch():
    data_provider.fetch_warehouse_pool().add_warehouse({"id": 11})
    assert data_provider.fetch_warehouse_pool().get_warehouse(11) is None


def test_change_is_seen_after_save():
    pool = data_provider.fetch_warehouse_pool()
    pool.add_warehouse({"id": 11})
    pool.save()
    assert data_provider.fetch_warehouse_pool().get_warehouse(11) is not None


# ---------- notification_processor ----------

@pytest.fixture
def timers(monkeypatch):
    # threading.Timer wordt vervangen, zodat send() zichzelf niet echt opnieuw start
    timers = []

    class FakeTimer:
        def __init__(self, interval, function):
            timers.append((interval, function))

        def start(self):
            pass

    monkeypatch.setattr(notification_processor.threading, "Timer", FakeTimer)
    return timers


@pytest.fixture
def queue(monkeypatch, timers):
    queue = []
    monkeypatch.setattr(notification_processor, "_queue", queue)
    return queue


def test_push_adds_to_end_of_queue(queue):
    notification_processor.push("een")
    notification_processor.push("twee")
    assert queue == ["een", "twee"]


def test_send_prints_oldest_notification(queue, capsys):
    queue.extend(["een", "twee"])
    notification_processor.send()

    assert capsys.readouterr().out == "een\n"
    assert queue == ["twee"]


def test_send_with_empty_queue_prints_nothing(queue, capsys):
    notification_processor.send()
    assert capsys.readouterr().out == ""


def test_send_schedules_itself_again(queue, timers):
    notification_processor.send()
    assert timers == [(notification_processor.NOTIFICATION_UPDATE_INTERVAL_SEC, notification_processor.send)]


def test_start_sends_directly(queue, capsys):
    queue.append("direct")
    notification_processor.start()
    assert capsys.readouterr().out == "direct\n"
