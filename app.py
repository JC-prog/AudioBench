import base64
import os
import time
import wave
import requests
import gradio as gr


DEFAULT_ENDPOINT = ""

LANGUAGES = [
    "Chinese",
    "Malay",
    "Tamil",
    "English",
    "Japanese",
    "Korean",
    "French",
    "German",
    "Spanish",
]


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


def transcribe(audio_path, api_key, endpoint):
    if not audio_path:
        return "No audio provided. Please record or upload audio first.", ""
    if not api_key:
        return "API key is required.", ""
    if not endpoint:
        endpoint = DEFAULT_ENDPOINT

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


def translate(audio_path, api_key, endpoint, target_language):
    if not audio_path:
        return "No audio provided. Please record or upload audio first.", ""
    if not api_key:
        return "API key is required.", ""
    if not endpoint:
        endpoint = DEFAULT_ENDPOINT

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


with gr.Blocks(title="MERaLiON Audio API Tester") as demo:
    gr.Markdown("# MERaLiON Audio API Tester")

    with gr.Row():
        api_key = gr.Textbox(
            label="API Key",
            type="password",
            placeholder="TTSH-...",
        )
        endpoint = gr.Textbox(
            label="Endpoint",
            placeholder="https://your-api-endpoint",
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
            value="Chinese",
        )

    output = gr.Textbox(label="Result", lines=8, interactive=False)
    metrics = gr.Textbox(label="Performance Metrics", lines=4, interactive=False)

    transcribe_btn.click(
        fn=transcribe,
        inputs=[audio, api_key, endpoint],
        outputs=[output, metrics],
    )

    translate_btn.click(
        fn=translate,
        inputs=[audio, api_key, endpoint, target_language],
        outputs=[output, metrics],
    )


if __name__ == "__main__":
    demo.launch()
