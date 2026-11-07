"""Generate the Postman collection + environment for the CargoHUB WMS API.

The request bodies and API keys are read straight out of `data/*.json` so the
collection stays in sync with the dataset the API actually serves. Re-run after
changing the routes in api/main.py or the seed data:

    python3 postman/generate_postman.py
"""

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "postman")

COLLECTION_NAME = "CargoHUB WMS API v1"
SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"


# --------------------------------------------------------------------------
# seed data helpers
# --------------------------------------------------------------------------

def load(name):
    with open(os.path.join(DATA, name), "r") as f:
        return json.load(f)


def record(name, **overrides):
    """First seed record, with `overrides` applied and nulls kept as-is."""
    row = dict(load(name)[0])
    row.update(overrides)
    return row


def post_body(name, items_key=None, items=None):
    """A create body: fresh id, no timestamps (the API stamps those itself)."""
    row = record(name)
    row.pop("created_at", None)
    row.pop("updated_at", None)
    if "id" in row:
        row["id"] = "__NEW_ID__"
    if items_key is not None:
        row[items_key] = items
    return row


def put_body(name, **overrides):
    """An update body. PUT replaces the whole record, so send every field."""
    return record(name, **overrides)


# Preference order when several app keys may call a route: the widest-scoped
# writer first, so the collection uses as few different keys as possible.
KEY_PREFERENCE = [
    "receiving_station",
    "shipping_station",
    "facility_management",
    "order_picker",
    "smartglass_reader",
    "analytics_dashboard",
]


def _access():
    return {u["app"]: u["endpoint_access"] for u in load("user.json")}


ACCESS = _access()


def key_for(resource, method):
    """The API_KEY variable to use for `resource`/`method`, and whether any app
    key is actually allowed to call it. `resource` is the first path segment -
    that is all has_access() looks at, sub-routes inherit the parent's flags."""
    for app in KEY_PREFERENCE:
        perms = ACCESS[app].get(resource)
        if perms and perms.get(method.lower(), False):
            return "{{api_key_%s}}" % app, True
    # Nothing grants it: use the widest writer so the 403 is about the flag and
    # not about an unknown key.
    return "{{api_key_receiving_station}}", False


def jsonify(body):
    """Render a body, un-quoting the {{new_id}} placeholder so Postman
    substitutes a number instead of a string."""
    text = json.dumps(body, indent=2, ensure_ascii=False)
    return text.replace('"__NEW_ID__"', "{{new_id}}")


# --------------------------------------------------------------------------
# request builders
# --------------------------------------------------------------------------

def tests(*lines):
    return {
        "listen": "test",
        "script": {"type": "text/javascript", "exec": list(lines)},
    }


def prerequest(*lines):
    return {
        "listen": "prerequest",
        "script": {"type": "text/javascript", "exec": list(lines)},
    }


def auto_request(name, method, segments, expect, body=None, description="",
                 extra_tests=None, events=None):
    """A request whose expected status collapses to 403 when no app key is
    allowed to call the route at all."""
    key, allowed = key_for(segments[0], method)
    if not allowed:
        expect = 403
        description = (description + "\n\n" if description else "") + (
            f"**No app key in data/user.json grants {method} on "
            f"`{segments[0]}`**, so this route is unreachable and answers 403. "
            "The handler behind it does exist."
        )
        events = [status_test(403, extra=None)]
    elif events is None:
        events = [status_test(expect, extra_tests)]
    return request(name, method, segments, body=body,
                   description=description, events=events, api_key=key)


def status_test(code, extra=None):
    lines = [
        f"pm.test('status is {code}', function () {{",
        f"    pm.response.to.have.status({code});",
        "});",
    ]
    if extra:
        lines += ["", *extra]
    return tests(*lines)


def json_array_test(code=200):
    return status_test(code, [
        "pm.test('body is a JSON array', function () {",
        "    pm.expect(pm.response.json()).to.be.an('array');",
        "});",
    ])


