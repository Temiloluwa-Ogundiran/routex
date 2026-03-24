from broadcaster import Broadcast
from settings import REDIS_URL
import asyncio
from websocket.manager import ConnectionManager
import json

manager = ConnectionManager()
broadcast = Broadcast(REDIS_URL)  # update if on another host


# async def start_broadcast_listener(merchant_id: str):

#     async def receive_messages():
#         async with broadcast.subscribe(channel= merchant_id) as subscriber:
#             async for event in subscriber:
#                 try:
#                     data = json.loads(event.message)
#                     await manager.send(merchant_id, data)
#                 except Exception as e:
#                     print(f"Broadcast error: {e}")

#     asyncio.create_task(receive_messages())