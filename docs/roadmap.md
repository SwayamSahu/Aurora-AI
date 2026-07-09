# Build Roadmap

Non-GPU work (Phases 0–8) is fully developed **and tested** on the MacBook (Apple Silicon, CPU/mock).
GPU model integration and testing (Phase 9) happen on the NVIDIA 16GB box via RDP.

| Phase | Scope | Runs on | Status |
|-------|-------|---------|--------|
| **0** | Scaffold, Docker dev stack, design system, app shell, CI | Mac | ✅ done |
| 1 | Auth, accounts, settings | Mac | ✅ done |
| 2 | Projects & asset library | Mac | ✅ done |
| 3 | Job queue + WebSocket progress + Mock generator contract | Mac | ✅ done |
| 4 | Generation studio UI | Mac | ✅ done |
| 5 | Timeline editor core | Mac | ✅ done |
| 6 | Real TTS voiceover + real Whisper captions + text overlays | Mac | ✅ done |
| 7 | Real FFmpeg render & export | Mac | ✅ done |
| 8 | Hardening, polish, accessibility, GPU code written (not run) | Mac | ✅ done |
| **9** | Swap to CUDA generators, download weights, tune for 16GB VRAM, GPU E2E | NVIDIA (RDP) | ⬜ |

## Phase 0 — Definition of done
- [x] Monorepo structure with git
- [x] Frontend: Next.js 16 + TS + Tailwind v4 + design tokens + shadcn-style primitives
- [x] App shell: sidebar nav, top bar, theme switcher (dark/light), command palette (⌘K)
- [x] Shared states: EmptyState, ErrorState, Skeletons, Toaster
- [x] `/design` route rendering all component states
- [x] Backend: FastAPI skeleton, health route, config with `GENERATOR_BACKEND` switch
- [x] Generator contract (`base.py`) + Mock implementations + real fixtures
- [x] DB models (user/project/asset/job/timeline) + Alembic initialized
- [x] Celery app skeleton
- [x] Requirements split (base / app / gpu / dev)
- [x] infra: `compose.dev.yml`, `compose.gpu.yml`, Dockerfiles (validated)
- [x] CI: lint + typecheck + test workflow
- [x] Boot test: frontend builds & serves, backend imports & serves, 5 tests pass

## Phase 1 — Definition of done
- [x] Backend security: bcrypt hashing + JWT (access + reset tokens)
- [x] Auth API: register, login (OAuth2), me, refresh, password-reset request/confirm
- [x] Users API: update profile, change password (with current-password check)
- [x] `get_current_user` dependency + protected routes (401 without token)
- [x] Initial Alembic migration (users/projects/assets/jobs/timeline) generated
- [x] Frontend: API client + token store + AuthProvider/useAuth
- [x] Auth screens: login, signup, forgot-password, reset-password (react-hook-form + zod)
- [x] Branded auth layout; route protection (AuthGuard) + RedirectIfAuthed
- [x] Settings screen: Profile, Appearance (theme), Generation defaults, Security
- [x] Topbar wired to real user + functional sign out
- [x] Test gate: 18 backend tests pass; frontend lint/typecheck/build green; live E2E smoke (register→login→me→profile→401)

## Phase 2 — Definition of done
- [x] Swappable storage (`local` for Mac/tests, `minio` for stack/prod) — `app/storage/`
- [x] Project CRUD API (create/list/get/update/delete/duplicate) with owner scoping + search/sort
- [x] Asset API: multipart upload, list (+kind filter), get, rename, delete, content streaming
- [x] Media content endpoint with flexible auth (bearer header OR `?token=` for media tags)
- [x] Frontend API clients + TanStack Query hooks (projects, assets)
- [x] Projects list: search (debounced), sort, grid, create/rename/duplicate/delete, empty/error/loading states
- [x] Project detail page: asset library with drag-drop uploader, kind tabs, previews, rename/delete/download
- [x] Dashboard wired to real projects (stats + recent projects)
- [x] Test gate: 34 backend tests pass; frontend lint/typecheck/build green; live E2E smoke (project→upload real MP4→download byte-exact→delete)

## Phase 3 — Definition of done
- [x] Celery wired with task module; eager mode for Mac dev/tests (no Redis needed)
- [x] Job model lifecycle: queued → running → succeeded/failed/cancelled with progress
- [x] Job runner orchestration: drives generator from registry, stores result as generated Asset
- [x] Jobs API: create (eager-inline vs Celery dispatch), list (+filters), get, retry, cancel
- [x] WebSocket progress endpoint (DB-polling — backend-agnostic, no Redis pub/sub needed)
- [x] Frontend: jobs API + hooks (auto-refetch while active) + WebSocket progress hook
- [x] Generation dialog (prompt/model/resolution/duration) with live progress bar
- [x] Jobs/render-queue page: status badges, live progress, result thumbnails, retry/cancel
- [x] Generate wired into project detail + jobs page; generated assets land in the library
- [x] Test gate: 43 backend tests pass (incl. 2 WebSocket); frontend lint/typecheck/build green; live E2E smoke (generate→succeeded→generated asset in library)

