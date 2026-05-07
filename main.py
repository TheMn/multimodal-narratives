from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import subprocess
import sys

app = FastAPI(title="Multimodal Narratives Backend")

import random

# Global references to the subprocesses
tracking_process = None
audio_process = None
is_tracking_active = False

def get_random_puzzle():
    try:
        desc_files = os.listdir("static/descriptions")
        txt_files = [f for f in desc_files if f.endswith('.txt')]
        if not txt_files:
            return None

        selected_txt = random.choice(txt_files)
        base_name = os.path.splitext(selected_txt)[0]

        artworks = os.listdir("static/artworks")
        matching_artwork = next((f for f in artworks if os.path.splitext(f)[0] == base_name), None)

        if not matching_artwork:
            return None

        with open(os.path.join("static/descriptions", selected_txt), "r", encoding="utf-8") as f:
            description = f.read()

        return {
            "type": "puzzle_init",
            "artwork": f"/static/artworks/{matching_artwork}",
            "description": description,
            "columns": 5,
            "rows": 2
        }
    except Exception as e:
        print(f"Error getting random puzzle: {e}")
        return None

def start_tracking():
    global tracking_process, audio_process, is_tracking_active
    is_tracking_active = True
    if tracking_process is None or tracking_process.poll() is not None:
        print("Starting tracking_module.py...")
        tracking_process = subprocess.Popen([sys.executable, "tracking_module.py"])
    if audio_process is None or audio_process.poll() is not None:
        print("Starting audio_module.py...")
        audio_process = subprocess.Popen([sys.executable, "audio_module.py"])

def stop_tracking():
    global tracking_process, audio_process, is_tracking_active
    is_tracking_active = False
    if tracking_process is not None and tracking_process.poll() is None:
        print("Stopping tracking_module.py...")
        tracking_process.terminate()
        tracking_process = None
    if audio_process is not None and audio_process.poll() is None:
        print("Stopping audio_module.py...")
        audio_process.terminate()
        audio_process = None

# Ensure static directory exists
os.makedirs("static", exist_ok=True)
os.makedirs("static/artworks", exist_ok=True)
os.makedirs("static/audio/processed", exist_ok=True)

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

@app.get("/api/processed_audio")
async def get_processed_audio():
    try:
        files = os.listdir("static/audio/processed")
        audio_files = [f for f in files if f.lower().endswith('.wav')]
        # Sort by creation time so they play in order
        audio_files.sort(key=lambda x: os.path.getmtime(os.path.join("static/audio/processed", x)))
        return {"audio_files": audio_files}
    except Exception as e:
        return {"audio_files": []}

@app.get("/api/notifications")
async def get_notifications():
    try:
        files = os.listdir("static/audio/notifications")
        audio_files = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.ogg'))]
        return {"notifications": audio_files}
    except Exception as e:
        return {"notifications": []}

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

    import json
    if room_name == "room1" and client_id in ["tracker", "audio_tracker"] and is_tracking_active:
        await websocket.send_text(json.dumps({"command": "toggle_tracking", "state": "on"}))

    if room_name == "room3":
        puzzle_data = get_random_puzzle()
        if puzzle_data:
            await websocket.send_text(json.dumps(puzzle_data))

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
