# Reception Robot System

A voice-activated receptionist robot system that uses speech-to-text, knowledge base lookup, and LLM integration to interact with users via a NAO robot.

## How to Install Dependencies

### Prerequisites

- **Python 2.7** (required for `body.py` - NAO robot communication) 
- **Python 3.x** (required for `sidecar.py` and other scripts)
- **NAO Robot SDK** (naoqi library for Python 2)

### Python 2 Dependencies (for `body.py`)

The `body.py` script requires:
- `flask` - Web framework for API endpoints
- `naoqi` - NAO robot SDK (Python 2)
- `qi` - NAO robot session management (Python 2)

Install NAO SDK:
```bash
# Download and install NAOqi SDK for Python 2.7 from SoftBank Robotics
# Follow the official NAOqi installation guide for your platform
```

Install Flask for Python 2:
```bash
pip2 install flask
```

### Python 3 Dependencies (for `sidecar.py` and other scripts)

Install required packages:
```bash
pip3 install requests numpy pyaudio soundfile faster-whisper google-genai scikit-learn seaborn matplotlib
```

Or create a `requirements.txt` and install:
```bash
pip3 install -r requirements.txt
```

**Note:** You may need to install system-level audio libraries:
- On macOS: `brew install portaudio`
- On Linux: `sudo apt-get install portaudio19-dev python3-pyaudio`
- On Windows: Install PyAudio wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

### Configuration

1. **Google GenAI API Key**:
This project uses **Google GenAI (Gemini)** for LLM responses.  
You must provide **your own API key** via the `GEMINI_API_KEY` environment variable.

### Linux / macOS (bash/zsh)

```bash
export GEMINI_API_KEY="YOUR_KEY_HERE"
```

2. **NAO Robot Connection**: IF REQUIRED Update the NAO robot IP address and port in `src/body.py`:
   ```python
   nao_IP = "192.168.34.110"  # Change to your NAO robot's IP
   nao_port = 9559
   ```

3. **Audio Device**: IF REQUIRED Update the audio device index in `src/sidecar.py`:
   ```python
   DEVICE_INDEX = 6  # Change to your USB microphone device index
   ```

## How to Run the Code

### Using `run.py`

The main entry point is `run.py`, which runs both `body.py` (Python 2) and `sidecar.py` (Python 3) in parallel:

```bash
python3 run.py
```

This will:
1. Start the Flask server (`body.py`) on port 5006 for NAO robot communication
2. Start the voice processing pipeline (`sidecar.py`) that records audio, transcribes speech, and generates responses

Press `Ctrl+C` to gracefully stop both processes.
Might have to use `pkill -9 python`to kill all python processes if tts continues to transcribe chunks

**Note:** `run.sh` does not exist. Use `run.py` as described above.

## Expected Inputs/Outputs

### Inputs

1. **Audio Input**: 
   - USB microphone connected to the system
   - Audio is recorded in 6-second chunks
   - Device index must be configured in `src/sidecar.py`

2. **User Queries** (via voice):
   - Greetings: "hello", "hi", "hey"
   - Directory queries: "where is [room/lab]?", "locate [location]"
   - Contact queries: "who is [faculty]?", "contact [name]"
   - Hours queries: "when is [facility] open?"
   - General questions (handled by LLM)

### Outputs

1. **Robot Responses**:
   - Text-to-speech output via NAO robot
   - Gestures (waving for greetings, bowing for closings)
   - Visual feedback through robot movements

2. **Logs and Metrics**:
   - `src/latency_log.csv` - Records latency metrics for each interaction:
     - `chunk_idx`: Chunk number
     - `stt_ms`: Speech-to-text processing time
     - `plan_ms`: Knowledge base lookup + LLM planning time
     - `speak_ms`: NAO TTS execution time
     - `total_ms`: Total end-to-end latency

3. **Generated Files** (in `assets/` directory):
   - `output.txt` - Text output logs
   - `run_log.txt` - Runtime logs
   - `log_run_1.jpg`, `log_run_2.jpg` - Log visualization plots
   - `query_classi_plot.jpg` - Intent classification visualization

4. **Console Output**:
   - Transcribed user speech
   - Bot reply text
   - Timing information for each chunk

## Folder Structure

```
reception/
├── README.md                 # This file
├── run.py                    # Main entry point - runs body.py and sidecar.py in parallel
├── assets/                   # Output files, logs, and visualizations
│   ├── log_run_1.jpg
│   ├── log_run_2.jpg
│   ├── output.txt
│   ├── query_classi_plot.jpg
│   └── run_log.txt
├── docs/                     # Documentation directory (currently empty)
└── src/                      # Source code directory
    ├── body.py              # Flask server for NAO robot communication (Python 2)
    ├── sidecar.py           # Voice processing pipeline (Python 3)
    ├── format.py            # Knowledge base lookup and LLM integration
    ├── kb.json              # Knowledge base data (rooms, labs, contacts, hours)
    ├── latency_log.csv      # Latency metrics log
    ├── avg_latency.py       # Latency analysis utility
    └── eval_intent_metrics.py  # Intent classification evaluation
```

### Key Files Description

- **`run.py`**: Orchestrates the system by running both Python 2 and Python 3 processes
- **`src/body.py`**: Flask API server that communicates with NAO robot (text-to-speech, gestures)
- **`src/sidecar.py`**: Main voice processing loop (audio recording → STT → KB/LLM → NAO TTS)
- **`src/format.py`**: Intent classification, knowledge base lookup, and LLM response formatting
- **`src/kb.json`**: Structured knowledge base containing rooms, labs, contacts, and hours
- **`src/avg_latency.py`**: Utility for analyzing latency metrics
- **`src/eval_intent_metrics.py`**: Evaluation script for intent classification performance
