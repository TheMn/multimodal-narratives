from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Multimodal Narratives Backend")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/admin")
async def get_admin():
    return FileResponse("static/admin.html")

@app.get("/puzzle")
async def get_puzzle():
    return FileResponse("static/puzzle.html")

@app.get("/room1")
async def get_room1():
    return FileResponse("static/room1.html")

@app.get("/")
async def get_root():
    return {"message": "Welcome to Multimodal Narratives. Endpoints: /admin, /puzzle, /room1"}

class ConnectionManager:
    def __init__(self):
        # Maps room names to a list of active WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room].remove(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]

    async def broadcast_to_room(self, message: str, room: str):
        if room in self.active_connections:
            for connection in self.active_connections[room]:
                await connection.send_text(message)

    async def broadcast_to_all(self, message: str):
        for room, connections in self.active_connections.items():
            for connection in connections:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{room_name}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: str):
    await manager.connect(websocket, room_name)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real app, you might parse the data and route it.
            # For now, we'll just echo it back to the room.
            await manager.broadcast_to_room(f"Client #{client_id} says: {data}", room_name)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
        await manager.broadcast_to_room(f"Client #{client_id} left the chat", room_name)
