import numpy as np
from scipy.io.wavfile import write

fs = 44100  # Sample rate
seconds = 1  # Duration

# Generate a 440Hz sine wave for room1_background
t = np.linspace(0, seconds, seconds * fs, False)
note = np.sin(440 * t * 2 * np.pi)
audio = note * (2**15 - 1) / np.max(np.abs(note))
audio = audio.astype(np.int16)
write('static/audio/room1_background.wav', fs, audio)

# Generate a 220Hz sine wave for room2_background
note2 = np.sin(220 * t * 2 * np.pi)
audio2 = note2 * (2**15 - 1) / np.max(np.abs(note2))
audio2 = audio2.astype(np.int16)
write('static/audio/room2_background.wav', fs, audio2)

# Generate a 880Hz sine wave for notification
note3 = np.sin(880 * t * 2 * np.pi)
audio3 = note3 * (2**15 - 1) / np.max(np.abs(note3))
audio3 = audio3.astype(np.int16)
write('static/audio/notification.wav', fs, audio3)

print("Dummy audio files generated.")