## Phase 4 — Definition of done
- [x] Shared `useGeneration` hook (create job + live WS progress + cache invalidation)
- [x] Full-page generation studio with project selector (+ inline create)
- [x] Prompt composer: type toggle, prompt, negative prompt, model/resolution/duration, seed (+ randomize)
- [x] Style presets (cinematic/photoreal/anime/3D/watercolor/noir) that shape prompt + negative prompt
- [x] Live preview panel (progress while generating, video/image result with download + send-to-editor)
- [x] Generation history gallery (thumbnails, select to preview)
- [x] `?mode=` deep-linking from dashboard start options; editor placeholder route added
- [x] Test gate: frontend lint/typecheck/build green (15 routes); studio/editor routes render; built on Phase 3's proven generate pipeline (no backend changes)

## Phase 5 — Definition of done
- [x] Backend: timeline document model + get/save API (current TimelineVersion per project)
- [x] Non-destructive project-JSON (tracks → clips referencing assets) with validation
- [x] Zustand editor store with undo/redo history, selection, transport, zoom
- [x] Multi-track timeline: ruler, lanes, draggable playhead, zoom
- [x] Clip blocks: drag-to-move + left/right trim handles, snapping, thumbnails
- [x] Preview canvas: video/image rendering, text overlays, rAF playback + transport
- [x] Inspector: position/duration/trim + text content & styling
- [x] Toolbar: add text, split, duplicate, delete, undo/redo, zoom, save indicator
- [x] Asset tray: add project media to the timeline
- [x] Autosave (debounced) + keyboard shortcuts (space/delete/⌘Z/⌘⇧Z/S)
- [x] Vitest set up; 10 editor-store unit tests (split/undo/redo/add/remove/duplicate); CI runs them
- [x] Test gate: 48 backend tests + 10 frontend unit tests pass; lint/typecheck/build green; live timeline round-trip with real clip references verified

## Phase 6 — Definition of done
- [x] `Transcriber` interface + segments→SRT helper in the generator contract
- [x] Real CPU TTS (`SayVoiceGenerator` macOS / `EspeakVoiceGenerator` Linux) — no ML deps
- [x] Real CPU transcription (`WhisperTranscriber` via faster-whisper, int8)
- [x] `audio_backend` setting (real CPU vs mock), separate from the GPU switch; graceful fallback
- [x] TTS, TRANSCRIBE, MUSIC wired through the job runner; transcribe → SRT subtitles asset
- [x] Jobs API accepts new types with per-type validation (text / asset_id / prompt)
- [x] Editor AI panel: Add voiceover (→ audio track) + Auto-subtitles (→ timed caption clips)
- [x] SRT parser + `addCaptionClips` store action; espeak-ng added to backend Docker image
- [x] Test gate: 54 backend tests + 13 frontend unit tests pass; lint/build green; **live REAL E2E**: `say` TTS (3.5s WAV) → Whisper transcription → accurate SRT, all CPU/no-GPU

## Kokoro TTS (between Phase 6 & 7)
- [x] `TtsEngine` enum (auto|say|espeak|kokoro|mock) + `TTS_ENGINE`, `KOKORO_LANG`, `KOKORO_DEFAULT_VOICE` settings
- [x] `KokoroVoiceGenerator` (torch/fp32, lru_cache singleton, WAV output via stdlib wave)
- [x] `resolve_voice_generator()` honours `TTS_ENGINE` with graceful fallback chain
- [x] `app/audio/voices.py` — per-engine voice catalogues (24 Kokoro voices, 7 say, 6 espeak)
- [x] `GET /api/v1/audio/voices` → engine + voices list; frontend `useVoices()` hook replaces hardcoded list
- [x] `requirements/tts-kokoro.txt` (opt-in, ~600MB-1GB with torch); `TTS_VOICES` removed from frontend
- [x] 16 TTS-engine unit tests (engine resolution + voices endpoint), no Kokoro/model in CI
- [x] Test gate: 70 backend tests; lint/build green; voices endpoint returns correct engine + voices live

## Phase 7 — Definition of done
- [x] `build_render_plan()` — pure function translating timeline JSON → RenderPlan (testable without FFmpeg)
- [x] `render_to_mp4()` — FFmpeg filter graph: black base + clip overlays + audio mix + fade-in/out
- [x] Caption burning via `drawtext` (when libfreetype present) or SRT sidecar graceful degradation
- [x] Export job runner: downloads assets → builds plan → renders → uploads MP4 as derived asset
- [x] Export API `POST /projects/{id}/export` + ExportRequest schema (width/height/fps/crf/fade)
- [x] Export Celery task + eager dispatch; export result added to the project asset library
- [x] Frontend: export dialog (settings/rendering/done/error phases), progress bar, download button
- [x] Export button wired into editor toolbar and project detail page
- [x] 12 export tests (7 unit plan-builder + 5 API incl. real MP4 render); 82 total backend tests
- [x] Test gate: 82 backend + 13 frontend unit tests pass; lint/build green; **live REAL E2E**: upload real MP4 → save timeline + caption → export → download **37.2 KB valid 4s MP4**

