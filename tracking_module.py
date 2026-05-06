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
        # If it is spawned, it should track by default
        self.is_tracking = True

        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # Open webcam
        self.cap = cv2.VideoCapture(0)
        self.prev_frame = None

        self.mock_mode = False
        if not self.cap.isOpened():
            print("\n" + "=" * 60)
            print("WARNING: Could not access the webcam (/dev/video0).")
            print(
                "This is common in WSL environments or if another app is using the camera."
            )
            print(
                "Starting in MOCK MODE: Generating random gaze and movement data for testing."
            )
            print("=" * 60 + "\n")
            self.mock_mode = True

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
        import random

        while True:
            if not self.is_tracking:
                await asyncio.sleep(0.5)
                continue

            if self.mock_mode:
                # Generate mock data so the frontend effects can be tested without a real camera
                intensity = random.uniform(0.0, 0.2) if random.random() > 0.8 else 0.0
                if intensity > 0.05:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "movement",
                                "intensity": round(intensity, 3),
                                "bounding_box": {
                                    "x1": 0,
                                    "y1": 0,
                                    "x2": 100,
                                    "y2": 100,
                                },
                            }
                        )
                    )

                # Mock gaze mostly towards the center
                if random.random() > 0.3:
                    mock_x = max(0.0, min(1.0, random.gauss(0.5, 0.2)))
                    mock_y = max(0.0, min(1.0, random.gauss(0.5, 0.2)))
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "gaze",
                                "detected": True,
                                "coordinates": {
                                    "x": round(mock_x, 3),
                                    "y": round(mock_y, 3),
                                },
                            }
                        )
                    )

                await asyncio.sleep(0.2)
                continue

            ret, frame = self.cap.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # --- 1. Movement Tracking ---
            # =====================================================================
            # HOW TO TWEAK MOVEMENT SENSITIVITY:
            # - MOVEMENT_PIXEL_THRESH (default 35): How much a pixel's color must
            #   change to be considered "movement". Increase this if shadows or
            #   slight lighting changes are triggering movement.
            # - MOVEMENT_MIN_AREA (default 2000): The minimum size of a moving
            #   blob to be counted. Increase this to ignore small twitches/noise.
            # - MOVEMENT_INTENSITY_DENOMINATOR (default 100000.0): The value used
            #   to calculate the 0.0 - 1.0 intensity scale. Increase this number
            #   to make the overall intensity *lower* (requires massive movement
            #   to hit 1.0).
            # - MOVEMENT_BROADCAST_THRESH (default 0.15): The threshold intensity
            #   required before a websocket message is actually sent.
            # =====================================================================
            MOVEMENT_PIXEL_THRESH = 35
            MOVEMENT_MIN_AREA = 2000
            MOVEMENT_INTENSITY_DENOMINATOR = 100000.0
            MOVEMENT_BROADCAST_THRESH = 0.15

            intensity = 0.0
            bounding_box = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}

            if self.prev_frame is not None:
                # Calculate difference between current and previous frame
                frame_diff = cv2.absdiff(self.prev_frame, gray)
                thresh = cv2.threshold(
                    frame_diff, MOVEMENT_PIXEL_THRESH, 255, cv2.THRESH_BINARY
                )[1]
                thresh = cv2.dilate(thresh, None, iterations=2)

                # Find contours to calculate intensity and bounding box
                contours, _ = cv2.findContours(
                    thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                total_area = 0
                max_area = 0
                for c in contours:
                    area = cv2.contourArea(c)
                    if area > MOVEMENT_MIN_AREA:  # Filter out small noise
                        total_area += area
                        if area > max_area:
                            max_area = area
                            x, y, w, h = cv2.boundingRect(c)
                            bounding_box = {"x1": x, "y1": y, "x2": x + w, "y2": y + h}

                # Normalize intensity based on a typical large movement
                intensity = min(total_area / MOVEMENT_INTENSITY_DENOMINATOR, 1.0)

            self.prev_frame = gray

            # Broadcast Movement Data
            if intensity > MOVEMENT_BROADCAST_THRESH:
                movement_msg = {
                    "type": "movement",
                    "intensity": round(intensity, 3),
                    "bounding_box": bounding_box,
                }
                await websocket.send(json.dumps(movement_msg))

            # --- 2. Gaze / Face Tracking ---
            # =====================================================================
            # HOW TO TWEAK GAZE SENSITIVITY (Iris vs Head Movement):
            # - HEAD_WEIGHT (default 0.3): How much the overall head position controls
            #   the glitch (0.0 = head position ignored, 1.0 = purely head tracked).
            # - IRIS_WEIGHT (default 0.7): How much the eyeball/iris movement controls
            #   the glitch. A higher weight means moving your eyes while your head
            #   is perfectly still will cause the glitch spot to move rapidly.
            # - MULTIPLIER_X / Y (default 250.0 / 3.0): Because your iris only moves a few
            #   millimeters, we multiply that tiny shift so it spans the entire
            #   computer screen. Increase this to make the glitch spot move further.
            # - OFFSET_X / Y (default 0.0 / -0.2): The camera is usually at the TOP
            #   of the screen, meaning you are technically looking "down" at the
            #   monitor. Decrease OFFSET_Y (make it negative) to artificially lift
            #   the baseline starting point up so it aligns with the center of the screen.
            # =====================================================================
            HEAD_WEIGHT = 0.2
            IRIS_WEIGHT = 0.8
            MULTIPLIER_X = 230
            MULTIPLIER_Y = 5
            OFFSET_X = 0.0
            OFFSET_Y = -0.2

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            gaze_detected = False
            gaze_coords = {"x": 0.5, "y": 0.5}

            if results.multi_face_landmarks:
                gaze_detected = True
                landmarks = results.multi_face_landmarks[0].landmark

                # Head position proxy (Nose Tip: 1)
                head_x = landmarks[1].x
                head_y = landmarks[1].y

                # Iris Tracking (Left Iris Center: 468, Right Iris Center: 473)
                # Eye Corners for reference (Left outer: 33, Right outer: 263)
                l_iris_x = landmarks[468].x
                r_iris_x = landmarks[473].x
                l_eye_corner_x = landmarks[33].x
                r_eye_corner_x = landmarks[263].x

                # Calculate relative Iris shift from center of the eyes
                # If iris is close to the outer corner, they are looking left/right
                eye_center_x = (l_eye_corner_x + r_eye_corner_x) / 2.0
                iris_center_x = (l_iris_x + r_iris_x) / 2.0

                # The raw difference is tiny, so we multiply it
                iris_shift_x = (iris_center_x - eye_center_x) * MULTIPLIER_X

                # Combine head position with the amplified iris shift, plus the physical offsets
                final_x = (
                    (head_x * HEAD_WEIGHT) + (0.5 + iris_shift_x) * IRIS_WEIGHT
                ) + OFFSET_X

                # For Y axis, just amplifying the head movement slightly since vertical
                # eye tracking is less reliable without calibration, and adding the offset.
                final_y = (0.5 + ((head_y - 0.5) * MULTIPLIER_Y)) + OFFSET_Y

                # Clamp values between 0.0 and 1.0 so the spot doesn't leave the screen
                gaze_coords["x"] = round(max(0.0, min(1.0, final_x)), 3)
                gaze_coords["y"] = round(max(0.0, min(1.0, final_y)), 3)

            # Broadcast Gaze Data
            if gaze_detected:
                gaze_msg = {
                    "type": "gaze",
                    "detected": True,
                    "coordinates": gaze_coords,
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
                self._listen_for_commands(websocket), self._process_frames(websocket)
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
