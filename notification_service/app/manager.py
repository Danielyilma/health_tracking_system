from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Store active connections: username -> list of websockets
        # (A user might have multiple tabs open)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        if username not in self.active_connections:
            self.active_connections[username] = []
        self.active_connections[username].append(websocket)
        print(f" [Manager] User {username} connected. Total active sessions: {len(self.active_connections[username])}")

    def disconnect(self, websocket: WebSocket, username: str):
        if username in self.active_connections:
            if websocket in self.active_connections[username]:
                self.active_connections[username].remove(websocket)
            if not self.active_connections[username]:
                del self.active_connections[username]
        print(f" [Manager] User {username} disconnected.")

    async def send_personal_message(self, message: str, username: str):
        if username in self.active_connections:
            for connection in self.active_connections[username]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f" [Manager] Failed to send to {username}: {e}")

manager = ConnectionManager()
