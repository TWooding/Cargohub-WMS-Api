# Bijlage C — Testinventaris

Alle testfuncties van v1 (`legacy/tests`) en v2 (`tests`). *Verwacht* is afgeleid uit de code (`xfail(strict=True)` = bekend defect); vervang door de echte uitslag na een run. `×n` = geparametriseerd.

## C.1 v1 (legacy/tests)

### `legacy/tests/test_auth.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_missing_api_key_gives_401` | PASS | — |
| `test_wrong_api_key_gives_401` | PASS | — |
| `test_rights_per_app` ×n | PASS | — |
| `test_nobody_can_delete_items_inventories_transfers_orders_or_shipments` | PASS | — |
| `test_read_only_app_gets_403_on_post` | PASS | — |
| `test_delete_item_gives_403_for_facility_management` | PASS | — |
| `test_rights_only_look_at_first_part_of_path` | PASS | — |
| `test_smartglass_can_commit_any_transfer` | PASS | — |
| `test_removed_key_in_user_file_is_refused_directly` | PASS | — |

### `legacy/tests/test_data.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_amount_of_records` ×n | PASS | — |
| `test_ids_are_unique` ×n | PASS | — |
| `test_every_warehouse_has_40_locations` | PASS | — |
| `test_inventory_has_no_id_but_item_and_location_are_unique` | PASS | — |
| `test_no_negative_inventory` | PASS | — |
| `test_statuses_in_data` | PASS | — |
| `test_orders_shared_by_multiple_shipments` | PASS | — |
| `test_order_has_three_clients` | PASS | — |
| `test_supplier_uses_other_field_names_than_client_and_warehouse` | PASS | — |
| `test_references_between_data_are_valid` | PASS | — |
| `test_users_are_six_apps_with_plain_api_key` | PASS | — |

### `legacy/tests/test_get_endpoints.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_get_list` ×n | PASS | — |
| `test_get_one_returns_record_from_data` ×n | PASS | — |
| `test_get_locations_of_warehouse` | PASS | — |
| `test_get_inventory_of_item` | PASS | — |
| `test_get_inventory_totals_of_item` | PASS | — |
| `test_item_line_items_returns_only_ids` | PASS | — |
| `test_supplier_items_returns_full_items` | PASS | — |
| `test_get_transfer_with_items` | PASS | — |
| `test_get_order_with_items_without_unit_price` | PASS | — |
| `test_get_shipment_with_items` | PASS | — |
| `test_shipment_orders_is_list_with_one_order` | PASS | — |
| `test_client_orders_also_returns_orders_as_receiver_or_payer` | PASS | — |

### `legacy/tests/test_orders_shipments.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_put_order_items_allocates_on_location_with_most_stock` | PASS | — |
| `test_post_order_allocates_same_as_put_order_items` | XFAIL | Orders: POST /orders met items reserveert niks, alleen PUT /orders/{id}/items doet dat |
| `test_cannot_allocate_more_than_on_hand` | XFAIL | Orders: je kunt meer reserveren dan er op voorraad ligt |
| `test_put_shipment_items_changes_ordered_on_location_with_most_stock` | PASS | — |
| `test_put_shipment_orders_only_keeps_first_order` | PASS | — |
| `test_delivered_shipment_cannot_go_back_to_scheduled` | XFAIL | Shipments: status mag vrij gekozen worden, Delivered kan terug naar Scheduled |

### `legacy/tests/test_performance.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_small_lists_are_fast` ×n | PASS | — |
| `test_get_orders_reads_order_items_only_once` | XFAIL | A5/R3: get_orders() leest order_item.json opnieuw in voor elke order (orders.py:13-27) |

### `legacy/tests/test_status_codes.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_get_returns_json` | PASS | — |
| `test_unknown_id_gives_200_with_null` | PASS | — |
| `test_post_gives_201_without_body` | PASS | — |
| `test_put_unknown_id_gives_200` | PASS | — |
| `test_delete_unknown_id_gives_200` | PASS | — |
| `test_unknown_resource_gives_403` ×n | PASS | — |
| `test_unknown_sub_path_gives_404` ×n | PASS | — |
| `test_put_inventory_with_id_gives_404` | PASS | — |
| `test_invalid_id_gives_500` ×n | PASS | — |
| `test_broken_json_gives_500` | PASS | — |
| `test_post_without_id_gives_500` ×n | PASS | — |
| `test_path_outside_api_v1_gives_no_response` ×n | PASS | — |
| `test_patch_gives_html_error_page` | PASS | — |

### `legacy/tests/test_transfers.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_new_transfer_always_gets_status_scheduled` | PASS | — |
| `test_commit_moves_inventory` | PASS | — |
| `test_commit_to_location_without_inventory_creates_row` | PASS | — |
| `test_commit_twice_moves_inventory_once` | XFAIL | R2: dezelfde transfer kan meerdere keren uitgevoerd worden |
| `test_commit_with_too_little_inventory_does_not_go_negative` | XFAIL | R2: geen check op genoeg voorraad, bronlocatie kan negatief worden |
| `test_commit_from_empty_location_does_not_create_inventory` | XFAIL | R2: bronlocatie zonder voorraadregel, toch voorraad op de doellocatie |
| `test_put_transfer_cannot_set_status_processed` | XFAIL | Transfers: PUT laat elke status toe, ook Processed zonder dat voorraad beweegt |

### `legacy/tests/test_write.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_post_warehouse_can_be_found_with_get` | XFAIL | A1/R1: schrijven geeft 200/201 maar wordt niet opgeslagen (main.py:399-400) |
| `test_put_warehouse_changes_name` | XFAIL | A1/R1: schrijven geeft 200/201 maar wordt niet opgeslagen (main.py:399-400) |
| `test_delete_warehouse_removes_it` | XFAIL | A1/R1: schrijven geeft 200/201 maar wordt niet opgeslagen (main.py:399-400) |
| `test_post_inventory_can_be_found_with_get` | XFAIL | A1/R1: schrijven geeft 200/201 maar wordt niet opgeslagen (main.py:399-400) |
| `test_commit_transfer_changes_status` | XFAIL | A1/R1: schrijven geeft 200/201 maar wordt niet opgeslagen (main.py:399-400) |
| `test_post_warehouse_is_written_to_data_file` | XFAIL | A1/R1: schrijven geeft 200/201 maar wordt niet opgeslagen (main.py:399-400) |
| `test_delete_with_linked_records_is_not_blocked` ×n | PASS | — |
| `test_put_replaces_whole_record` | PASS | — |
| `test_put_accepts_other_id_in_body_than_in_path` | PASS | — |
| `test_post_accepts_duplicate_id_and_get_returns_first` | PASS | — |

## C.2 v2 (tests)

### `tests/test_endpoint_skeletons.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_skeletons_are_registered` | PASS | — |
| `test_skeleton_returns_501` ×n | PASS | — |
| `test_skeleton_requires_api_key` ×n | PASS | — |
| `test_skeletons_are_documented` | PASS | — |

### `tests/test_health.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_health` | PASS | — |
| `test_health_db` | PASS | — |

### `tests/test_warehouses.py`

| Test | Verwacht | Reden xfail |
|---|---|---|
| `test_requires_api_key` | PASS | — |
| `test_crud` | PASS | — |
| `test_create_validation` | PASS | — |

## Uitvoeren

```bash
# v1: vanuit legacy/api
pytest ../tests -rxX
# v2: in de container (eenmalig: uv add --dev pytest-cov)
docker compose exec api pytest --cov=app --cov-report=term-missing
```

## Ruwe output

_Plak hier de pytest- en coverage-output._
