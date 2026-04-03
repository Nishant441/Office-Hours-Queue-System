"""WebSocket routes for real-time updates."""
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time session updates.
    
    Connected clients will receive messages when tickets are:
    - Created
    - Claimed
    - Started
    - Resolved
    - Cancelled
    """
    try:
        session_uuid = uuid.UUID(session_id)
        await manager.connect(websocket, session_uuid)
        
        while True:
            # We don't expect messages from students, but keep connection open
            await websocket.receive_text()
            
    except (ValueError, WebSocketDisconnect):
        pass
    finally:
        try:
            session_uuid = uuid.UUID(session_id)
            manager.disconnect(websocket, session_uuid)
        except Exception:
            pass
