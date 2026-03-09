"""ancroo-runner — Script runner with plugin system for deterministic transformations."""

import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI

from app.plugin_loader import load_plugins

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = FastAPI(title="ancroo-runner", version="0.1.0")

# Build-time commit hash (written by Dockerfile ARG, fallback to git in dev)
_commit_file = Path("/app/BUILD_COMMIT")
if _commit_file.exists() and _commit_file.read_text().strip() not in ("", "dev"):
    BUILD_COMMIT = _commit_file.read_text().strip()
else:
    try:
        BUILD_COMMIT = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        BUILD_COMMIT = "dev"

# Load plugins from builtin and user directories
BUILTIN_PLUGINS = Path("/app/plugins")
USER_PLUGINS = Path("/app/user-plugins")

loaded_plugins = load_plugins(app, [BUILTIN_PLUGINS, USER_PLUGINS])


@app.get("/health")
async def health():
    return {"status": "ok", "commit": BUILD_COMMIT, "plugins_loaded": len(loaded_plugins)}


@app.get("/plugins")
async def list_plugins():
    return {"plugins": loaded_plugins}
