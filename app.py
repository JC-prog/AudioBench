import base64
import os
import time
import wave
import requests
import gradio as gr
from faster_whisper import WhisperModel


MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

LANGUAGES = [
    "English",
    "Chinese",
    "Malay",
    "Tamil",
    "Japanese",
    "Korean",
    "French",
    "German",
    "Spanish",
]

MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]

_model_cache: dict = {}
_model_devices: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def encode_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_audio_duration(audio_path: str):
    try:
        with wave.open(audio_path) as wf:
            return wf.getnframes() / wf.getframerate()
    except Exception:
        return None


def format_metrics(latency: float, audio_path: str) -> str:
    lines = [f"Latency:            {latency:.2f} s"]
    duration = get_audio_duration(audio_path)
    if duration is not None:
        lines.append(f"Audio Duration:     {duration:.2f} s")
        if duration > 0:
            lines.append(f"Real-time Factor:   {latency / duration:.3f}x")
    size_kb = os.path.getsize(audio_path) / 1024
    lines.append(f"Audio File Size:    {size_kb:.1f} KB")
    return "\n".join(lines)


def get_model(model_size: str) -> WhisperModel:
    if model_size not in _model_cache:
        try:
            model = WhisperModel(model_size, device="cuda", compute_type="float16", download_root=MODELS_DIR)
            _model_devices[model_size] = "cuda"
        except Exception:
            model = WhisperModel(model_size, device="cpu", compute_type="int8", download_root=MODELS_DIR)
            _model_devices[model_size] = "cpu"
        _model_cache[model_size] = model
    return _model_cache[model_size]


# ---------------------------------------------------------------------------
# API backend
# ---------------------------------------------------------------------------

def transcribe_api(audio_path, api_key, endpoint):
    if not audio_path:
        return "No audio provided. Please record or upload audio first.", ""
    if not api_key:
        return "API key is required.", ""
    if not endpoint:
        return "Endpoint is required.", ""

    try:
        audio_b64 = encode_audio(audio_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        body = {
            "audio_url": f"data:audio/wav;base64,{audio_b64}",
            "stream": False,
        }
        t0 = time.perf_counter()
        response = requests.post(
            f"{endpoint}/audio/transcription", headers=headers, json=body, timeout=120
        )
        latency = time.perf_counter() - t0
        response.raise_for_status()
        result = response.json()
        text = result["choices"][0]["message"]["content"].strip()
        return text, format_metrics(latency, audio_path)
    except requests.HTTPError as e:
        return f"HTTP error {e.response.status_code}: {e.response.text}", ""
    except Exception as e:
        return f"Error: {e}", ""


def translate_api(audio_path, api_key, endpoint, target_language):
    if not audio_path:
        return "No audio provided. Please record or upload audio first.", ""
    if not api_key:
        return "API key is required.", ""
    if not endpoint:
        return "Endpoint is required.", ""

    try:
        audio_b64 = encode_audio(audio_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        body = {
            "audio_url": f"data:audio/wav;base64,{audio_b64}",
            "translation_params": {
                "source_language": "",
                "target_language": target_language,
            },
            "stream": False,
        }
        t0 = time.perf_counter()
        response = requests.post(
            f"{endpoint}/audio/translation", headers=headers, json=body, timeout=120
        )
        latency = time.perf_counter() - t0
        response.raise_for_status()
        result = response.json()
        text = result["choices"][0]["message"]["content"].strip()
        return text, format_metrics(latency, audio_path)
    except requests.HTTPError as e:
        return f"HTTP error {e.response.status_code}: {e.response.text}", ""
    except Exception as e:
        return f"Error: {e}", ""


# ---------------------------------------------------------------------------
# Local backend (faster-whisper)
# ---------------------------------------------------------------------------

def transcribe_local(audio_path, model_size):
    if not audio_path:
        return "No audio provided. Please record or upload audio first.", ""

    try:
        t0 = time.perf_counter()
        model = get_model(model_size)
        segments, info = model.transcribe(audio_path, beam_size=5)
        text = " ".join(seg.text for seg in segments).strip()
        latency = time.perf_counter() - t0
        metrics = format_metrics(latency, audio_path)
        metrics += f"\nDetected Language:  {info.language} ({info.language_probability:.0%})"
        metrics += f"\nDevice:             {_model_devices.get(model_size, 'unknown')}"
        return text, metrics
    except Exception as e:
        return f"Error: {e}", ""


def translate_local(audio_path, model_size):
    if not audio_path:
        return "No audio provided. Please record or upload audio first.", ""

    try:
        t0 = time.perf_counter()
        model = get_model(model_size)
        segments, info = model.transcribe(audio_path, task="translate", beam_size=5)
        text = " ".join(seg.text for seg in segments).strip()
        latency = time.perf_counter() - t0
        metrics = format_metrics(latency, audio_path)
        metrics += f"\nDetected Language:  {info.language} ({info.language_probability:.0%})"
        metrics += f"\nDevice:             {_model_devices.get(model_size, 'unknown')}"
        return text, metrics
    except Exception as e:
        return f"Error: {e}", ""


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

def run_transcribe(audio_path, api_key, endpoint, backend, model_size):
    if backend == "API":
        return transcribe_api(audio_path, api_key, endpoint)
    return transcribe_local(audio_path, model_size)


def run_translate(audio_path, api_key, endpoint, target_language, backend, model_size):
    if backend == "API":
        return translate_api(audio_path, api_key, endpoint, target_language)
    return translate_local(audio_path, model_size)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def toggle_backend(backend):
    is_api = backend == "API"
    return (
        gr.update(visible=is_api),       # api_row
        gr.update(visible=not is_api),   # local_row
        gr.update(visible=is_api),       # target_language dropdown
        gr.update(visible=not is_api),   # english-only note
    )


with gr.Blocks(title="AudioBench") as demo:
    gr.Markdown("# AudioBench")

    backend = gr.Radio(
        ["API", "Local (faster-whisper)"],
        value="API",
        label="Backend",
    )

    with gr.Row() as api_row:
        api_key = gr.Textbox(
            label="API Key",
            type="password",
            placeholder="Enter your API key",
        )
        endpoint = gr.Textbox(
            label="Endpoint",
            placeholder="https://your-api-endpoint",
        )

    with gr.Row(visible=False) as local_row:
        model_size = gr.Dropdown(
            label="Model Size",
            choices=MODEL_SIZES,
            value="base",
        )

    audio = gr.Audio(
        label="Audio",
        sources=["microphone", "upload"],
        type="filepath",
    )

    with gr.Row():
        transcribe_btn = gr.Button("Transcribe", variant="primary")
        translate_btn = gr.Button("Translate", variant="primary")
        target_language = gr.Dropdown(
            label="Target Language",
            choices=LANGUAGES,
            value="English",
        )
        english_note = gr.Markdown(
            "*Local translation outputs English only.*",
            visible=False,
        )

    output = gr.Textbox(label="Result", lines=8, interactive=False)
    metrics = gr.Textbox(label="Performance Metrics", lines=5, interactive=False)

    backend.change(
        fn=toggle_backend,
        inputs=[backend],
        outputs=[api_row, local_row, target_language, english_note],
    )

    transcribe_btn.click(
        fn=run_transcribe,
        inputs=[audio, api_key, endpoint, backend, model_size],
        outputs=[output, metrics],
    )

    translate_btn.click(
        fn=run_translate,
        inputs=[audio, api_key, endpoint, target_language, backend, model_size],
        outputs=[output, metrics],
    )


if __name__ == "__main__":
    demo.launch()
