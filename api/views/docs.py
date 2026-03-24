from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import secrets

# --- Basic Auth ---
security = HTTPBasic()
USERNAME = "admin"
PASSWORD = "eev/=f*K6p.wYCv5f"

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

# --- Docs Router ---
docs_router = APIRouter()

# We will inject the main app dynamically in the routes
def get_app_for_docs():
    from main import app  # import the main app
    return app

@docs_router.get("/docs", dependencies=[Depends(authenticate)])
def custom_swagger_ui():
    app = get_app_for_docs()
    return get_swagger_ui_html(openapi_url=app.openapi_url, title="Protected API Docs")

@docs_router.get("/redoc", dependencies=[Depends(authenticate)])
def custom_redoc_ui():
    app = get_app_for_docs()
    return get_redoc_html(openapi_url=app.openapi_url, title="Protected ReDoc")

@docs_router.get("/openapi.json", dependencies=[Depends(authenticate)])
def protected_openapi():
    app = get_app_for_docs()
    return JSONResponse(get_openapi(title="Protected API", version="1.0.0", routes=app.routes))
