"""WebSocket connection manager."""
import uuid
import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections grouped by session."""

    def __init__(self):
        self.active_connections: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: uuid.UUID):
        """Accept connection and add to session group."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, websocket: WebSocket, session_id: uuid.UUID):
        """Remove connection from session group."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast(self, session_id: uuid.UUID, message: dict):
        """Send message to all connections in a session."""
        if session_id in self.active_connections:
            # We iterate over a copy of the set because connections might disconnect during broadcast
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # Clean up any failed connections
            for connection in disconnected:
                self.disconnect(connection, session_id)


# Singleton instance
manager = ConnectionManager()
