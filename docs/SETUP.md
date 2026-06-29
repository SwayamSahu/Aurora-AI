# Aurora — Local Setup Guide (macOS & Windows)

A complete, beginner-friendly walkthrough to get **Aurora** running on your own
machine. No prior experience with this stack is assumed — if you can install an
app and copy/paste commands, you can run Aurora.

> **TL;DR (the fast path):** install **Docker Desktop** + **Git**, then run
> `docker compose -f infra/compose.dev.yml up --build` from the project root and
> open **http://localhost:3000**. Everything else below explains the details and
> alternatives.

---

## Table of contents

1. [What you're running](#1-what-youre-running)
2. [Prerequisites](#2-prerequisites)
3. [Path A — Run everything with Docker (recommended)](#3-path-a--run-everything-with-docker-recommended)
4. [Path B — Hybrid: services in Docker, apps local (best for coding)](#4-path-b--hybrid-services-in-docker-apps-run-locally-best-for-active-development)
5. [Verifying it works](#5-verifying-it-works)
6. [Everyday commands](#6-everyday-commands)
7. [Running tests & quality checks](#7-running-tests--quality-checks)
8. [Ports, URLs & credentials](#8-ports-urls--credentials)
9. [Troubleshooting](#9-troubleshooting)
10. [Project layout](#10-project-layout)

---

## 1. What you're running

Aurora is a full-stack app made of several cooperating services:

| Service | What it does | Tech |
|---|---|---|
| **frontend** | The website + app UI (landing page, studio, marketplace) | Next.js 16 + React 19 |
| **api** | Backend REST/WebSocket API | FastAPI (Python 3.11) |
| **worker** | Runs background jobs (generation, render, transcribe) | Celery |
| **db** | Stores users, projects, jobs | PostgreSQL 16 |
| **redis** | Job queue + cache | Redis 7 |
| **minio** | File/media storage (S3-compatible) | MinIO |

On your laptop, the AI generators run in **mock mode** (`GENERATOR_BACKEND=mock`)
— they return real placeholder media instantly, so you get the full app without
a GPU. FFmpeg, text-to-speech, and subtitles are **real** even on a laptop.

---

## 2. Prerequisites

### Required for everyone

| Tool | Version | macOS | Windows |
|---|---|---|---|
| **Git** | any recent | `brew install git` or [git-scm.com](https://git-scm.com) | [git-scm.com](https://git-scm.com) |
| **Docker Desktop** | latest | [docker.com](https://www.docker.com/products/docker-desktop/) | [docker.com](https://www.docker.com/products/docker-desktop/) (enable **WSL 2** backend) |

> **Windows note:** Docker Desktop must use the **WSL 2** backend (it offers to
> set this up on install). You'll run all commands either in **PowerShell** or,
> better, inside a **WSL 2 / Ubuntu** terminal. See the Windows tips in
> [§9](#9-troubleshooting).

After installing Docker Desktop, **launch it once** and wait until it says
"Docker Desktop is running" before continuing.

### Only needed for Path B (running the apps without Docker)

| Tool | Version | macOS | Windows |
|---|---|---|---|
| **Node.js** | 22.x | `brew install node@22` or [nodejs.org](https://nodejs.org) | [nodejs.org](https://nodejs.org) (LTS 22) |
| **Python** | 3.11.x | `brew install python@3.11` | [python.org](https://www.python.org/downloads/) (check "Add to PATH") |
| **FFmpeg** | recent | `brew install ffmpeg` | `winget install Gyan.FFmpeg` |
| **espeak-ng** (Linux/Windows TTS) | recent | not needed (macOS uses built-in `say`) | `winget install eSpeak-NG.eSpeak-NG` |

---

## 3. Path A — Run everything with Docker (recommended)

This is the easiest, most reliable way to run the whole stack. You don't need
Node, Python, or FFmpeg installed — Docker provides everything.

### Step 1 — Get the code

```bash
git clone <your-repo-url> aurora
cd aurora
```

### Step 2 — Start the stack

From the **project root** (the folder containing `infra/`, `backend/`, `frontend/`):

```bash
docker compose -f infra/compose.dev.yml up --build
```

The first run takes a few minutes (it downloads images and builds the app).
You'll know it's ready when you see logs like:

- `bucket ready` (MinIO created the media bucket)
- database migrations finishing on the **api** service
- `Ready in …` from the **frontend** (Next.js)

> You do **not** need to create any `.env` file for Path A — the compose file
> already points the backend at `backend/.env.example`, which has working
> defaults for the Docker network.

### Step 3 — Open the app

| URL | What |
|---|---|
| **http://localhost:3000** | The app + landing page |
| http://localhost:3000/explore | The AI marketplace |
| http://localhost:8000/docs | Interactive API docs (Swagger) |
| http://localhost:9001 | MinIO console (login `aurora` / `aurora-secret`) |

That's it — Aurora is running. To stop it, press **Ctrl+C**, then optionally
`docker compose -f infra/compose.dev.yml down`.

> **Tip:** add `-d` (`up --build -d`) to run in the background and get your
> terminal back. View logs with `docker compose -f infra/compose.dev.yml logs -f`.

---

## 4. Path B — Hybrid: services in Docker, apps run locally (best for active development)

When you're **editing code**, running the frontend and backend directly on your
machine gives faster, more reliable hot-reload than the Docker dev containers
(which can miss file changes — see [§9](#9-troubleshooting)). The supporting
services (database, Redis, MinIO) still run in Docker.

### Step 1 — Start only the supporting services

```bash
docker compose -f infra/compose.dev.yml up -d db redis minio minio-init
```

This leaves ports open for your local apps:
Postgres on **localhost:5434**, Redis on **6379**, MinIO on **9000/9001**.

### Step 2 — Backend (FastAPI + Celery)

```bash
cd backend

# Create + activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate          # macOS / Linux / WSL
# .venv\Scripts\Activate.ps1       # Windows PowerShell

# Install dependencies (dev.txt includes test tools)
pip install -r requirements/dev.txt

# Create your env file
cp .env.example .env               # macOS/Linux;  on PowerShell: copy .env.example .env
```

Now **edit `backend/.env`** so it points at the Docker services on `localhost`
(the defaults use Docker-internal hostnames like `db`/`redis`/`minio`):

```dotenv
DATABASE_URL=postgresql+psycopg2://aurora:aurora@localhost:5434/aurora
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
S3_ENDPOINT=localhost:9000
# Easiest dev option: run jobs inline so you don't need a separate worker.
CELERY_TASK_ALWAYS_EAGER=true
GENERATOR_BACKEND=mock
```

Apply the database schema and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

> **Want a real background worker** instead of inline jobs? Set
> `CELERY_TASK_ALWAYS_EAGER=false` in `.env` and, in a second terminal:
> ```bash
> cd backend && source .venv/bin/activate
> celery -A app.core.celery_app.celery_app worker --loglevel=info
> ```

### Step 3 — Frontend (Next.js)

In a new terminal:

```bash
cd frontend
npm ci

# Tell the frontend where the API is
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

Open **http://localhost:3000**.

---

## 5. Verifying it works

1. **Frontend loads** — http://localhost:3000 shows the Aurora landing page with
   the animated hero showreel.
2. **API is up** — http://localhost:8000/docs shows the Swagger UI.
3. **Create an account** — go to http://localhost:3000/signup, register with any
   email (use a real-looking domain like `you@example.com` — `.test`/`.local`
   addresses are rejected by validation), and you should land in the dashboard.
4. **Storage works** — http://localhost:9001 → login `aurora` / `aurora-secret` →
   you'll see the `aurora-media` bucket.

If all four pass, your environment is healthy.

---

## 6. Everyday commands

All Docker commands are run from the **project root**.

```bash
# Start / stop the full stack (Path A)
docker compose -f infra/compose.dev.yml up --build        # start (foreground)
docker compose -f infra/compose.dev.yml up -d             # start (background)
docker compose -f infra/compose.dev.yml stop              # stop, keep data
docker compose -f infra/compose.dev.yml down              # stop + remove containers
docker compose -f infra/compose.dev.yml down -v           # ALSO wipe DB + media (full reset)

# Logs
docker compose -f infra/compose.dev.yml logs -f           # all services
docker compose -f infra/compose.dev.yml logs -f frontend  # one service

# Restart a single service (e.g. after adding a new page/route)
docker compose -f infra/compose.dev.yml restart frontend

# Rebuild after changing dependencies (package.json / requirements)
docker compose -f infra/compose.dev.yml up --build api frontend
```

---

## 7. Running tests & quality checks

**Frontend** (from `frontend/`):

```bash
npm run typecheck      # TypeScript type checking
npm run lint           # ESLint
npm run test           # Vitest unit tests
npm run build          # Production build (also type-checks)
```

**Backend** (from `backend/`, with the venv active):

```bash
pip install -r requirements/dev.txt   # once, for pytest etc.
pytest                                # run the test suite
```

> The backend tests run fully on CPU/mock — no GPU or external services needed
> beyond what `dev.txt` installs.

---

## 8. Ports, URLs & credentials

| Service | URL / Port | Credentials |
|---|---|---|
| Frontend | http://localhost:3000 | — |
| API | http://localhost:8000 (docs at `/docs`) | — |
| API base path | all endpoints are under `/api/v1` | — |
| PostgreSQL | `localhost:5434` (→ container 5432) | user `aurora` / pass `aurora` / db `aurora` |
| Redis | `localhost:6379` | — |
| MinIO API | `localhost:9000` | `aurora` / `aurora-secret` |
| MinIO Console | http://localhost:9001 | `aurora` / `aurora-secret` |
| Media bucket | `aurora-media` | auto-created on first boot |

> **Heads-up:** Postgres is published on **5434** (not the usual 5432) to avoid
> clashing with other local Postgres instances. Inside the Docker network the
> services still talk to each other on standard ports.

---

## 9. Troubleshooting

### "Port is already allocated" / address in use
Another program is using one of the ports above (commonly 3000, 5432/5434, 6379,
8000, 9000). Stop that program, or edit the `ports:` mapping in
`infra/compose.dev.yml` (change the **left** number, e.g. `"3001:3000"`).

### Frontend shows a 500 error, or `TurbopackInternalError` / missing `.sst` file
The Next.js dev cache in the container got corrupted (a known Turbopack-in-Docker
quirk). Clear it and restart:

```bash
docker compose -f infra/compose.dev.yml exec frontend rm -rf /app/.next/dev
docker compose -f infra/compose.dev.yml restart frontend
```

### A new page/route returns 404, or code changes don't show up (Docker)
On macOS and Windows, file-change events don't always reach the dev server
through the Docker volume mount, so **new route folders** especially aren't
picked up live. Restart the frontend:

```bash
docker compose -f infra/compose.dev.yml restart frontend
```

For active UI work, prefer **Path B** (run `npm run dev` locally) — its
hot-reload is reliable.

### The page reloads forever / looks blank
Your browser tab is holding stale dev JavaScript. **Hard-reload**:
**Cmd+Shift+R** (macOS) / **Ctrl+Shift+R** (Windows), or close and reopen the tab.

### A "hydration mismatch" error mentioning `data-gr-*` attributes
That's a browser extension (e.g. Grammarly) editing the page before React loads.
It's harmless and won't appear in an Incognito window.

### "connection refused" to the database / Redis
The services may still be starting. Wait for the healthchecks (`docker compose …
ps` shows `healthy`). For Path B, confirm you started `db redis minio` and that
your `.env` uses `localhost:5434` for Postgres.

### Registration fails with an email validation error
Use a normal-looking domain (`you@example.com`). Reserved TLDs like `.test`,
`.local`, and `.example` are rejected by the email validator.

### Windows-specific tips
- Use the **WSL 2** backend in Docker Desktop (Settings → General).
- For best performance and to avoid line-ending issues, **clone the repo inside
  your WSL 2 home** (e.g. `\\wsl$\Ubuntu\home\you\aurora`) and run commands from
  the Ubuntu terminal, not from a Windows `C:\` path.
- If Git rewrites line endings, set `git config --global core.autocrlf input`.
- PowerShell venv activation: `.venv\Scripts\Activate.ps1` (you may need
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once).

### Apple Silicon (M1/M2/M3/M4)
Everything is arm64-compatible out of the box — no Rosetta or extra flags needed.
Generators stay in `mock` mode (real GPU inference is a separate NVIDIA-only
phase).

### Start completely fresh
```bash
docker compose -f infra/compose.dev.yml down -v   # removes containers + volumes
docker compose -f infra/compose.dev.yml up --build
```

---

## 10. Project layout

| Path | Purpose |
|---|---|
| `frontend/` | Next.js app — landing page, studio UI, timeline editor, marketplace |
| `backend/` | FastAPI app, Celery workers, generators, FFmpeg media pipeline |
| `backend/requirements/` | Python deps: `app.txt` (runtime), `dev.txt` (+ tests), `gpu.txt` (NVIDIA only) |
| `infra/` | Docker Compose files (`compose.dev.yml` for laptops, `compose.gpu.yml` for the GPU box) |
| `docs/` | This guide, the build roadmap, and architecture notes |
| `scripts/` | Helper scripts (e.g. GPU model download — GPU box only) |

---

### Need more context?

- Architecture & phases: [`docs/roadmap.md`](roadmap.md)
- Project overview: [`README.md`](../README.md)
- API reference: run the stack and open http://localhost:8000/docs

Welcome aboard — happy building! 🎬
