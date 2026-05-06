import asyncio
import websockets
import json
import pyaudio
import wave
import time
import os
import threading
import numpy as np
from pydub import AudioSegment
from pydub.effects import speedup

class AudioModule:
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.is_recording = False

        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.RECORD_SECONDS = 5
        self.TOTAL_DURATION_LIMIT = 60 # Stop recording after 1 minute per session
        self.p = pyaudio.PyAudio()

        self.processed_dir = "static/audio/processed"
        os.makedirs(self.processed_dir, exist_ok=True)

        # Keep track of when the experience started to limit recording to 1 min
        self.session_start_time = None
        self.recording_thread = None

    def _apply_effects_and_save(self, frames, filename):
        """Applies eerie effects and saves the file."""
        # Save raw temporarily
        temp_filename = "temp_" + filename
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        try:
            # Load with pydub
            sound = AudioSegment.from_wav(temp_filename)

            # 1. Reverse the audio
            sound = sound.reverse()

            # 2. Lower the pitch (simulate by slowing down sample rate, then exporting normally)
            # This makes it sound deeper and slower
            new_sample_rate = int(sound.frame_rate * 0.7)
            sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
                "frame_rate": new_sample_rate
            })
            sound = sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

            # Export
            filepath = os.path.join(self.processed_dir, filename)
            sound.export(filepath, format="wav")
            print(f"Saved processed audio to {filepath}")

        except Exception as e:
            print(f"Error processing audio: {e}")

        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def _record_loop(self):
        """Continuously records 5 second snippets while is_recording is True."""
        print("Audio recording loop started.")
        self.session_start_time = time.time()
        chunk_index = 0

        # Clear previous processed files on new session start
        for f in os.listdir(self.processed_dir):
            if f.endswith(".wav"):
                os.remove(os.path.join(self.processed_dir, f))

        try:
            stream = self.p.open(format=self.FORMAT,
                                channels=self.CHANNELS,
                                rate=self.RATE,
                                input=True,
                                frames_per_buffer=self.CHUNK)
        except OSError as e:
            print(f"Error opening audio stream: {e}")
            self.is_recording = False
            return

        try:
            while self.is_recording:
                elapsed_session_time = time.time() - self.session_start_time
                if elapsed_session_time > self.TOTAL_DURATION_LIMIT:
                    print(f"Reached {self.TOTAL_DURATION_LIMIT}s limit. Stopping recording.")
                    self.is_recording = False
                    break

                print(f"Recording chunk {chunk_index}...")
                frames = []
                for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                    if not self.is_recording:
                        break
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)

                if frames:
                    # Process and save in a separate thread so we don't drop frames for the next chunk
                    filename = f"processed_{chunk_index}.wav"
                    threading.Thread(target=self._apply_effects_and_save, args=(frames, filename)).start()
                    chunk_index += 1

        finally:
            stream.stop_stream()
            stream.close()
            print("Audio recording loop ended.")

    async def _listen_for_commands(self, websocket):
        """Listens for commands from the central server, like toggling tracking/audio."""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if "command" in data and data["command"] == "toggle_tracking":
                        if data["state"] == "on":
                            if not self.is_recording:
                                self.is_recording = True
                                self.recording_thread = threading.Thread(target=self._record_loop)
                                self.recording_thread.start()
                        elif data["state"] == "off":
                            self.is_recording = False
                            if self.recording_thread:
                                self.recording_thread.join(timeout=2.0)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed.")

    async def run(self):
        print(f"AudioModule connecting to {self.websocket_url}...")
        async with websockets.connect(self.websocket_url) as websocket:
            print("AudioModule connected! Waiting for toggle_tracking command...")
            await self._listen_for_commands(websocket)

    def cleanup(self):
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        self.p.terminate()

if __name__ == "__main__":
    websocket_url = "ws://localhost:8000/ws/room1/audio_tracker"
    module = AudioModule(websocket_url)
    try:
        asyncio.run(module.run())
    except KeyboardInterrupt:
        print("Shutting down audio module.")
    finally:
        module.cleanup()
