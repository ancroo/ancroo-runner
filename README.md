# Ancroo Runner

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)]()

Deterministic script runner for the [Ancroo](https://github.com/ancroo/ancroo) ecosystem. Runs user-extensible plugins that transform data — no LLM required.

> **Note:** This module is marked as **experimental**. The stack will ask for confirmation before enabling it.

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

The runner integrates with [Ancroo Backend](https://github.com/ancroo/ancroo-backend) via the `custom` workflow type. Example workflow definitions are in the `workflows/` directory. To use them, copy the JSON files into the backend's workflow import directory or import them via the admin API.

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

## License

MIT — see [LICENSE](LICENSE).

---

Built with the help of AI ([Claude](https://claude.ai) by Anthropic).
