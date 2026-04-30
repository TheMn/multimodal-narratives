# Multimodal Narratives: Mindful Art Consumption

Welcome to the technical and conceptual repository for our interactive art installation. This project aims to merge art, technology, and shared experiences to encourage mindful consumption of artistic products.

## Introduction

We live in an era of hyper-connectivity and endless scrolling. Our average attention span for an image on social media has plummeted to roughly 4-5 seconds. This constant barrage of visual stimuli often leads to sensory overload and, ironically, a profound sense of isolation and loneliness.

Our installation is an interactive experience designed to raise public awareness regarding mindful art consumption. By manipulating the sensory environment across three distinct spaces, we aim to guide participants from a state of chaotic overstimulation to a state of collaborative, focused reconciliation with art. Our ultimate goal is to make art not just a passive visual experience, but an interactive journey that makes people slow down and become active participants.

## The Installation

### Technical Aspects
- **Capacity:** Small groups of visitors (approx. 4-6 people per group) traversing the rooms together.
- **Format:** The installation can be built as a pop-up/mobile experience or adapted for a permanent exhibition space.
- **Host/Self-Guided:** The experience is entirely self-guided, relying on the environment and technological cues to move the audience forward.
- **Timing:** 10-15 minutes total, divided equally among the three rooms.

### The Tech Stack
- **Backend/Orchestration:** Python with **FastAPI**. It handles real-time data, web sockets for synchronized user experiences, and routing for audio/visual components.
- **Tracking & Inputs:** Simple Webcams with **OpenCV** and **MediaPipe** for movement and gaze tracking. (Note: For the final production in low-light environments, specialized Infrared/Night-vision cameras will be required).
- **Audio/Visual Processing:** Real-time audio recording, processing (applying mysterious effects), and playback. Dynamic image projections timed and manipulated via the central server.
- **Frontend Interfaces:** Web technologies (HTML/JS/CSS) served by FastAPI for the interactive touch screen puzzle and the admin control portal.

## The Three Rooms

### Room 1: Overstimulation (The Chaos)
A space designed to mimic the overwhelming nature of our digital lives.
- **Atmosphere:** Chaotic, high sensory overload (both audio and visual).
- **Visuals:** Projections of famous artworks appear and disappear rapidly on various surfaces at 4/5 second intervals. Some artworks will have missing details (e.g., out-of-focus faces) to represent the fleeting nature of our attention.
- **Audio:** Chaotic, overlapping sounds.
- **Tech Integration:** We will use gaze detection and movement tracking. Furthermore, microphones will subtly record snippets of the visitors' voices/reactions to be processed for the next room.

### Room 2: Isolation (The Void)
A harsh contrast to the first room, designed to evoke loneliness, unease, and a sense of being lost.
- **Atmosphere:** Pitch black. It is impossible to see or interact visually with the people around you, creating a sense of suspension from reality and disorientation.
- **Audio:** A mysterious, eerie soundtrack mixed dynamically with the edited, warped voice recordings captured from the visitors in Room 1.

### Room 3: Reconciliation (The Connection)
A cozy, relaxed space where participants reunite, slow down, and actively engage with art.
- **Atmosphere:** Welcoming, with relaxing music and sounds.
- **Interaction:** A collaborative touch-screen table where participants work together to assemble digital puzzles of famous artworks.
- **Goal:** This playful activity encourages people to focus on the work, noticing its intricate details and dedicating the time to it that true art deserves. Visitors will also have access to explanations and the history of the operas/artworks.

## The Artworks
*(Placeholder - Non-technical team members: Please insert the names of the artworks we have chosen, their meaning, and why they were selected for the specific rooms).*

## Case Studies
**A Walkthrough Experience:**
1. A group of four friends enters Room 1. They are bombarded with fleeting images of Renaissance paintings and modern art. Their eyes dart around the room as they try to focus, while sensors track their chaotic movements and hidden microphones capture their bewildered chatter.
2. The doors open to Room 2. They step into utter darkness. The sensory overload vanishes, replaced by a haunting soundtrack infused with their own, distorted voices from just moments ago. They experience a profound sense of isolation despite being in the same room.
3. They are guided into Room 3 by soft lighting. The eerie sounds are replaced by calming tones. They gather around a central glowing table and must work together to reassemble one of the fragmented paintings they briefly saw in Room 1. Through collaboration, they slow down and truly see the art.

## Budget & Costs
*(Placeholder - Non-technical team members: Please provide an estimation of the budget. It doesn't need to be extremely detailed, but we should indicate if this requires a high or low budget based on the physical materials, room construction, and projector rentals).*

## Final Thoughts
**Weak Points, Doubts, and Concerns:**
- **Tracking in the Dark:** Our primary technical hurdle is reliable tracking in Room 1 and Room 2 due to low lighting. The PoC will use standard webcams in a lit room, but the real installation requires IR technology.
- **Audio Feedback Loops:** Dynamically recording, editing, and playing back audio between Room 1 and Room 2 must be carefully managed to avoid microphone feedback loops and ensure the editing effect sounds eerie rather than just noisy.

## Conclusion
"Multimodal Narratives" is more than an art exhibit; it is an intervention. By taking visitors on a journey from digital exhaustion to mindful connection, we hope to redefine how we consume art—proving that by slowing down, we can truly see again.

---

## 🚀 Setup & Running Guide (For Developers)

We aim to keep the project as simple as possible. You don't need databases or heavy frameworks, just Python and a few libraries.

### Prerequisites
- Python 3.9+ installed on your laptop.
- A built-in or external webcam and microphone.

### Step-by-Step Guide
1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd multimodal-narratives
   ```
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Server:**
   ```bash
   uvicorn main:app --reload
   ```
5. **Access the Portals:**
   - **Admin Portal:** Open your browser and navigate to `http://localhost:8000/admin`
   - **Interactive Puzzle (Room 3):** Navigate to `http://localhost:8000/puzzle`

*(Note: The `requirements.txt` and `main.py` files are to be created based on the tasks outlined in `tasks.md`.)*
