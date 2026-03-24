from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from settings import MAX_WS_LIFETIME


class ConnectionManager:
    def __init__(self):
        # Maps merchant_id -> list of (websocket, expiration_task)
        self.active_connections: Dict[str, List[Dict]] = {}

    async def connect(self, merchant_id: str, websocket: WebSocket):
        await websocket.accept()

        # Schedule a background task to close the connection after MAX_WS_LIFETIME
        expiration_task = asyncio.create_task(self._expire(websocket, merchant_id))

        connection = {"websocket": websocket, "task": expiration_task}
        self.active_connections.setdefault(merchant_id, []).append(connection)

    def disconnect(self, merchant_id: str, websocket: WebSocket):
        connections = self.active_connections.get(merchant_id, [])
        updated_connections = []

        for conn in connections:
            if conn["websocket"] == websocket:
                conn["task"].cancel()  # Cancel the expiration task
            else:
                updated_connections.append(conn)

        if updated_connections:
            self.active_connections[merchant_id] = updated_connections
        else:
            self.active_connections.pop(merchant_id, None)

    async def _expire(self, websocket: WebSocket, merchant_id: str):
        try:
            await asyncio.sleep(MAX_WS_LIFETIME)
            await websocket.close(code=1000, reason="Connection expired")
            self.disconnect(merchant_id, websocket)
        except asyncio.CancelledError:
            # Cancelled when connection closes before expiry
            pass

    async def send(self, merchant_id: str, message: dict):
        connections = self.active_connections.get(merchant_id, [])
        dead_connections = []

        for conn in connections:
            websocket = conn["websocket"]
            try:
                await websocket.send_json(message)
            except Exception:
                # Mark for cleanup if sending fails
                dead_connections.append(websocket)

        for dead_ws in dead_connections:
            self.disconnect(merchant_id, dead_ws)
