"""PROTOTYPE. vLLM OpenAI-compatible server on Modal (L4), one app per model.
Usage: AQ_MODEL=Qwen/Qwen3.5-4B AQ_APP=aq31-qwen35-4b modal deploy serve_modal.py   (then: modal app stop aq31-qwen35-4b)
AQ_EXTRA = extra vllm serve flags (e.g. Mistral tokenizer/config/load-format flags)."""
import os, subprocess
import modal

MODEL = os.environ.get("AQ_MODEL", "Qwen/Qwen3.5-4B")
APP = os.environ.get("AQ_APP", "aq31-test")
EXTRA = os.environ.get("AQ_EXTRA", "")
VLLM = os.environ.get("AQ_VLLM", "0.33.0")

image = (
    modal.Image.from_registry("nvidia/cuda:12.9.1-devel-ubuntu22.04", add_python="3.12")   # devel image: flashinfer JIT needs nvcc
    .pip_install(f"vllm=={VLLM}", "huggingface_hub")
    .env({"AQ_MODEL": MODEL, "AQ_EXTRA": EXTRA, "HF_HOME": "/cache", "VLLM_USE_FLASHINFER_SAMPLER": "0", "VLLM_LOGGING_LEVEL": "INFO"})
)
cache = modal.Volume.from_name("aq31-hf-cache", create_if_missing=True)
app = modal.App(APP)


@app.function(image=image, gpu="L4", volumes={"/cache": cache}, scaledown_window=120, timeout=30 * 60, max_containers=1)
@modal.web_server(8000, startup_timeout=20 * 60)
def serve():
    cmd = ["vllm", "serve", MODEL, "--served-model-name", "m", "--host", "0.0.0.0", "--port", "8000",
           "--max-model-len", "4096", "--enforce-eager", "--gpu-memory-utilization", "0.90", *EXTRA.split()]
    print("CMD", cmd, flush=True)
    subprocess.Popen(cmd)
