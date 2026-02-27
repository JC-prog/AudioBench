# AudioBench

Gradio-based web interface for benchmarking and testing audio-to-text APIs.

## Features

- Record audio via microphone or upload an audio file
- Play back recorded/uploaded audio before submitting
- Two backends: **API** (remote) or **Local (faster-whisper)**
- Transcribe audio to text
- Translate audio to a target language
- Performance metrics displayed after each request

## Backends

### API
Sends audio to a remote HTTP endpoint. Requires an API key and endpoint URL. Supports translation to any target language.

### Local (faster-whisper)
Runs [faster-whisper](https://github.com/SYSTRAN/faster-whisper) entirely on-device using CTranslate2 — no API key or internet connection needed. Models are downloaded automatically from Hugging Face on first use.

> **Translation note:** Local translation outputs **English only**. This is a limitation of the underlying Whisper model architecture. For other target languages, use the API backend.

| Model Size | Speed | Accuracy |
|---|---|---|
| tiny | Fastest | Lowest |
| base | Fast | Good |
| small | Moderate | Better |
| medium | Slow | High |
| large-v2 / large-v3 | Slowest | Highest |

## Performance Metrics

After each request, the app shows:

| Metric | Description |
|---|---|
| **Latency** | End-to-end processing time (seconds) |
| **Audio Duration** | Length of the audio clip (seconds, WAV only) |
| **Real-time Factor** | Latency ÷ Audio Duration — below 1.0 means faster-than-real-time |
| **Audio File Size** | Size of the audio file (KB) |
| **Detected Language** | Source language and confidence (local backend only) |

## Setup

**Prerequisites:** [ffmpeg](https://ffmpeg.org/download.html) must be installed and on your PATH (required by faster-whisper for audio decoding).

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:7860` in your browser.

## Usage

1. Select a **Backend**: API or Local (faster-whisper)
2. **API:** Enter your API Key and Endpoint
   **Local:** Select a model size
3. Record audio with the microphone or upload a WAV/MP3/OGG file
4. Click **Transcribe** for a transcript, or select a target language and click **Translate**
5. View the result and performance metrics below

## API Reference

Expected endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/audio/transcription` | POST | Transcribe audio to text |
| `/audio/translation` | POST | Translate audio to another language |

**Audio requirements:** 16 kHz, mono. Recommended formats: WAV, MP3, OGG.
