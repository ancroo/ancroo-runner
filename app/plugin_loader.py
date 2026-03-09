"""Plugin loader — scans directories for tool.yaml files and registers FastAPI endpoints."""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, Request

logger = logging.getLogger(__name__)


def _load_module(script_path: Path):
    """Import a Python script as a module."""
    module_name = f"plugin_{script_path.parent.name}_{script_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _register_endpoint(app: FastAPI, path: str, script_path: Path, description: str):
    """Register a single plugin endpoint."""
    module = _load_module(script_path)

    if not hasattr(module, "run"):
        raise AttributeError(f"{script_path} has no 'run' function")

    run_fn = module.run

    async def endpoint(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        try:
            result = run_fn(body)
        except Exception as exc:
            logger.exception("Plugin error in %s", path)
            raise HTTPException(status_code=500, detail=str(exc))
        return result

    # Set a unique operation_id for OpenAPI
    operation_id = path.strip("/").replace("/", "_")
    app.post(path, summary=description, operation_id=operation_id)(endpoint)


def load_plugins(app: FastAPI, plugin_dirs: list[Path]) -> list[dict[str, Any]]:
    """Scan plugin directories and register endpoints.

    Returns a list of loaded plugin metadata for the /plugins info endpoint.
    """
    loaded: list[dict[str, Any]] = []

    for plugin_dir in plugin_dirs:
        if not plugin_dir.is_dir():
            continue

        for tool_yaml in sorted(plugin_dir.glob("*/tool.yaml")):
            plugin_path = tool_yaml.parent
            plugin_name = plugin_path.name

            try:
                config = yaml.safe_load(tool_yaml.read_text())
            except Exception:
                logger.exception("Failed to parse %s", tool_yaml)
                continue

            name = config.get("name", plugin_name)
            description = config.get("description", "")
            endpoints = config.get("endpoints", [])
            registered = []

            for ep in endpoints:
                ep_path = ep.get("path")
                ep_script = ep.get("script")
                ep_desc = ep.get("description", "")

                if not ep_path or not ep_script:
                    logger.warning("Skipping endpoint in %s: missing path or script", plugin_name)
                    continue

                script_path = plugin_path / ep_script

                if not script_path.is_file():
                    logger.warning("Script not found: %s", script_path)
                    continue

                try:
                    _register_endpoint(app, ep_path, script_path, ep_desc)
                    registered.append({"path": ep_path, "description": ep_desc})
                    logger.info("Registered endpoint: POST %s (%s)", ep_path, plugin_name)
                except Exception:
                    logger.exception("Failed to register %s from %s", ep_path, plugin_name)

            if registered:
                loaded.append({
                    "name": name,
                    "description": description,
                    "source": str(plugin_path),
                    "endpoints": registered,
                })

    return loaded