def json_object_test(code=200, *required):
    extra = [
        "pm.test('body is a JSON object', function () {",
        "    pm.expect(pm.response.json()).to.be.an('object');",
        "});",
    ]
    if required:
        extra += [
            "pm.test('has the expected fields', function () {",
            "    const body = pm.response.json();",
        ]
        extra += [f"    pm.expect(body).to.have.property('{f}');" for f in required]
        extra += ["});"]
    return tests(*status_test(code)["script"]["exec"], "", *extra)


def request(name, method, segments, body=None, description="",
            events=None, api_key="__AUTO__", headers=None):
    if api_key == "__AUTO__":
        api_key, _ = key_for(segments[0], method)
    raw_path = "/".join(["{{base_url}}", "api", "v1", *segments])
    item = {
        "name": name,
        "request": {
            "method": method,
            "header": list(headers or []),
            "url": {
                "raw": raw_path,
                "host": ["{{base_url}}"],
                "path": ["api", "v1", *segments],
            },
            "description": description,
        },
    }
    if api_key is not None:
        item["request"]["header"].append(
            {"key": "API_KEY", "value": api_key, "type": "text"}
        )
    if body is not None:
        item["request"]["header"].append(
            {"key": "Content-Type", "value": "application/json", "type": "text"}
        )
        item["request"]["body"] = {
            "mode": "raw",
            "raw": jsonify(body),
            "options": {"raw": {"language": "json"}},
        }
    if events:
        item["event"] = events
    return item


def folder(name, items, description=""):
    return {"name": name, "item": items, "description": description}


def new_id_script(slug):
    """Give a POST a collision-free id and remember it for the PUT/DELETE."""
    return [
        prerequest(
            "// Fresh id so the create can be re-run without colliding with",
            "// the seed data (ids there are well below 900000).",
            "pm.collectionVariables.set('new_id', 900000 + Math.floor(Math.random() * 99999));",
        ),
        status_test(201, [
            f"// Remember the id so 'Update {slug}' / 'Delete {slug}' can target it.",
            f"pm.collectionVariables.set('created_{slug}_id', pm.collectionVariables.get('new_id'));",
        ]),
    ]


# --------------------------------------------------------------------------
# resource definitions
# --------------------------------------------------------------------------

# Every resource that is a plain CRUD collection: list / detail / create /
# update / delete, optionally with read-only sub-resources and extra routes.
RESOURCES = [
    {
        "name": "Warehouses",
        "path": "warehouses",
        "file": "warehouse.json",
        "slug": "warehouse",
        "id_var": "warehouse_id",
        "subs": [("locations", "Locations in warehouse",
                  "Every location row whose warehouse_id matches.")],
    },
    {
        "name": "Locations",
        "path": "locations",
        "file": "location.json",
        "slug": "location",
        "id_var": "location_id",
    },
    {
        "name": "Items",
        "path": "items",
        "file": "item.json",
        "slug": "item",
        "id_var": "item_id",
        "subs": [
            ("inventory", "Inventory for item",
             "All inventory rows (one per location) holding this item."),
        ],
        "extra_gets": [
            (["items", "{{item_id}}", "inventory", "totals"],
             "Inventory totals for item",
             "Aggregated totals across every location: total_expected, "
             "total_ordered, total_allocated and total_available "
             "(on_hand - allocated).",
             json_object_test(200, "total_expected", "total_ordered",
                              "total_allocated", "total_available")),
        ],
    },
    {
        "name": "Item lines",
        "path": "item_lines",
        "file": "item_line.json",
        "slug": "item_line",
        "id_var": "item_line_id",
        "subs": [("items", "Items in item line", "Items with this item_line_id.")],
    },
    {
        "name": "Item groups",
        "path": "item_groups",
        "file": "item_group.json",
        "slug": "item_group",
        "id_var": "item_group_id",
        "subs": [("items", "Items in item group", "Items with this item_group_id.")],
    },
    {
        "name": "Item types",
        "path": "item_types",
        "file": "item_type.json",
        "slug": "item_type",
        "id_var": "item_type_id",
        "subs": [("items", "Items of item type", "Items with this item_type_id.")],
    },
    {
        "name": "Suppliers",
        "path": "suppliers",
        "file": "supplier.json",
        "slug": "supplier",
        "id_var": "supplier_id",
        "subs": [("items", "Items from supplier", "Items with this supplier_id.")],
    },
    {
        "name": "Clients",
        "path": "clients",
        "file": "client.json",
        "slug": "client",
        "id_var": "client_id",
        "subs": [("orders", "Orders for client",
                  "Orders where the client is the ordering, ship-to or "
                  "bill-to party.")],
    },
]


