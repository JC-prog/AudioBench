# AudioBench

Gradio-based web interface for benchmarking and testing audio-to-text APIs, starting with the MERaLiON API.

## Features

- Record audio via microphone or upload an audio file
- Play back recorded/uploaded audio before submitting
- Enter API key and endpoint at runtime (no hardcoding)
- Transcribe audio to text
- Translate audio to a target language
- Performance metrics displayed after each request

## Performance Metrics

After each transcription or translation request, the app shows:

| Metric | Description |
|---|---|
| **Latency** | End-to-end API round-trip time (seconds) |
| **Audio Duration** | Length of the audio clip (seconds, WAV only) |
| **Real-time Factor** | Latency ÷ Audio Duration — values below 1.0 mean faster-than-real-time processing |
| **Audio File Size** | Size of the audio file sent to the API (KB) |

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:7860` in your browser.

## Usage

1. Enter your **API Key** and **Endpoint** at the top
2. Record audio with the microphone or upload a WAV/MP3/OGG file
3. Click **Transcribe** to get a text transcript, or select a target language and click **Translate**
4. View the result and performance metrics below

## API Reference

The app targets the MERaLiON API. Relevant endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/audio/transcription` | POST | Transcribe audio to text |
| `/audio/translation` | POST | Translate audio to another language |

**Audio requirements:** 16 kHz, mono. Recommended formats: WAV, MP3, OGG.
