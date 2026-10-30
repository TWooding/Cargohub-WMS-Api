# Postman library — CargoHUB WMS API v1

| File | What it is |
| --- | --- |
| `CargoHUB-WMS-API.postman_collection.json` | 87 requests over all 12 resources, plus an auth/error folder and a transfer-commit scenario |
| `CargoHUB-local.postman_environment.json` | `base_url` and one variable per app key in `data/user.json` |
| `generate_postman.py` | Generator. Re-run after changing the routes in `api/main.py` or the seed data |

## Use it

1. Start the API: `./start-system.sh` (listens on `http://localhost:3000`).
2. In Postman: **Import** both JSON files, then select the *CargoHUB - local*
   environment.
3. Open any request and send it — every request already carries an `API_KEY`
   that is allowed to make that specific call.

Headless, with [newman](https://github.com/postmanlabs/newman):

```sh
npx newman@6 run postman/CargoHUB-WMS-API.postman_collection.json \
  -e postman/CargoHUB-local.postman_environment.json
```

A full run takes a few minutes: `GET /orders` and `GET /shipments` return the
whole table with every line item inlined (~5–6k records), and the server is
single-threaded.

## Regenerate

```sh
python3 postman/generate_postman.py
```

Request bodies come from the first record of the matching `data/*.json` file and
the API keys straight out of `data/user.json`, so the collection cannot drift
from the dataset. Route coverage is hand-maintained in the folder builders at the
bottom of the script.

## Notes on the API this describes

- Authorisation is checked on the **first path segment only**, before routing, so
  `GET /api/v1/nonsense` answers 403 rather than 404.
- `DELETE` is granted to `facility_management` only. On transfers, items, orders,
  shipments and inventories no existing key can delete, so those requests expect
  a 403 and say so in their description.
- `GET /<resource>/<unknown id>` is a 200 with a `null` body.
- `PUT` replaces the whole record; the nested writes
  (`PUT /orders/{id}/items`, `PUT /shipments/{id}/items|orders`) take a bare JSON
  array.
- **Writes do not persist.** Each handler mutates one pool instance and then
  calls `data_provider.fetch_*_pool().save()`, which loads a fresh instance from
  disk and writes that back — so a 201/200 comes back but `data/` is only
  rewritten in compact form. Step 5 of the scenario folder asserts the intended
  behaviour and therefore fails against the API as it stands; it is the one
  expected failure in a full run (126 assertions, 125 green).