def crud_folder(spec):
    path, id_var, slug = spec["path"], spec["id_var"], spec["slug"]
    detail = [path, "{{%s}}" % id_var]
    write_target = [path, "{{%s_write_id}}" % slug]
    items = [
        auto_request(f"List {path}", "GET", [path], 200,
                     description=f"All {path}. No pagination or filtering - the "
                                 "full seed set comes back in one response.",
                     events=[json_array_test()]),
        auto_request(f"Get {slug} by id", "GET", detail, 200,
                     description="Single record. An unknown id is a 200 with a "
                                 "`null` body, not a 404.",
                     events=[json_object_test()]),
    ]
    for seg, name, desc in spec.get("subs", []):
        items.append(auto_request(name, "GET", detail + [seg], 200,
                                  description=desc, events=[json_array_test()]))
    for segments, name, desc, test in spec.get("extra_gets", []):
        items.append(auto_request(name, "GET", segments, 200,
                                  description=desc, events=[test]))

    items.append(auto_request(
        f"Create {slug}", "POST", [path], 201, body=post_body(spec["file"]),
        description="`created_at` / `updated_at` are set server-side; the `id` "
                    "must be in the body. Returns 201 with an empty body.",
        events=new_id_script(slug)))
    items.append(auto_request(
        f"Update {slug}", "PUT", write_target, 200,
        body=put_body(spec["file"], id="__NEW_ID__"),
        description=f"Full replace of `{path}/{{{{{slug}_write_id}}}}` - PUT "
                    "overwrites the whole record, so send every field. Point "
                    f"`{slug}_write_id` at the row you want to edit.",
        events=[
            prerequest(
                "// Keep the id in the body equal to the id in the URL.",
                f"pm.collectionVariables.set('new_id', pm.collectionVariables.get('{slug}_write_id'));",
            ),
            status_test(200),
        ]))
    items.append(auto_request(
        f"Delete {slug}", "DELETE", write_target, 200,
        description="Returns 200 whether or not the id existed."))
    return folder(spec["name"], items)


# --------------------------------------------------------------------------
# resources with hand-written extras
# --------------------------------------------------------------------------

def transfers_folder():
    return folder("Transfers", [
        auto_request("List transfers", "GET", ["transfers"], 200,
                     description="Every transfer, each with its `items` array "
                                 "inlined from transfer_item.json.",
                     events=[json_array_test()]),
        auto_request("Get transfer by id", "GET", ["transfers", "{{transfer_id}}"],
                     200, description="Single transfer including its `items`.",
                     events=[json_object_test()]),
        auto_request("Items in transfer", "GET",
                     ["transfers", "{{transfer_id}}", "items"], 200,
                     description="Just the `{item_id, amount}` rows.",
                     events=[json_array_test()]),
        auto_request("Create transfer", "POST", ["transfers"], 201,
                     body=post_body("transfer.json", "items",
                                    [{"item_id": 190, "amount": 67}]),
                     description="`transfer_status` is forced to `Scheduled` and "
                                 "the timestamps are set server-side. `items` is "
                                 "split off into transfer_item.json. Also pushes "
                                 "a message onto the notification worker.",
                     events=new_id_script("transfer")),
        auto_request("Update transfer", "PUT",
                     ["transfers", "{{transfer_write_id}}"], 200,
                     body=put_body("transfer.json", id="__NEW_ID__",
                                   transfer_status="Scheduled"),
                     description="Full replace. Include `items` to replace the "
                                 "transfer lines too; omit it to keep them.",
                     events=[
                         prerequest("pm.collectionVariables.set('new_id', pm.collectionVariables.get('transfer_write_id'));"),
                         status_test(200),
                     ]),
        auto_request("Commit transfer", "PUT",
                     ["transfers", "{{transfer_write_id}}", "commit"], 200,
                     description="No request body. For every transfer line it "
                                 "subtracts `amount` from `quantity_on_hand` at "
                                 "`from_location_id` and adds it at "
                                 "`to_location_id` (creating that inventory row "
                                 "if needed), sets `transfer_status` to "
                                 "`Processed` and notifies the worker. Not "
                                 "idempotent: committing twice moves the stock "
                                 "twice."),
        auto_request("Delete transfer", "DELETE",
                     ["transfers", "{{transfer_write_id}}"], 200),
    ], "Transfers move stock between two locations. `commit` is the route that "
       "actually touches inventory.")


