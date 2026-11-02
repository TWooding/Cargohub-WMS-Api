WAREHOUSE = {
    "code": "YQZZNL56",
    "name": "Heemskerk cargo hub",
    "address": "Karlijndreef 281",
    "city": "Heemskerk",
    "zip_code": "4002 AS",
    "province": "Friesland",
    "country": "NL",
    "contact_name": "Fem Keijzer",
    "contact_phone": "(078) 0013363",
    "contact_email": "blamore@example.net",
}


def test_requires_api_key(client):
    assert client.get("/api/v2/warehouses").status_code == 401
    assert client.get("/api/v2/warehouses", headers={"API_KEY": "wrong"}).status_code == 401


def test_crud(client, auth_headers):
    created = client.post("/api/v2/warehouses", json=WAREHOUSE, headers=auth_headers)
    assert created.status_code == 201
    warehouse_id = created.json()["id"]

    fetched = client.get(f"/api/v2/warehouses/{warehouse_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == WAREHOUSE["name"]

    updated = client.put(f"/api/v2/warehouses/{warehouse_id}", json={"city": "Rotterdam"}, headers=auth_headers)
    assert updated.status_code == 200
    assert updated.json()["city"] == "Rotterdam"
    assert updated.json()["code"] == WAREHOUSE["code"]

    assert len(client.get("/api/v2/warehouses", headers=auth_headers).json()) == 1

    assert client.delete(f"/api/v2/warehouses/{warehouse_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/v2/warehouses/{warehouse_id}", headers=auth_headers).status_code == 404


def test_create_validation(client, auth_headers):
    response = client.post("/api/v2/warehouses", json={"name": "only a name"}, headers=auth_headers)
    assert response.status_code == 422
