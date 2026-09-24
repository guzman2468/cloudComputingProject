"""In-process WebSocket connections for live chat events."""

from collections import defaultdict

from fastapi import WebSocket


class ChatConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, email: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[email].add(websocket)

    def disconnect(self, email: str, websocket: WebSocket) -> None:
        self.connections[email].discard(websocket)
        if not self.connections[email]:
            del self.connections[email]

    async def broadcast(self, emails: list[str], event: dict) -> None:
        disconnected: list[tuple[str, WebSocket]] = []
        for email in set(emails):
            for websocket in self.connections.get(email, set()):
                try:
                    await websocket.send_json(event)
                except Exception:
                    disconnected.append((email, websocket))

        for email, websocket in disconnected:
            self.disconnect(email, websocket)


chat_connection_manager = ChatConnectionManager()
