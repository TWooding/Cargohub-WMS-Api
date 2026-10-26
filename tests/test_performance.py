"""Snelheid van de API (rapport: A5, 5.3 en risico R3)."""
import time

import pytest

from providers import data_provider


@pytest.mark.parametrize("path", ["/warehouses", "/items"])
def test_small_lists_are_fast(api, path):
    start = time.time()
    response = api.get(path)
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 1


@pytest.mark.xfail(strict=True, reason="A5/R3: get_orders() leest order_item.json opnieuw in voor elke order (orders.py:13-27)")
def test_get_orders_reads_order_items_only_once(monkeypatch):
    original = data_provider.fetch_order_item_pool
    calls = []

    def counting_fetch():
        calls.append(1)
        return original()

    monkeypatch.setattr(data_provider, "fetch_order_item_pool", counting_fetch)
    orders = data_provider.fetch_order_pool()
    orders.data = orders.data[:5]
    orders.get_orders()

    assert len(calls) <= 1
