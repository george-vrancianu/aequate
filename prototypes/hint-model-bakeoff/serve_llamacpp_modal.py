"""PROTOTYPE. llama.cpp CUDA llama-server on Modal (L4), serving one GGUF (default: the official Gemma 4 E4B QAT q4_0).
Same llama.cpp build as the local CPU run (b12211). Usage:
  modal deploy serve_llamacpp_modal.py   (then: modal app stop aq31-gemma4-e4b-q4-llamacpp)
Env: AQ_REPO, AQ_FILE (GGUF in the HF repo), AQ_APP, AQ_TAG (ghcr.io/ggml-org/llama.cpp tag)."""
import os, subprocess
import modal

REPO = os.environ.get("AQ_REPO", "google/gemma-4-E4B-it-qat-q4_0-gguf")
FILE = os.environ.get("AQ_FILE", "gemma-4-E4B_q4_0-it.gguf")
APP = os.environ.get("AQ_APP", "aq31-gemma4-e4b-q4-llamacpp")
TAG = os.environ.get("AQ_TAG", "server-cuda12-b12211")

image = (
    modal.Image.from_registry(f"ghcr.io/ggml-org/llama.cpp:{TAG}", add_python="3.12")
    .entrypoint([])
    .pip_install("huggingface_hub")
    .env({"AQ_REPO": REPO, "AQ_FILE": FILE, "HF_HOME": "/cache"})
)
cache = modal.Volume.from_name("aq31-hf-cache", create_if_missing=True)
app = modal.App(APP)


@app.function(image=image, gpu="L4", volumes={"/cache": cache}, scaledown_window=120, timeout=30 * 60, max_containers=1)
@modal.web_server(8000, startup_timeout=20 * 60)
def serve():
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(REPO, FILE)
    cmd = ["/app/llama-server", "-m", path, "--host", "0.0.0.0", "--port", "8000", "--jinja", "-c", "4096", "--parallel", "1",
           "-ngl", "99", "--alias", "m"]
    print("CMD", cmd, flush=True)
    subprocess.Popen(cmd)
