# Multi-stage build for the CargoHUB WMS API. Stages, in order:
#
#   builder  resolves production dependencies from uv.lock into /opt/venv
#   runtime  venv + app code, runs non-root; the image CI publishes to GHCR
#            (docker-deploy.yml builds with --target runtime)
#   dev      runtime + dev group (pytest, httpx) + tests/; the image that
#            docker-compose builds (target: dev), so the documented
#            `docker compose exec api pytest` workflow keeps working
#
# Stage order matters: dev extends runtime and therefore comes last, so a
# plain `docker build .` produces the dev image. Production builds must
# always pass --target runtime.

# ---- builder --------------------------------------------------------------
# Install dependencies into /opt/venv. Only the venv is passed on: uv itself
# and its wheel cache stay in this stage and never reach a final image.
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /code

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Dependencies first, so this layer is cached until pyproject/uv.lock change.
# --no-dev keeps pytest/httpx out of the venv that the runtime image ships.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ---- runtime ---------------------------------------------------------------
# Production image. Two invariants, both required for the copied venv to
# work: the same base image as the builder (the venv symlinks its python
# into the base image), and the same venv path (uv's console scripts point
# at /opt/venv/bin/python absolutely).
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

# ---- dev --------------------------------------------------------------------
# Everything docker-compose needs on top of runtime: the dev group (pytest,
# httpx) and tests/. uv sync only adds the missing dev packages to the venv.
FROM runtime AS dev

# uv runs here as the non-root app user, so point its cache at the
# world-writable /tmp instead of the default $HOME/.cache.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CACHE_DIR=/tmp/uv-cache

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/
COPY --chown=app:app pyproject.toml uv.lock ./
# Copy tests/ to an explicit directory target: as a bare `./` source, a
# directory's contents would be spilled into /code instead.
COPY --chown=app:app tests ./tests

RUN uv sync --frozen --no-install-project
