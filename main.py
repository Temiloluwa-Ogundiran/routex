# from alembic import env
from api.urls import router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from websocket.manager import ConnectionManager
from websocket.broadcast import broadcast
from api.views.socketView import socket_router
from settings import IS_V1
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # You could connect to the database or load other resources here if needed
    # await broadcast.connect()
    yield
    # await broadcast.disconnect()
    # Optional cleanup

# Create the FastAPI app instance



# Define allowed origins (e.g., front-end URL)
origins = [
    "http://localhost:3000",     # for local React/Vue dev server
    'https://x-aggregator.vercel.app/',
    "https://x-aggregator.vercel.app",
    "https://www.xoropay.com",
    "https://www.xoropay.com/"

    # "https://your-frontend.com", # for production frontend
] 
if IS_V1: #Server is in v1
    app = FastAPI(lifespan=lifespan)

    origins = ['*']


else: #dashboard server
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url="/openapi.json", lifespan= lifespan)  # disable default docs
    app.include_router(socket_router)
    origins = [
    "http://localhost:3000",     # for local React/Vue dev server
    'https://x-aggregator.vercel.app/',
    "https://x-aggregator.vercel.app",
    "https://www.xoropay.com",
    "https://www.xoropay.com/",
    "https://dashboard.xoropay.com/",
    "https://dashboard.xoropay.com",
    "https://checkout.xoropay.com",
    "https://checkout.xoropay.com/"

] 
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # or ["*"] to allow all origins (not recommended for prod)
    allow_credentials=True,
    allow_methods=["*"],              # allow all HTTP methods
    allow_headers=["*"],              # allow all headers
)
# Include your routers
app.include_router(router.router)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

