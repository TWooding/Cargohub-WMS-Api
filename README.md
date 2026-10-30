# CargoHUB WMS API v2

FastAPI + PostgreSQL, achter nginx, volledig in Docker. De oude API (v1) staat in [`legacy/`](legacy/) en op de `legacy` branch.

## Starten

Vereist: [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env      # optioneel, defaults werken ook
docker compose up -d --build
```

| Wat                | URL                                     |
| ------------------ | --------------------------------------- |
| Swagger UI         | http://localhost:8080/docs              |
| ReDoc              | http://localhost:8080/redoc             |
| API (Postman)      | http://localhost:8080/api/v2/...        |
| Health check       | http://localhost:8080/health            |
| PostgreSQL         | `localhost:5432` (user/pass/db: `cargohub`) |

Beveiligde endpoints vereisen de header `API_KEY` (default `dev-key`, in te stellen via `API_KEYS` in `.env`). In Swagger: klik op **Authorize**.

De `app/` map is in de container gemount met hot reload: wijzigingen zijn direct actief. Na een wijziging in `pyproject.toml` opnieuw bouwen met `docker compose up -d --build api`.

Handige commando's:

```bash
docker compose logs -f api          # logs van de API
docker compose exec api pytest      # tests draaien
docker compose down                 # stoppen
docker compose down -v              # stoppen + database wissen
```

## Containers

```
Postman / browser ──► nginx (:8080) ──► api: FastAPI/uvicorn (:8000) ──► db: PostgreSQL (:5432)
```

## Mappenstructuur

```
app/
├── main.py                 # FastAPI app: middleware + routers koppelen
├── core/
│   └── config.py           # instellingen uit environment variables
├── frontend/               # HTTP-laag: alleen endpoints (controllers)
│   ├── router.py           # verzamelt alle routers, publiek vs. beveiligd
│   └── endpoints/          # één bestand per resource (warehouses.py, ...)
├── middleware/             # alles tussen request en endpoint
│   ├── auth.py             # API key check
│   └── request_timing.py   # request logging + X-Process-Time header
└── backend/                # data-laag
    ├── database.py         # engine + session per request
    ├── models/             # SQLModel tabellen + request/response schema's
    └── services/           # business logic / database queries
tests/                      # pytest, draait op in-memory SQLite
docker/nginx/default.conf   # reverse proxy config
legacy/                     # API v1 (alleen ter referentie)
```

**Een nieuwe resource toevoegen** (bijv. `clients`), met `warehouses` als voorbeeld:

1. Model in `app/backend/models/client.py` en exporteren in `models/__init__.py`
2. Queries in `app/backend/services/client_service.py`
3. Endpoints in `app/frontend/endpoints/clients.py`
4. Router registreren in `app/frontend/router.py`
5. Tests in `tests/test_clients.py`

Tabellen worden bij het opstarten automatisch aangemaakt (`create_all`). Bij schemawijzigingen aan bestaande tabellen: `docker compose down -v` of later overstappen op Alembic migraties.

## Contribution Guidelines

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for our commit messages. This means that each commit message should start with a type (e.g., feat, fix, chore) followed by a short description of the change.

### Package Manager

We use [uv](https://docs.astral.sh/uv/getting-started/installation/). Docker installeert alles zelf; lokaal (voor je IDE) kan dat met:

```bash
uv sync
```