def orders_folder():
    return folder("Orders", [
        auto_request("List orders", "GET", ["orders"], 200,
                     description="Every order with its `items` inlined. ~4.8k "
                                 "records, so expect a large response.",
                     events=[json_array_test()]),
        auto_request("Get order by id", "GET", ["orders", "{{order_id}}"], 200,
                     events=[json_object_test()]),
        auto_request("Items in order", "GET",
                     ["orders", "{{order_id}}", "items"], 200,
                     description="The `{item_id, amount}` lines of the order.",
                     events=[json_array_test()]),
        auto_request("Create order", "POST", ["orders"], 201,
                     body=post_body("order.json", "items",
                                    [{"item_id": 82, "amount": 24}]),
                     description="`items` is split off into order_item.json.",
                     events=new_id_script("order")),
        auto_request("Update order", "PUT", ["orders", "{{order_write_id}}"], 200,
                     body=put_body("order.json", id="__NEW_ID__"),
                     description="Full replace. Including `items` also runs the "
                                 "allocation sync described below.",
                     events=[
                         prerequest("pm.collectionVariables.set('new_id', pm.collectionVariables.get('order_write_id'));"),
                         status_test(200),
                     ]),
        auto_request("Update items in order", "PUT",
                     ["orders", "{{order_write_id}}", "items"], 200,
                     body=[{"item_id": 82, "amount": 12},
                           {"item_id": 119, "amount": 6}],
                     description="Body is a bare JSON array of `{item_id, "
                                 "amount}`. Replaces all order lines and shifts "
                                 "`quantity_allocated` by the delta on the "
                                 "inventory row that holds the most stock for "
                                 "each item."),
        auto_request("Delete order", "DELETE", ["orders", "{{order_write_id}}"],
                     200),
    ])


def shipments_folder():
    return folder("Shipments", [
        auto_request("List shipments", "GET", ["shipments"], 200,
                     description="Every shipment with its `items` inlined. ~6.1k "
                                 "records.",
                     events=[json_array_test()]),
        auto_request("Get shipment by id", "GET",
                     ["shipments", "{{shipment_id}}"], 200,
                     events=[json_object_test()]),
        auto_request("Orders in shipment", "GET",
                     ["shipments", "{{shipment_id}}", "orders"], 200,
                     description="`shipment.order_id` is 1:1 in this schema, so "
                                 "the array holds at most one order id.",
                     events=[json_array_test()]),
        auto_request("Items in shipment", "GET",
                     ["shipments", "{{shipment_id}}", "items"], 200,
                     events=[json_array_test()]),
        auto_request("Create shipment", "POST", ["shipments"], 201,
                     body=post_body("shipment.json", "items",
                                    [{"item_id": 82, "amount": 6}]),
                     events=new_id_script("shipment")),
        auto_request("Update shipment", "PUT",
                     ["shipments", "{{shipment_write_id}}"], 200,
                     body=put_body("shipment.json", id="__NEW_ID__"),
                     events=[
                         prerequest("pm.collectionVariables.set('new_id', pm.collectionVariables.get('shipment_write_id'));"),
                         status_test(200),
                     ]),
        auto_request("Update orders in shipment", "PUT",
                     ["shipments", "{{shipment_write_id}}", "orders"], 200,
                     body=[1],
                     description="Body is a bare JSON array of order ids."),
        auto_request("Update items in shipment", "PUT",
                     ["shipments", "{{shipment_write_id}}", "items"], 200,
                     body=[{"item_id": 82, "amount": 3}],
                     description="Body is a bare JSON array of `{item_id, "
                                 "amount}`. Replaces the shipment lines and "
                                 "keeps `quantity_ordered` in sync on the "
                                 "inventory row with the most stock for each "
                                 "item."),
        auto_request("Delete shipment", "DELETE",
                     ["shipments", "{{shipment_write_id}}"], 200),
    ])