## Clip-to-clip transitions (between Phase 7 & 8)
- [x] `transition_in` field on `TimelineClip` schema — FFmpeg xfade names (fade/dissolve/wipeleft/…) or null for hard cut
- [x] `VideoSegment.transition_in` carried through `build_render_plan()`
- [x] `render_to_mp4()` rebuilt: concat + xfade chain replaces overlay-on-black; black fills for timeline gaps
- [x] Inspector "Transition in" dropdown for video clips (7 options)
- [x] 3 new plan-builder unit tests; **85 total backend tests**

## Phase 8 — Definition of done
- [x] CUDA generator implementations written (not run): `app/generators/cuda/` package
  - `CudaVideoGenerator` — LTX-Video (bfloat16, CPU offload, ~6 GB VRAM)
  - `CudaImageToVideoGenerator` — SVD-XT (fp16, CPU offload, ~7 GB VRAM)
  - `CudaImageGenerator` — FLUX.1-dev (bfloat16, sequential CPU offload, ~16 GB)
  - `CudaMusicGenerator` — MusicGen-small via HF Transformers (~1 GB)
- [x] `app/generators/cuda/vram.py` — one-model-at-a-time VRAM manager (evict + gc + cache flush)
- [x] Registry already wired: `get_video_generator()` etc. import from `app.generators.cuda` when `GENERATOR_BACKEND=cuda`
- [x] `scripts/download_gpu_models.sh` — pre-downloads all weights to `HF_HOME` (~36 GB total)
- [x] Prod error masking: global `Exception` handler in `app/main.py` returns generic 500 JSON (hides tracebacks in production)
- [x] React `ErrorBoundary` component (`components/shared/error-boundary.tsx`) wrapping the workspace layout
- [x] Clip block keyboard accessibility: `onKeyDown` Delete/Backspace removes clip; `aria-label` with kind + name + duration
- [x] Transition badge: tiny pill on clip bottom-left shows transition type (e.g. "fade") when set
- [x] Test gate: **85 backend + 13 frontend unit tests pass**; ruff + lint/typecheck/build green

## AI Edit workspace (Runway/Pika-class in-editor editing)

Prompt- and mask-driven editing inside the editor page (`/projects/[id]/editor`,
"AI Edit" mode). ~29 spec feature families collapse onto 8 engine primitives; a
data-driven preset catalog (~120 presets) sits on top. Mock-first on Mac, CUDA
on the NVIDIA box.

| Sub-phase | Scope | Runs on | Status |
|-----------|-------|---------|--------|
| **E1** | Mode switcher, mask canvas (brush/eraser/lasso/rect/ellipse), preset catalog, prompt panel | Mac | ✅ done |
| **E2** | `edit_layers` model+API+Celery, mock editor (real FFmpeg), layers panel, before/after slider, export substitution | Mac | ✅ done |
| **E3** | Real retime/camera (FFmpeg), real color grading (18 lighting/time/season recipes), OCR text-detect (Tesseract) | Mac (real) | ✅ done |
| **E4** | Tracking UX: click-to-select, "select all X", object chips, per-object presence ranges (mock detector) | Mac | ✅ done |
| **E5** | CUDA editor (SD inpaint/img2img, Real-ESRGAN) + detector (SAM 2, GroundingDINO) — **code written, GPU-run deferred** | NVIDIA (RDP) | 🟡 written, not run |
| E6 | Face swap + human replacement behind a consent gate; batch multi-clip; export presets | NVIDIA (RDP) | ⬜ |

### E5 — Definition of done (GPU code written; runs in Phase 9)
- [x] `VideoEditor` + `ObjectDetector` contracts; `get_video_editor()` / `get_object_detector()` registry entries
- [x] `CudaVideoEditor` (`generators/cuda/editor.py`): SD inpaint (remove), SD img2img (masked v2v / restyle), Real-ESRGAN (enhance); non-generative engines (retime, color grade, OCR) delegate to the shared FFmpeg/Tesseract impl
- [x] `CudaObjectDetector` (`generators/cuda/detector.py`): SAM 2 click→mask→bbox, GroundingDINO text→boxes
- [x] All GPU imports lazy → **importable on CPU-only Mac** (verified: no torch installed, classes import, registry still resolves mock)
- [x] `gpu.txt` + `download_gpu_models.sh` extended (SD-inpaint, SD-2.1, GroundingDINO, SAM 2); SAM 2 / ProPainter noted as GitHub installs
- [x] Detect route attaches clip source bytes so real backends have a frame; mock ignores them
- [x] Test gate: **106 backend tests pass** (incl. 4 E5: CPU-only import, FFmpeg-delegated retime + grade run on Mac, detector source guard); ruff + format clean
- [ ] **Deferred to Phase 9 (NVIDIA box):** real inference, 16 GB VRAM tuning, temporal-coherence upgrade (Wan 2.1 VACE / AnimateDiff), GPU E2E
