import sounddevice as sd
import numpy as np
import whisper
import queue

# Load the Whisper model
model = whisper.load_model("base")

RATE = 16000         # Sample rate required by Whisper
CHANNELS = 1         # Mono audio
SECONDS_PER_CHUNK = 2  # Process every 2 seconds of audio

audio_q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_q.put(indata.copy())
    
# Open an input stream with sounddevice
with sd.InputStream(samplerate=RATE, channels=CHANNELS, callback=audio_callback):
    print("Listening... (Press Ctrl+C to stop)")
    audio_buffer = np.empty((0, CHANNELS), dtype=np.float32)
    try:
        while True:
            # Retrieve audio chunks from the queue
            data = audio_q.get()
            audio_buffer = np.concatenate((audio_buffer, data), axis=0)
            if len(audio_buffer) >= RATE * SECONDS_PER_CHUNK:
                # Extract a chunk of audio for transcription
                chunk = audio_buffer[:RATE * SECONDS_PER_CHUNK]
                audio_buffer = audio_buffer[RATE * SECONDS_PER_CHUNK:]
                # Flatten to 1-D array if mono
                audio_chunk = chunk.flatten()
                # Transcribe the audio chunk
                result = model.transcribe(audio_chunk)
                print("Transcript:", result["text"].strip())
    except KeyboardInterrupt:
        print("Stopping...")