def inventories_folder():
    inv = post_body("inventory.json")
    inv["item_id"] = 119
    inv["location_id"] = 399
    return folder("Inventories", [
        auto_request("List inventories", "GET", ["inventories"], 200,
                     description="All ~4.8k inventory rows.",
                     events=[json_array_test()]),
        auto_request("Create / upsert inventory", "POST", ["inventories"], 201,
                     body=inv,
                     description="Keyed on the composite `(item_id, "
                                 "location_id)`: an existing row is merged, "
                                 "otherwise a new row is appended. There is no "
                                 "surrogate id."),
        auto_request("Get inventory by id (404 by design)", "GET",
                     ["inventories", "1"], 404,
                     description="404 on purpose: inventory rows are keyed on "
                                 "`(item_id, location_id)`, so a single id has "
                                 "no meaning. Use `GET /items/{id}/inventory`."),
        auto_request("Update inventory (404 by design)", "PUT",
                     ["inventories", "1"], 404, body=inv,
                     description="404 by design - same composite-key reason. "
                                 "Re-POST the row to upsert it."),
        auto_request("Delete inventory (404 by design)", "DELETE",
                     ["inventories", "1"], 404,
                     description="404 by design. No route removes an inventory "
                                 "row."),
    ], "Inventory is the one resource without per-id routes: reads go through "
       "the item routes, writes are upserts on POST.")


# --------------------------------------------------------------------------
# auth / error folder
# --------------------------------------------------------------------------

def auth_folder():
    return folder("00 - Auth & errors", [
        request("No API key -> 401", "GET", ["warehouses"], api_key=None,
                description="Every route requires the `API_KEY` header. A "
                            "missing or unknown key is a 401.",
                events=[status_test(401)]),
        request("Unknown API key -> 401", "GET", ["warehouses"],
                api_key="not-a-real-key", events=[status_test(401)]),
        request("Key without write access -> 403", "POST", ["warehouses"],
                api_key="{{api_key_readonly}}",
                body=post_body("warehouse.json"),
                description="`api_key_readonly` is the analytics_dashboard key: "
                            "GET on everything, no writes. Permissions are "
                            "per-resource and per-method in data/user.json.",
                events=[prerequest("pm.collectionVariables.set('new_id', 999999);"),
                        status_test(403)]),
        request("Unknown resource -> 403", "GET", ["there_is_no_such_thing"],
                description="A resource that is not in the user's "
                            "`endpoint_access` map is refused before routing "
                            "happens, so an unknown *resource* answers 403 - "
                            "not the 404 you might expect.",
                events=[status_test(403)]),
        request("Unknown sub-resource -> 404", "GET",
                ["warehouses", "1", "nope"],
                description="Past the access check, an unrecognised sub-path is "
                            "a 404.",
                events=[status_test(404)]),
        request("Non-numeric id -> 500", "GET", ["warehouses", "abc"],
                description="`int(paths[1])` raises and the handler turns every "
                            "exception into a bare 500.",
                events=[status_test(500)]),
    ], "Authentication is a single `API_KEY` header matched against "
       "data/user.json; authorisation is a per-resource, per-method flag on "
       "that user. There is no /api/v2, and a path that does not start with "
       "`/api/v1` gets no HTTP response at all - the handler falls through "
       "without writing a status line, so the client sees an empty reply.")


