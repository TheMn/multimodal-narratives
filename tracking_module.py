import cv2
import mediapipe as mp
import numpy as np
import websockets
import asyncio
import json

# ==============================================================================
# NOTE FOR FINAL INSTALLATION:
# This proof of concept uses a standard laptop webcam via opencv-python.
# Due to the low light environment in Room 1 and Room 2, the final production
# will require replacing this standard webcam feed with specialized
# Infrared (IR) or Night-vision cameras.
# ==============================================================================

class TrackingModule:
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.is_tracking = False

        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Open webcam
        self.cap = cv2.VideoCapture(0)
        self.prev_frame = None

    async def _listen_for_commands(self, websocket):
        """Listens for commands from the central server, like toggling tracking."""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if "command" in data and data["command"] == "toggle_tracking":
                        if data["state"] == "on":
                            self.is_tracking = True
                            print("Tracking started.")
                        elif data["state"] == "off":
                            self.is_tracking = False
                            print("Tracking stopped.")
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed.")

    async def _process_frames(self, websocket):
        """Continuously processes webcam frames and sends telemetry."""
        while True:
            if not self.is_tracking:
                await asyncio.sleep(0.5)
                continue

            ret, frame = self.cap.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # --- 1. Movement Tracking ---
            intensity = 0.0
            bounding_box = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}

            if self.prev_frame is not None:
                # Calculate difference between current and previous frame
                frame_diff = cv2.absdiff(self.prev_frame, gray)
                thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)

                # Find contours to calculate intensity and bounding box
                contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                total_area = 0
                max_area = 0
                for c in contours:
                    area = cv2.contourArea(c)
                    if area > 500: # filter out small noise
                        total_area += area
                        if area > max_area:
                            max_area = area
                            (x, y, w, h) = cv2.boundingRect(c)
                            bounding_box = {"x1": x, "y1": y, "x2": x + w, "y2": y + h}

                # Normalize intensity based on a typical large movement
                intensity = min(total_area / 50000.0, 1.0)

            self.prev_frame = gray

            # Broadcast Movement Data
            if intensity > 0.05:
                movement_msg = {
                    "type": "movement",
                    "intensity": round(intensity, 3),
                    "bounding_box": bounding_box
                }
                await websocket.send(json.dumps(movement_msg))

            # --- 2. Gaze / Face Tracking ---
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            gaze_detected = False
            gaze_coords = {"x": 0.0, "y": 0.0}

            if results.multi_face_landmarks:
                gaze_detected = True
                # Just using the nose tip (landmark 1) as a proxy for attention focus point
                landmark = results.multi_face_landmarks[0].landmark[1]
                # Use normalized coordinates directly (0.0 to 1.0)
                gaze_coords = {"x": round(landmark.x, 3), "y": round(landmark.y, 3)}

            # Broadcast Gaze Data (only send if someone is looking, or periodically to reset)
            if gaze_detected:
                gaze_msg = {
                    "type": "gaze",
                    "detected": True,
                    "coordinates": gaze_coords
                }
                await websocket.send(json.dumps(gaze_msg))

            # Yield control back to event loop
            await asyncio.sleep(0.1)

    async def run(self):
        print(f"Connecting to {self.websocket_url}...")
        async with websockets.connect(self.websocket_url) as websocket:
            print("Connected! Waiting for toggle_tracking command...")
            # Run the listener and the frame processor concurrently
            await asyncio.gather(
                self._listen_for_commands(websocket),
                self._process_frames(websocket)
            )

if __name__ == "__main__":
    # Connect to the room1 tracking channel
    websocket_url = "ws://localhost:8000/ws/room1/tracker"
    tracker = TrackingModule(websocket_url)
    try:
        asyncio.run(tracker.run())
    except KeyboardInterrupt:
        print("Shutting down tracking module.")
    finally:
        tracker.cap.release()
