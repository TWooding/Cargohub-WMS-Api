# Bijlage A — Bronanalyse v1-data en conversielog

Uitgevoerd op de JSON-bestanden in `legacy/data` (commit `e5a00de`): per bestand de aantallen, dubbele id's en alle 20 verwijzingen tussen bestanden. Dit is de nulmeting voor de migratie naar PostgreSQL.

## Records per bestand

| Bestand | Records | Grootte | Dubbele id | Opmerking |
|---|---:|---:|---:|---|
| warehouse.json | 10 | 4 KB | 0 | code uniek |
| location.json | 400 | 81 KB | 0 | 40 per warehouse |
| item.json | 600 | 315 KB | 0 | code uniek |
| inventory.json | 4.800 | 1,2 MB | n.v.t. | geen id; (item, location) uniek |
| supplier.json | 21 | 9 KB | 0 | `phone_number` i.p.v. `contact_phone` |
| item_line.json | 14 | 3 KB | 0 | |
| item_group.json | 3 | 1 KB | 0 | |
| item_type.json | 3 | 1 KB | 0 | |
| client.json | 300 | 122 KB | 0 | |
| order.json | 4.854 | 2,0 MB | 0 | |
| order_item.json | 26.498 | 2,8 MB | 0 | `unit_price` altijd gevuld |
| shipment.json | 6.132 | 2,2 MB | 0 | |
| shipment_item.json | 33.660 | 2,8 MB | 0 | |
| transfer.json | 800 | 179 KB | 0 | |
| transfer_item.json | 2.370 | 197 KB | 0 | |
| user.json | 6 | 9 KB | — | API-keys in plaintext |

## Verwijzingen

| Verwijzing | Naar | Wees | Leeg |
|---|---|---:|---:|
| location.warehouse_id | warehouse | 0 | 0 |
| item.item_line_id / item_group_id / item_type_id | item_line / item_group / item_type | 0 | 0 |
| item.supplier_id | supplier | 0 | 0 |
| inventory.item_id / location_id | item / location | 0 | 0 |
| order.client_id / ship_to_client_id / bill_to_client_id | client | 0 | 0 |
| order.warehouse_id | warehouse | 0 | 0 |
| order_item.order_id / item_id | order / item | 0 | 0 |
| shipment.order_id | order | 0 | 0 |
| shipment_item.shipment_id / item_id | shipment / item | 0 | 0 |
| transfer.from_location_id / to_location_id | location | 0 | 0 |
| transfer_item.transfer_id / item_id | transfer / item | 0 | 0 |

## Bevindingen

- Referentieel is de bron schoon: 0 verweesde verwijzingen, 0 dubbele id's, geen negatieve voorraad en nergens `quantity_allocated > quantity_on_hand`. Foreign keys in PostgreSQL kunnen zonder opschonen aan.
- `inventory` heeft geen eigen id: in v2 een surrogaatsleutel plus een unieke `(item_id, location_id)`-constraint.
- 2.263 orders hebben meer dan één shipment en 985 orders hebben er geen: het v2-model moet een 1:n-relatie order → shipments ondersteunen.
- Statusverdeling: orders Shipped 2.390 / Pending 2.464 · shipments Transit 1.996 / Scheduled 2.066 / Delivered 2.070 · transfers Scheduled 393 / Processed 407.

## Conversielog migratie

_Nog uit te voeren. Plak hier per entity de output van het importscript (gelezen / geïmporteerd / geweigerd + reden) en neem de totalen over in tabel 1.5 van het rapport._
