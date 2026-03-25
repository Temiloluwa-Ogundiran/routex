from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


PUBLIC_PATH_PREFIXES = (
    "/api/v1/",
    "/api/v2/",
    "/public/openapi.json",
    "/webhook/test-signature",
)

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
        if path == "/public/openapi.json" or any(
            path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES
        ):
            public_routes.append(route)

    return get_openapi(
        title="RouteX Public API",
        version="1.0.0",
        routes=public_routes,
    )
