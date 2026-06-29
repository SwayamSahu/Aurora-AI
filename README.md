# Aurora — AI Video Generation Platform

An open-source platform to **generate** AI videos (text→video, image→video), **enrich** them with AI voiceover, auto-subtitles, images and music, and **edit** everything on a professional multi-track timeline before exporting a final MP4.

Built entirely with free & open-source software. Developed on macOS (Apple Silicon, CPU/mock) and deployed on an NVIDIA 16GB GPU for real model inference.

---

## Architecture at a glance

```
Next.js (UI + timeline editor)  ──REST/WS──>  FastAPI  ──>  Celery + Redis  ──>  Workers
                                                  │                                 │
                                              PostgreSQL                     ┌───────┴────────┐
                                                  │                          │ Generators     │ (Mock on Mac,
                                              MinIO (S3)  <──────────────────│ Media (FFmpeg) │  CUDA on GPU box)
                                                                             │ Transcribe     │
                                                                             └────────────────┘
```

The **generator backend is swappable** via `GENERATOR_BACKEND`:
- `mock` — returns real fixture media instantly. Full app is built & tested on the Mac with this.
- `cuda` — runs real models (LTX-Video, CogVideoX, SVD, FLUX/SDXL, MusicGen) on the NVIDIA box.

FFmpeg, TTS and Whisper transcription are **real on both platforms** (CPU-capable), so only diffusion generation is deferred to the GPU phase.

---

## Repository layout

| Path | Purpose |
|------|---------|
| `frontend/` | Next.js 15 + TypeScript + Tailwind + shadcn/ui. All UI screens & the timeline editor. |
| `backend/` | FastAPI app, Celery workers, generators, media/FFmpeg pipeline. |
| `infra/` | Docker Compose (`compose.dev.yml` for Mac, `compose.gpu.yml` for the NVIDIA box). |
| `docs/` | Architecture, API reference, GPU transfer runbook. |
| `scripts/` | Dev seed data, model download (GPU box only). |

---

## Quick start (development)

> 📘 **New here?** Read the full step-by-step guide for macOS & Windows:
> **[docs/SETUP.md](docs/SETUP.md)** — prerequisites, Docker & hybrid workflows,
> tests, and troubleshooting.

Prerequisites: Docker Desktop + Git. (For non-Docker dev: Node 22, Python 3.11.)

```bash
# Start everything (Postgres, Redis, MinIO, API, worker, frontend)
docker compose -f infra/compose.dev.yml up --build

# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
# MinIO:     http://localhost:9001  (aurora / aurora-secret)
```

For local (non-Docker) development of each part, see **[docs/SETUP.md](docs/SETUP.md)**.

## Build phases

This project is built in phases — non-GPU work is fully developed and tested on the Mac (Phases 0–8); GPU model integration and testing happen last on the NVIDIA box (Phase 9). See `docs/roadmap.md`.

## License

The platform code is MIT. Bundled AI models retain their own licenses — see `docs/model-licenses.md`.
