import pytest

from app.core.config import get_settings
from app.main import app

PREFIX = get_settings().api_prefix

# Routes die al echt geïmplementeerd zijn en dus geen 501 geven.
IMPLEMENTED = {
    ("GET", "/warehouses"),
    ("GET", "/warehouses/{warehouse_id}"),
    ("POST", "/warehouses"),
    ("PUT", "/warehouses/{warehouse_id}"),
    ("DELETE", "/warehouses/{warehouse_id}"),
}


def _skeletons():
    for full_path, operations in app.openapi()["paths"].items():
        if not full_path.startswith(PREFIX):
            continue
        for method in operations:
            if (method.upper(), full_path.removeprefix(PREFIX)) not in IMPLEMENTED:
                yield method.upper(), full_path


SKELETONS = sorted(_skeletons())


def _fill(path: str) -> str:
    """Vervang elke {param} door 1."""
    return "/".join("1" if part.startswith("{") else part for part in path.split("/"))


def test_skeletons_are_registered():
    assert len(SKELETONS) == 68


@pytest.mark.parametrize("method,path", SKELETONS)
def test_skeleton_returns_501(client, auth_headers, method, path):
    assert client.request(method, _fill(path), headers=auth_headers).status_code == 501


@pytest.mark.parametrize("method,path", SKELETONS)
def test_skeleton_requires_api_key(client, method, path):
    assert client.request(method, _fill(path)).status_code in (401, 403)


def test_skeletons_are_documented():
    spec = app.openapi()["paths"]
    for method, path in SKELETONS:
        operation = spec[path][method.lower()]
        assert operation.get("summary"), f"{method} {path} mist summary"
        assert operation.get("description"), f"{method} {path} mist docstring"
