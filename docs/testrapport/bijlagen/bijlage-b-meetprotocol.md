# Bijlage B — Meetprotocol responsiviteit en concurrency

Beide API's draaien op dezelfde machine met dezelfde dataset. Per endpoint 1 warm-up request, daarna 20 metingen; rapporteer mediaan en p95. v1 draait op `:3000` (`legacy/start-system.sh`), v2 via nginx op `:8080`.

```bash
# responsiviteit v1 (key van analytics_dashboard uit legacy/data/user.json)
for i in $(seq 20); do curl -s -o /dev/null -w '%{time_total}\n' \
  -H "API_KEY: $V1_KEY" http://localhost:3000/api/v1/orders; done

# responsiviteit v2 (server-side tijd staat in de X-Process-Time-header)
for i in $(seq 20); do curl -s -o /dev/null -w '%{time_total}\n' \
  -H 'API_KEY: dev-key' http://localhost:8080/api/v2/orders; done

# concurrency: 1000 requests, 50 tegelijk
hey -n 1000 -c 50 -H 'API_KEY: dev-key' http://localhost:8080/api/v2/warehouses
```

## Resultaten

| Endpoint | v1 mediaan | v1 p95 | v2 mediaan | v2 p95 | Fouten |
|---|---:|---:|---:|---:|---:|
| /warehouses | … | … | … | … | … |
| /items | … | … | … | … | … |
| /orders | … | … | … | … | … |
| /shipments | … | … | … | … | … |

## Ruwe output

_Plak hier de output van de commando's._
