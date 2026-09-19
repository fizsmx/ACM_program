"""Rutas portables: todo se resuelve desde la carpeta raíz de la aplicación (APP_ROOT).

Nunca se usan rutas absolutas fijas ni letras de unidad: el USB puede montarse en D:, E:, F:...
"""
from __future__ import annotations

import json
import os
import sys

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IS_WIN = sys.platform.startswith("win")
EXE = ".exe" if IS_WIN else ""


def p(*parts: str) -> str:
    return os.path.join(APP_ROOT, *parts)


# Los binarios de Windows y de Linux conviven en el mismo USB; se elige según el sistema.
if IS_WIN:
    PYTHON_EXE = p("runtime", "python", "python.exe")
    NODE_EXE = p("runtime", "node", "node.exe")
else:
    PYTHON_EXE = p("runtime", "python-linux", "bin", "python3")
    NODE_EXE = p("runtime", "node-linux", "bin", "node")

MODELS_DIR = p("models")
WORKSPACE_DIR = p("workspace")
LOGS_DIR = p("logs")
WEB_DIR = p("web")
PROMPTS_DIR = p("prompts")
CONFIG_FILE = p("config", "config.json")
RUNTIME_STATE_FILE = p("workspace", "runtime.json")
LLM_PID_FILE = p("workspace", "llama.pid")


def llama_dir(kind: str) -> str:
    """kind: 'cpu' | 'vulkan'"""
    return p("bin", "llama", kind if IS_WIN else "linux-" + kind)


def llama_server_exe(kind: str) -> str:
    return os.path.join(llama_dir(kind), "llama-server" + EXE)


def ensure_dirs() -> None:
    for d in (WORKSPACE_DIR, LOGS_DIR):
        os.makedirs(d, exist_ok=True)


def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def read_prompt(name: str) -> str:
    with open(os.path.join(PROMPTS_DIR, name), "r", encoding="utf-8") as f:
        return f.read()
