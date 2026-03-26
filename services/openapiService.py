from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


PUBLIC_EXACT_PATHS = {
    "/api/v1/initiate",
    "/api/v1/transactions/verify",
    "/api/v1/payout",
}

PRIVATE_PATH_PREFIXES = (
    "/admin/",
    "/analytics/",
    "/wallet",
    "/merchant",
    "/users",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def build_public_openapi(app: FastAPI) -> dict:
    public_routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if any(path.startswith(prefix) for prefix in PRIVATE_PATH_PREFIXES):
            continue
        if path in PUBLIC_EXACT_PATHS:
            public_routes.append(route)

    return get_openapi(
        title="RouteX Public API",
        version="1.0.0",
        routes=public_routes,
    )
