"""Fail closed (sectie 06): elke route moet een permissie declareren of expliciet identiteit-only zijn."""
from fastapi import FastAPI
from fastapi.routing import APIRoute

OPEN_PATH_SUFFIXES = ("/health", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc")


def _calls(dependant):
    for d in dependant.dependencies:
        yield d.call
        yield from _calls(d)


def unguarded_routes(app: FastAPI, identity_prefix: str) -> list[str]:
    """Routes zonder permissie-dependency, behalve /health, docs en `{identity_prefix}/auth/*`."""
    bad = []
    for r in app.routes:
        if not isinstance(r, APIRoute) or r.path.endswith(OPEN_PATH_SUFFIXES):
            continue
        if r.path.startswith(f"{identity_prefix}/auth/"):
            continue
        if not any(getattr(c, "permission", None) for c in _calls(r.dependant)):
            bad.append(f"{sorted(r.methods)} {r.path}")
    return bad
