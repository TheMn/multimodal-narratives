from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import subprocess
import sys

app = FastAPI(title="Multimodal Narratives Backend")

# Global reference to the tracking subprocess
tracking_process = None

def start_tracking():
    global tracking_process
    if tracking_process is None or tracking_process.poll() is not None:
        print("Starting tracking_module.py...")
        tracking_process = subprocess.Popen([sys.executable, "tracking_module.py"])

def stop_tracking():
    global tracking_process
    if tracking_process is not None and tracking_process.poll() is None:
        print("Stopping tracking_module.py...")
        tracking_process.terminate()
        tracking_process = None

# Ensure static directory exists
os.makedirs("static", exist_ok=True)
os.makedirs("static/artworks", exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/artworks")
async def get_artworks():
    try:
        files = os.listdir("static/artworks")
        # Filter for basic image types
        images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        return {"artworks": images}
    except Exception as e:
        return {"artworks": []}

@app.get("/admin")
async def get_admin():
    return FileResponse("static/admin.html")

@app.get("/room1")
async def get_room1():
    return FileResponse("static/room1.html")

@app.get("/room2")
async def get_room2():
    return FileResponse("static/room2.html")

@app.get("/room3")
async def get_room3():
    return FileResponse("static/room3.html")

@app.get("/")
async def get_root():
    return {"message": "Welcome to Multimodal Narratives. Endpoints: /admin, /room1, /room2, /room3"}

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
            # Try to parse as JSON for specific routing, otherwise echo
            import json
            try:
                json_data = json.loads(data)

                if room_name == "room1":
                    # Check for start/stop commands
                    if "command" in json_data and json_data["command"] == "toggle_tracking":
                        if json_data["state"] == "on":
                            start_tracking()
                        elif json_data["state"] == "off":
                            stop_tracking()

                    # If telemetry data from tracking module, also send to admin
                    if "type" in json_data and json_data["type"] in ["movement", "gaze"]:
                        await manager.broadcast_to_room(data, "admin")

                # Broadcast the JSON data to the room
                await manager.broadcast_to_room(data, room_name)
            except json.JSONDecodeError:
                # Fallback for simple text messages
                await manager.broadcast_to_room(f"Client #{client_id} says: {data}", room_name)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
        await manager.broadcast_to_room(f"Client #{client_id} left the chat", room_name)
