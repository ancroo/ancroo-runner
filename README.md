# Ancroo Runner

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status: Beta](https://img.shields.io/badge/Status-Beta-yellow.svg)]()

Deterministic script runner for the [Ancroo](https://github.com/ancroo/ancroo) ecosystem. Runs user-extensible plugins that transform data — no LLM required.

> **Phase 0 (Beta)** — The runner works end-to-end, but the stack it connects to runs without encryption or authentication by default. Intended for local/trusted networks only. See the [Ancroo Roadmap](https://github.com/ancroo/ancroo/blob/main/ROADMAP.md) for the security path forward.

## How It Works

Ancroo Runner is a lightweight FastAPI service with a **plugin system**. Each plugin is a directory with a config file and Python scripts. The runner loads plugins at startup and exposes them as HTTP endpoints.

```
Browser Extension → Ancroo Backend → Ancroo Runner → Plugin Script
                                                    ↓
                                              Result (JSON)
```

The backend calls the runner via the existing `custom` workflow type — no special integration needed.

## Plugins

Plugins live in two locations:

| Location | Purpose |
|----------|---------|
| `plugins/` | Builtin plugins, shipped with the image |
| User-mounted volume | User plugins, added without rebuilding |

### Plugin Structure

```
my-plugin/
├── tool.yaml              # Endpoint definitions
├── requirements.txt       # Python dependencies (optional)
├── my_script.py           # def run(input: dict) -> dict
└── another_script.py      # Additional scripts (optional)
```

### tool.yaml

```yaml
name: my-plugin
description: What this plugin does
endpoints:
  - path: /convert/something
    script: my_script.py
    description: Convert something to something else
```

### Script Convention

Every script must export a `run` function:

```python
def run(input: dict) -> dict:
    # Process input
    return {"result": "output text"}
```

- **Input:** JSON body from the HTTP request
- **Output:** Dict with `"result"` key (matches the `$.result` response mapping convention)

## Builtin Plugins

### markdown-utils

| Endpoint | Description |
|----------|-------------|
| `POST /convert/html-to-markdown` | Convert HTML to clean Markdown |

**Input:** `{"html": "<b>Hello</b> <a href='https://example.com'>World</a>"}`
**Output:** `{"result": "**Hello** [World](https://example.com)"}`

### audio-transcription

| Endpoint | Description |
|----------|-------------|
| `POST /transcribe/audio` | Transcribe audio with silence-based splitting via Whisper API |

Splits long audio files at speech pauses, transcribes each chunk via a Whisper-compatible API (e.g. [Speaches](https://github.com/speaches-ai/speaches)), and reassembles the text. Requires the `speaches` or `whisper-rocm` stack module.

**Input:**
```json
{
  "audio_base64": "<base64-encoded audio (WAV, MP3, FLAC, OGG)>",
  "language": "de",
  "model": "Systran/faster-whisper-large-v3"
}
```

**Output:**
```json
{
  "result": "Transcribed text...",
  "duration_s": 45.2,
  "chunks_count": 3
}
```

**Environment:** Set `WHISPER_BASE_URL` to override the default Whisper API endpoint (`http://speaches:8000/v1/audio/transcriptions`).


## Installation

### As Ancroo Stack Module

If the runner repo is cloned alongside the stack (e.g. via the [meta-installer](https://github.com/ancroo/ancroo)):

```bash
cd ancroo-runner
./install-stack.sh ../ancroo-stack
```

This copies the module files into the stack and optionally enables the module. For dev builds from source, set `ANCROO_LOCAL_BUILD=y`:

```bash
ANCROO_LOCAL_BUILD=y ./install-stack.sh ../ancroo-stack
```

Alternatively, if the module files are already in the stack:

```bash
cd ancroo-stack
./module.sh enable ancroo-runner
```

### Standalone (Docker)

```bash
docker build --build-arg BUILD_COMMIT=$(git rev-parse --short HEAD) -t ancroo-runner .
docker run -p 8510:8000 -v ./my-plugins:/app/user-plugins:ro ancroo-runner
```

### Adding User Plugins

1. Create a plugin directory with `tool.yaml` and scripts
2. Place it in the user plugins volume (default: `data/ancroo-runner/plugins/`)
3. Restart the container

```bash
docker compose restart ancroo-runner
```

## Workflow Integration

The runner integrates with [Ancroo Backend](https://github.com/ancroo/ancroo-backend) via the `custom` workflow type. Example workflow definitions are in the `workflows/` directory. To use them, import them via the backend admin panel or API.

**Important:** The runner listens on port **8000** inside the Docker network. The host port (default 8510) is only for external access. When creating backend workflows that call the runner, use the internal URL:

```
http://ancroo-runner:8000/convert/html-to-markdown
```

See `workflows/html-to-markdown.json` for a complete example that maps a browser text selection to the runner's `/convert/html-to-markdown` endpoint.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (includes commit hash and plugin count) |
| `GET` | `/plugins` | List loaded plugins and their endpoints |
| `POST` | `<plugin path>` | Execute a plugin endpoint |

## Contributing

Contributions are welcome! Feel free to open an [issue](https://github.com/ancroo/ancroo-runner/issues) or submit a pull request.

## Author

**Stefan Schmidbauer** — [GitHub](https://github.com/Stefan-Schmidbauer)

## Acknowledgments

This project is built with the following open-source software:

| Project | Purpose | License |
|---------|---------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | Web framework | MIT |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server | BSD-3-Clause |
| [PyYAML](https://pyyaml.org/) | Plugin config parsing | MIT |

Builtin plugins use additional libraries:

| Library | Plugin | License |
|---------|--------|---------|
| [markdownify](https://github.com/matthewwithanm/python-markdownify) | markdown-utils | MIT |
| [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) | webpage-to-ebook | MIT |
| [lxml](https://lxml.de/) | webpage-to-ebook | BSD-3-Clause |
| [ebooklib](https://github.com/aerkalov/ebooklib) | webpage-to-ebook | AGPL-3.0 |
| [pydub](https://github.com/jiaaro/pydub) | audio-transcription | MIT |
| [Requests](https://requests.readthedocs.io/) | audio-transcription | Apache-2.0 |

> **Note:** The `webpage-to-ebook` plugin depends on ebooklib, which is licensed under AGPL-3.0. This dependency is isolated to the plugin and installed at container startup only when the plugin is loaded.

## License

MIT — see [LICENSE](LICENSE). The Ancroo name is not covered by this license and remains the property of the author.

---

Built with the help of AI ([Claude](https://claude.ai) by Anthropic).
