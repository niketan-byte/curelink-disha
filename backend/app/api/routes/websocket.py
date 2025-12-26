"""
WebSocket Routes for Real-time Events
"""
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# Store active connections: {user_id: [websocket1, websocket2]}
active_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat events (typing indicators, etc).
    """
    await websocket.accept()
    
    # Register connection
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(websocket)
    
    logger.info(f"WebSocket connected for user: {user_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle events from client if needed
            event_type = message.get("event")
            
            if event_type == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # Unregister connection
        if user_id in active_connections:
            if websocket in active_connections[user_id]:
                active_connections[user_id].remove(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]


async def broadcast_to_user(user_id: str, event_data: dict):
    """
    Broadcast an event to all active connections of a user.
    """
    if user_id in active_connections:
        disconnected = []
        for ws in active_connections[user_id]:
            try:
                await ws.send_text(json.dumps(event_data))
            except Exception:
                disconnected.append(ws)
        
        # Cleanup disconnected
        for ws in disconnected:
            active_connections[user_id].remove(ws)
        if not active_connections[user_id]:
            del active_connections[user_id]


async def send_typing_indicator(user_id: str, is_typing: bool):
    """
    Utility to send typing indicator event.
    """
    await broadcast_to_user(user_id, {
        "event": "typing_start" if is_typing else "typing_end",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
