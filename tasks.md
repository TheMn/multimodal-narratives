# Technical Tasks for Multimodal Narratives (PoC Phase)

This document outlines the technical tasks required to build the Proof of Concept (PoC) for our installation. The backend is powered by **FastAPI** to allow real-time control, monitoring, and synchronization. The codebase will be modular to allow each system (tracking, audio, visual) to be tested independently and reused.

---

## Task 1: Project Setup & Core Server
**Goal:** Create the basic FastAPI skeleton and install necessary dependencies.
- [ ] Create `requirements.txt` with standard, reliable libraries: `fastapi`, `uvicorn`, `websockets`, `opencv-python`, `mediapipe`, `pyaudio`, `scipy` or `pydub`.
- [ ] Create `main.py` to initialize the FastAPI app.
- [ ] Set up a basic WebSocket endpoint in `main.py` that can handle bidirectional communication between the server and any connected clients (admin portal, room interfaces).
- [ ] Set up static file serving and Jinja2 templates (if necessary) to serve the frontend web interfaces.

---

## Task 2: Tracking Module (Room 1 & Beyond)
**Goal:** Implement a simple gaze and movement tracking system using a standard laptop webcam.
- [ ] Create a `tracking_module.py`.
- [ ] Use `opencv-python` to access the laptop webcam.
- [ ] Implement simple **Movement Tracking**: Calculate the difference between consecutive video frames to detect motion intensity. This intensity value should be broadcasted via WebSockets to the server.
- [ ] Implement simple **Gaze/Face Tracking**: Use `mediapipe` (Face Mesh) to detect if a user is looking at the screen (or track the general direction of their gaze). Broadcast "attention" events to the server.
- [ ] *Note:* Ensure the tracking module can be toggled on/off by the admin portal. Leave comments that the final installation will replace this standard webcam logic with IR cameras due to low light.

---

## Task 3: Visual System (Room 1)
**Goal:** Build the frontend projection interface for Room 1 that reacts to the tracking data.
- [ ] Create an HTML/JS page (e.g., `room1.html`).
- [ ] Implement logic to display images of artworks from a local folder.
- [ ] Set up a timer to rapidly switch the images every 4-5 seconds.
- [ ] Connect the page to the central WebSocket server.
- [ ] **Interactivity:** If the server broadcasts a "high movement" event (from Task 2), make the visuals glitch or change faster. If a "gaze detected" event is received, perhaps bring the out-of-focus details into sharp focus temporarily.

---

## Task 4: Audio System (Room 1 & Room 2)
**Goal:** Handle the chaotic audio of Room 1, record voices, apply eerie effects, and play them back in Room 2.
- [ ] Create an `audio_module.py` (using libraries like `pyaudio` and basic waveform manipulation via `scipy` or `numpy`).
- [ ] **Room 1 Audio:** Play a continuous loop of overlapping, chaotic background sounds.
- [ ] **Recording Loop:** Set up a background process that continuously records short snippets of audio from the laptop microphone (capturing visitors' voices).
- [ ] **Audio Processing:** Apply simple effects to the recorded audio chunks (e.g., pitch shifting, reverb, or reversing) to make them sound mysterious. Save these to a temporary local folder.
- [ ] **Room 2 Audio:** Play a dark, eerie soundtrack mixed with the processed voice recordings. Allow the Admin portal to trigger this playback when visitors enter Room 2.

---

## Task 5: Admin Control Portal
**Goal:** A centralized web interface for the host/admin to manage the installation.
- [ ] Create `admin.html`.
- [ ] Connect to the WebSocket server.
- [ ] Display real-time telemetry: showing current movement intensity, gaze status, and audio recording status.
- [ ] Add manual control buttons:
  - "Start Room 1 Visuals"
  - "Trigger Room 2 Audio (The Void)"
  - "Start Room 3 Relaxing Audio"
- [ ] Allow the admin to toggle whether the installation runs on an automated timer or waits for manual triggers.

---

## Task 6: Room 3 Interactive Puzzle (The User Portal)
**Goal:** A cozy, synchronized multiplayer puzzle interface.
- [ ] Create `puzzle.html`.
- [ ] Implement a simple drag-and-drop puzzle game using basic HTML5 Canvas or pure JS/CSS grid. The puzzle pieces will be cut from a high-resolution famous artwork.
- [ ] **Synchronization:** When a user moves a piece, broadcast the move via WebSockets to the server, which broadcasts it to all other connected clients. This ensures all users see the pieces moving in real-time.
- [ ] Add a celebratory animation and display educational text about the artwork once the puzzle is completed.
- [ ] Add background relaxing audio playback to this page (or controlled via the central server).

---

## Architecture Summary for Reusability
By breaking the system into these tasks, we ensure that:
1. `tracking_module.py` runs independently, constantly sending data to `main.py`.
2. `audio_module.py` listens to commands from `main.py` and processes sound in the background.
3. The web interfaces (`room1.html`, `admin.html`, `puzzle.html`) act as dumb clients, simply reacting to WebSocket messages sent from `main.py`. This makes it incredibly easy to swap out the frontend or run them on different devices connected to the same local network.