def scenario_folder():
    return folder("99 - Scenario: commit a transfer", [
        auto_request("1. The transfer before commit", "GET",
                     ["transfers", "{{transfer_write_id}}"], 200,
                     description="Records the transfer lines and status the "
                                 "commit should act on.",
                     events=[status_test(200, [
                         "const t = pm.response.json();",
                         "pm.collectionVariables.set('scenario_item_id', t.items.length ? t.items[0].item_id : 119);",
                         "pm.test('transfer exists', function () {",
                         "    pm.expect(t).to.not.eql(null);",
                         "});",
                     ])]),
        auto_request("2. Inventory totals before commit", "GET",
                     ["items", "{{scenario_item_id}}", "inventory", "totals"], 200,
                     description="Stores `total_available` so step 4 can compare.",
                     events=[status_test(200, [
                         "pm.collectionVariables.set('available_before', pm.response.json().total_available);",
                     ])]),
        auto_request("3. Commit the transfer", "PUT",
                     ["transfers", "{{transfer_write_id}}", "commit"], 200,
                     description="Moves the stock and flips the status to "
                                 "`Processed`."),
        auto_request("4. Inventory totals after commit", "GET",
                     ["items", "{{scenario_item_id}}", "inventory", "totals"], 200,
                     description="A move between two locations neither creates "
                                 "nor destroys stock, so the total available is "
                                 "unchanged.",
                     events=[status_test(200, [
                         "pm.test('total_available is unchanged by an internal move', function () {",
                         "    const before = Number(pm.collectionVariables.get('available_before'));",
                         "    pm.expect(pm.response.json().total_available).to.eql(before);",
                         "});",
                     ])]),
        auto_request("5. Transfer is Processed", "GET",
                     ["transfers", "{{transfer_write_id}}"], 200,
                     description="**This assertion fails against the API as it "
                                 "stands** - see 'Known issues' in the "
                                 "collection description: the commit handler "
                                 "saves a different pool instance than the one "
                                 "it mutated, so the new status is never "
                                 "written to disk.",
                     events=[status_test(200, [
                         "pm.test('status is Processed', function () {",
                         "    pm.expect(pm.response.json().transfer_status).to.eql('Processed');",
                         "});",
                     ])]),
    ], "Run this folder top to bottom with the Collection Runner. It walks the "
       "one route in the API that has real side effects. Step 5 documents a "
       "persistence bug and currently fails on purpose.")


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def collection():
    items = [auth_folder()]
    for spec in RESOURCES:
        items.append(crud_folder(spec))
        if spec["path"] == "locations":
            items.append(transfers_folder())
        if spec["path"] == "suppliers":
            items.append(inventories_folder())
            items.append(orders_folder())
    items.append(shipments_folder())
    items.append(scenario_folder())

    variables = [
        {"key": "base_url", "value": "http://localhost:3000", "type": "string"},
        {"key": "new_id", "value": "999999", "type": "string"},
    ]
    # Ids the read requests point at.
    for key in ["warehouse_id", "location_id", "transfer_id", "item_id",
                "item_line_id", "item_group_id", "item_type_id", "supplier_id",
                "order_id", "client_id", "shipment_id"]:
        variables.append({"key": key, "value": "1", "type": "string"})
    # Ids the PUT / DELETE / commit requests point at. Kept separate from the
    # read ids so repointing a write cannot change what the GETs show.
    for slug in ["warehouse", "location", "transfer", "item", "item_line",
                 "item_group", "item_type", "supplier", "client", "order",
                 "shipment"]:
        variables.append({"key": f"{slug}_write_id", "value": "1",
                          "type": "string"})
    # Filled in by test scripts at run time.
    for slug in ["warehouse", "location", "transfer", "item", "item_line",
                 "item_group", "item_type", "supplier", "client", "order",
                 "shipment"]:
        variables.append({"key": f"created_{slug}_id", "value": "",
                          "type": "string"})
    variables.append({"key": "scenario_item_id", "value": "119", "type": "string"})
    variables.append({"key": "available_before", "value": "", "type": "string"})

    return {
        "info": {
            "name": COLLECTION_NAME,
            "schema": SCHEMA,
            "description": DESCRIPTION,
        },
        "item": items,
        "variable": variables,
    }


