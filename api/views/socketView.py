from fastapi import WebSocket, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services import merchantService, userService
from database.session import get_async_session
from websocket.manager import ConnectionManager
from websocket.broadcast import broadcast
from fastapi.websockets import WebSocketDisconnect
import json
import asyncio

socket_router = APIRouter()
manager = ConnectionManager()


@socket_router.websocket("/ws/{merchant_id}")
async def socket_endpoint(
    merchant_id: str,
    websocket: WebSocket,
    session: AsyncSession = Depends(get_async_session),
):
    print(f"WebSocket opened for merchant: {merchant_id}")
    
    user = await userService.get_current_user_ws(websocket, session)
    if not user:
        await websocket.close(code=1008, reason="User not authenticated")
        return

    merchant = await merchantService.get_by_id_or_email(id=merchant_id, session=session)
    if not merchant:
        await websocket.close(code=1008, reason="Merchant not found")
        return

    if not await userService.user_in_merchant(user=user, merchant=merchant, session=session):
        await websocket.close(code=1008, reason="Access denied for merchant socket")
        return

    await manager.connect(merchant_id, websocket)

    channel = f"merchant_{merchant_id}"

    async def listen_to_broadcast():
        async with broadcast.subscribe(channel) as subscriber:
            async for event in subscriber:
                try:
                    data = json.loads(event.message)
                    await websocket.send_json(data)
                except Exception as e:
                    print(f"Error sending message: {e}")

    # Start listening to broadcast in background
    listen_task = asyncio.create_task(listen_to_broadcast())

    try:
        while True:
            await websocket.receive_text()  # Just to keep the connection alive

    except WebSocketDisconnect:
        print("Client disconnected")
        manager.disconnect(merchant_id, websocket)
        listen_task.cancel()

    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(merchant_id, websocket)
        listen_task.cancel()
