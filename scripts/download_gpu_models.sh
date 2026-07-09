#!/usr/bin/env bash
# Pre-download Aurora model weights to the HF_HOME cache directory.
# Run once on the NVIDIA box before starting the GPU stack.
#
# Usage:
#   HF_HOME=/models/hf bash scripts/download_gpu_models.sh
#
# Requirements: the GPU virtualenv must be activated, or docker exec into
# the worker container and run this script there.
#
# Approximate download sizes (one-time):
#   LTX-Video         ~6 GB
#   SVD-XT            ~7 GB
#   FLUX.1-dev        ~23 GB
#   MusicGen-small    ~300 MB
#   Total             ~36 GB  (cached; re-runs are instant)

set -euo pipefail

HF_HOME="${HF_HOME:-/models/hf}"
export HF_HOME

log() { echo "[aurora] $*"; }

log "Downloading model weights → $HF_HOME"
log "First run takes 30–90 min depending on bandwidth (~36 GB total)."
echo ""

# Activate the backend virtualenv if running outside a container.
if [ -f "backend/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source backend/.venv/bin/activate
fi

python3 - <<'PYEOF'
import os
import sys

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("ERROR: huggingface_hub not found. Activate the GPU virtualenv first.", file=sys.stderr)
    sys.exit(1)

hf_home = os.environ.get("HF_HOME", "/models/hf")
os.makedirs(hf_home, exist_ok=True)

MODELS = [
    ("Lightricks/LTX-Video",                          "LTX-Video  (text→video, ~6 GB)"),
    ("stabilityai/stable-video-diffusion-img2vid-xt", "SVD-XT     (image→video, ~7 GB)"),
    ("black-forest-labs/FLUX.1-dev",                  "FLUX.1-dev (text→image, ~23 GB)"),
    ("facebook/musicgen-small",                       "MusicGen   (music, ~300 MB)"),
    # AI Edit (E5)
    ("runwayml/stable-diffusion-inpainting",          "SD-Inpaint (object removal, ~4 GB)"),
    ("stabilityai/stable-diffusion-2-1",              "SD-2.1     (masked v2v / restyle, ~5 GB)"),
    ("IDEA-Research/grounding-dino-tiny",             "GroundingDINO (text→boxes, ~700 MB)"),
    ("facebook/sam2-hiera-large",                     "SAM 2      (click→mask, ~900 MB)"),
]

failed = []
for repo_id, label in MODELS:
    print(f"\n→ {label}")
    try:
        path = snapshot_download(repo_id=repo_id, cache_dir=hf_home)
        print(f"  ✓  {path}")
    except Exception as exc:
        print(f"  ✗  FAILED: {exc}", file=sys.stderr)
        failed.append(repo_id)

print()
if failed:
    print(f"WARNING: {len(failed)} model(s) failed to download:", file=sys.stderr)
    for m in failed:
        print(f"  - {m}", file=sys.stderr)
    sys.exit(1)
else:
    print("✓ All models downloaded successfully.")
PYEOF
