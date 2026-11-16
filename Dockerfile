# ---- Stage 1: builder — resolve dependencies into /opt/venv. ----
# Only the venv is passed to later stages; uv itself and its wheel cache
# never reach the final image.
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /code

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Dependencies first, so this layer is cached until pyproject/uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ---- Stage 2: runtime — production image; CI publishes this target. ----
# Invariants: same base image as the builder and the same venv path, because
# the console scripts in /opt/venv/bin point at /opt/venv/bin/python absolutely.
FROM python:3.11-slim AS runtime

# uid 1000 matches the usual host user id, keeping bind mounts writable.
RUN useradd --create-home --uid 1000 app && mkdir /code && chown app:app /code
WORKDIR /code

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --chown=app:app app ./app

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]

# ---- Stage 3: dev — runtime plus dev deps; this is what compose builds. ----
# Adds the dev group (pytest, httpx) and tests/ so the documented
# `docker compose exec api pytest` workflow keeps working.
FROM runtime AS dev

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CACHE_DIR=/tmp/uv-cache

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/
COPY --chown=app:app pyproject.toml uv.lock ./
COPY --chown=app:app tests ./tests

RUN uv sync --frozen --no-install-project
