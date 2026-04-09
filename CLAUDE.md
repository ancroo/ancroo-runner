# ancroo-runner — Deterministic Script Runner

**Language:** Python 3.12 (FastAPI)
**License:** MIT

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI entry point |
| `app/plugin_loader.py` | Plugin discovery & dynamic route registration |
| `plugins/` | Builtin plugins (shipped with image) |
| `entrypoint.sh` | Installs plugin requirements, starts uvicorn |
| `module/` | ancroo-stack integration (Compose overlays) |
| `module/module.conf` | Stack module metadata |
| `install-stack.sh` | Stack integration script |
| `workflows/` | Example workflow definitions (for backend import) |

## API Endpoints

- `GET /health` — Health check (status, commit hash, plugin count)
- `GET /plugins` — List loaded plugins and their endpoints
- `POST /convert/html-to-markdown` — HTML → Markdown (markdown-utils plugin)
- `POST /transcribe/audio` — Audio transcription via Whisper API (audio-transcription plugin)
- `POST /convert/webpage-to-ebook` — HTML → EPUB (webpage-to-ebook plugin)

Endpoints are **dynamically registered** from plugin `tool.yaml` files.

## Plugin System

**Discovery:** `plugin_loader.py` scans for `tool.yaml` in plugin directories at startup.

**Plugin structure:**
```
plugins/my-plugin/
├── tool.yaml          # Endpoint definitions (name, description, endpoints[])
├── handler.py         # Python script with run(input: dict) -> dict
└── requirements.txt   # Optional plugin-specific dependencies
```

**Two plugin sources:**
- `/app/plugins` — Builtin (in Docker image)
- `/app/user-plugins` — User-mounted volume (container restart to load)

**Builtin plugins:**

| Plugin | Endpoint | What it does |
|--------|----------|--------------|
| `markdown-utils` | `POST /convert/html-to-markdown` | markdownify-based HTML→MD |
| `audio-transcription` | `POST /transcribe/audio` | Base64 audio → Whisper API → text |
| `webpage-to-ebook` | `POST /convert/webpage-to-ebook` | HTML → EPUB (ebooklib) |

## Cross-Repo Interfaces

**Called by ancroo-backend:**
- `GET /plugins` — Backend auto-discovers plugins → syncs to Tool database
- `GET /health` — Health check
- `POST {endpoint}` — Plugin execution (via Tool executor)
- Integration code: `ancroo-backend/packages/backend/src/integrations/runner.py`

**Depends on ancroo-stack:**
- Docker network (`ai-network`)
- Whisper/Speaches service (for audio-transcription plugin)

## Development

```bash
pip install -r requirements.txt
cd app && uvicorn main:app --reload --port 8000
```

## Docker

```bash
docker build --build-arg BUILD_COMMIT=$(git rev-parse --short HEAD) -t ancroo-runner .
docker run -p 8510:8000 -v ./my-plugins:/app/user-plugins:ro ancroo-runner
```

## Stack Integration

```bash
./install-stack.sh ../ancroo-stack
```

Port mapping: 8510 (host) → 8000 (container).
