#AI generated

from __future__ import annotations
import requests, time, numpy as np
import time
import numpy as np
import pyaudio
import soundfile as sf
from faster_whisper import WhisperModel
import csv
import os

# Import your KB + LLM + NAO helpers from the format file
import format as format  

BASE = "http://127.0.0.1:5006"    
LANG = "English"               # NAO TTS language label

# ====== AUDIO / STT CONFIG ======
DEVICE_INDEX = 6               # USB PnP Audio Device index 
RECORD_SECONDS = 6             # length of each chunk
FRAMES_PER_BUFFER = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1

WHISPER_MODEL_NAME = "small"        # or "base"/"medium"/etc.
WHISPER_DEVICE = "cpu"              # "cuda" if GPU is available
WHISPER_COMPUTE_TYPE = "int8"       # "float16"/"int8_float16" for GPU
LATENCY_CSV = "latency_log.csv"

# ===== Helpers =====
def speak(text,intent):
    if intent=="greeting" :
        wave()
        requests.post(f"{BASE}/talk", json={"message": text, "language": LANG}, timeout=100)

    elif intent=="close":
        bow()
        requests.post(f"{BASE}/talk", json={"message": text, "language": LANG}, timeout=100)

    else:
        requests.post(f"{BASE}/talk", json={"message": text, "language": LANG}, timeout=100) 

def wave():
    # Right-hand wave
    requests.post(f"{BASE}/wave_hand", json={"hand": "right"})

def bow():
    requests.post(f"{BASE}/bow", timeout=100)


def init_latency_csv():
    """
    Create latency_log.csv to record latency if it does not exist.
    """
    if not os.path.exists(LATENCY_CSV):
        with open(LATENCY_CSV, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "chunk_idx",
                "stt_ms",
                "plan_ms",
                "speak_ms",
                "total_ms",
            ])

def record_once(device_index: int) -> tuple[np.ndarray, int]:
    """
    - Function to record audio
    - Uses device's defaultSampleRate (so no invalid-rate errors)
    - Records RECORD_SECONDS
    """
    p = pyaudio.PyAudio()
    dev_info = p.get_device_info_by_index(device_index)

    sample_rate = int(dev_info["defaultSampleRate"])
    max_in = dev_info.get("maxInputChannels", 0)

    print(f"\n[Record] Using device {device_index}: {dev_info.get('name')}")
    print(f"[Record] defaultSampleRate={sample_rate}, maxInputChannels={max_in}")

    if max_in <= 0:
        raise RuntimeError("Selected device has no input channels (not a mic).")

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=FRAMES_PER_BUFFER,
    )

    print(f"[Record] Recording for {RECORD_SECONDS} seconds...")
    frames: list[bytes] = []
    num_frames = int(sample_rate / FRAMES_PER_BUFFER * RECORD_SECONDS)

    for _ in range(num_frames):
        data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
        frames.append(data)

    print("[Record] Done recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    pcm_bytes = b"".join(frames)
    audio_np = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    return audio_np, sample_rate


class WhisperSTT:
    """
    Load Whisper once and reuse it for all chunks.
    """
    def __init__(self, model_name: str, device: str, compute_type: str):
        print(f"[STT] Loading Whisper model: {model_name}")
        self.model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )

    def transcribe(self, audio_np: np.ndarray, sample_rate: int):
        if audio_np.size == 0:
            return ""

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio_np, sample_rate)
            tmp_path = tmp.name

        print(f"[STT] Transcribing chunk ({len(audio_np)/sample_rate:.2f}s)...")
        segments, info = self.model.transcribe(tmp_path, beam_size=5)
        text = "".join(seg.text for seg in segments).strip()
        return text


def main():
    # Instantiate STT once
    stt = WhisperSTT(
        model_name=WHISPER_MODEL_NAME,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
    )
    init_latency_csv()

    print("\n=== Continuous voice → STT → KB/LLM → NAO TTS ===")
    print(f"Recording {RECORD_SECONDS}-second chunks from device index {DEVICE_INDEX}")
    print("For each chunk, the system will:")
    print("  1) Transcribe speech")
    print("  2) Run plan_reply (intent + kb + LLM)")
    print("  3) Send final reply to NAO via format.speak(...)")
    print("Press Ctrl+C to stop.\n")

    chunk_idx = 0

    try:
        while True:
            chunk_idx += 1

            # 1) record a chunk (we do NOT include the fixed record time in timings)
            audio_np, sr = record_once(device_index=DEVICE_INDEX)

            # 2) STT timing
            t0 = time.time()
            text = stt.transcribe(audio_np, sr)
            t1 = time.time()

            print(f"\n===== CHUNK {chunk_idx} (sr={sr}) =====")
            print("User (transcribed):", text or "[no text recognized]")

            if not text.strip():
                print("No speech detected, skipping reply.")
                time.sleep(2)
                continue

            # 3) KB + LLM planning timing
            t2_start = time.time()
            reply, intent = format.plan_reply(text)
            t2_end = time.time()
            print("Bot reply:", reply)

            # 4) NAO TTS / speak timing
            t3_start = time.time()
            speak(reply, intent)
            t3_end = time.time()
            print("=================================\n")

            # --- compute and log latencies ---
            stt_ms   = (t1 - t0) * 1000.0
            plan_ms  = (t2_end - t2_start) * 1000.0
            speak_ms = (t3_end - t3_start) * 1000.0
            total_ms = (t3_end - t0) * 1000.0

            try:
                with open(LATENCY_CSV, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([chunk_idx, f"{stt_ms:.2f}", f"{plan_ms:.2f}",
                                        f"{speak_ms:.2f}", f"{total_ms:.2f}"])
            except Exception as e:
                print(f"[WARN] Failed to write latency CSV: {e}")

            # Small pause 
            time.sleep(3)

    except KeyboardInterrupt:
            print("\n[Main] Stopped by user.")


if __name__ == "__main__":
    main()