DESCRIPTION = """CargoHUB WMS API - the full request library, generated from
the source in `api/` by `postman/generate_postman.py`.

## Running the API

```sh
./start-system.sh        # serves on http://localhost:3000
```

The API is a `http.server` handler in front of the JSON files in `data/`.

## Conventions

- Base path: `{{base_url}}/api/v1`. Nothing else is routed, and a path that does
  not start with `/api/v1` gets no HTTP response at all - the handler returns
  without writing a status line, so the client sees an empty reply.
- Auth: an `API_KEY` header matched against `data/user.json`. Missing or unknown
  key -> 401; a known key without the right flag -> 403. Every request in this
  collection already carries a key that is allowed to make that call, so a 403
  means the flag changed in `data/user.json`.
- Authorisation is checked on the **first path segment only**, before routing.
  So `GET /nonsense` is a 403 rather than a 404, and sub-routes inherit the
  parent resource's flags.
- POST: the `id` goes in the body, `created_at` / `updated_at` are stamped
  server-side, and the reply is a 201 with an empty body.
- PUT: replaces the *entire* record - send every field, or the missing ones are
  dropped. Replies 200.
- DELETE: replies 200 whether or not the id existed.
- `GET /<resource>/<unknown id>` is a 200 with a `null` body, not a 404.
- Nested writes (`PUT /orders/{id}/items`, `PUT /shipments/{id}/items`,
  `PUT /shipments/{id}/orders`) take a **bare JSON array** as the body.
- No pagination, filtering, sorting or query parameters exist anywhere. Listing
  orders or shipments returns the whole table (~5-6k records, each with its
  items inlined).

## Variables

`{{<resource>_id}}` is what the read requests point at; `{{<resource>_write_id}}`
is what PUT / DELETE / commit point at, so repointing a write never changes what
the GETs show. Both default to `1`.

## Which key can do what

| app | scope |
| --- | --- |
| analytics_dashboard | read-only on everything |
| smartglass_reader | read-all, PUT on transfers and inventories |
| order_picker | read-all, PUT on transfers, orders, inventories |
| receiving_station | read-all, POST/PUT on everything except warehouses, locations, clients |
| shipping_station | read-all, POST/PUT on transfers, clients, shipments; PUT on orders, inventories |
| facility_management | full CRUD on warehouses, locations, item_lines, item_groups, item_types, suppliers, clients |

DELETE is granted to `facility_management` only, so `DELETE` on transfers,
items, orders, shipments and inventories is unreachable for every key that
exists - those requests are marked and expect a 403.

## Known issues this collection surfaces

Writes do not persist. Every handler mutates one pool instance and then calls
`data_provider.fetch_*_pool().save()`, which builds a *fresh* instance from disk
and writes that back unchanged - so a POST replies 201, a PUT replies 200, and
nothing reaches `data/`. The one visible effect of a write is that the JSON file
gets rewritten in compact form. Folder `99 - Scenario` walks the transfer commit
route and its last assertion fails for exactly this reason.
"""


def environment():
    values = [
        {"key": "base_url", "value": "http://localhost:3000",
         "type": "default", "enabled": True},
    ]
    for user in load("user.json"):
        values.append({
            "key": f"api_key_{user['app']}",
            "value": user["api_key"],
            "type": "default",
            "enabled": True,
        })
    values.append({"key": "api_key_readonly",
                   "value": "{{api_key_analytics_dashboard}}",
                   "type": "default", "enabled": True})
    return {
        "name": "CargoHUB - local",
        "values": values,
        "_postman_variable_scope": "environment",
    }


def count(items):
    n = 0
    for item in items:
        n += count(item["item"]) if "item" in item else 1
    return n


if __name__ == "__main__":
    col = collection()
    env = environment()
    col_path = os.path.join(OUT, "CargoHUB-WMS-API.postman_collection.json")
    env_path = os.path.join(OUT, "CargoHUB-local.postman_environment.json")
    with open(col_path, "w") as f:
        json.dump(col, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(env_path, "w") as f:
        json.dump(env, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"{col_path}: {count(col['item'])} requests in {len(col['item'])} folders")
    print(f"{env_path}: {len(env['values'])} variables")
