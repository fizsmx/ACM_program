"""Ejecución del código generado con los runtimes incluidos, timeout y carpeta temporal por ejecución."""
from __future__ import annotations

import os
import signal
import shutil
import subprocess
import time
import uuid

import paths

LANGS = {
    "python": {"ext": "py", "label": "Python"},
    "javascript": {"ext": "js", "label": "JavaScript"},
}

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _popen_kwargs() -> dict:
    """En Windows oculta la ventana; en Linux crea un grupo de procesos nuevo para poder matar el árbol."""
    if paths.IS_WIN:
        return {"creationflags": _NO_WINDOW}
    return {"start_new_session": True}


def _env() -> dict:
    env = {
        "PATH": os.path.dirname(paths.NODE_EXE) + os.pathsep + os.path.dirname(paths.PYTHON_EXE)
                + (os.pathsep + "/usr/bin:/bin" if not paths.IS_WIN else ""),
        "TEMP": paths.WORKSPACE_DIR, "TMP": paths.WORKSPACE_DIR, "TMPDIR": paths.WORKSPACE_DIR,
        "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
        "NODE_OPTIONS": "--max-old-space-size=1024",
    }
    if paths.IS_WIN:
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
    else:
        env["HOME"] = os.environ.get("HOME", paths.WORKSPACE_DIR)
        env["LANG"] = "C.UTF-8"
        # los binarios portables de Linux traen sus .so junto al ejecutable
        env["LD_LIBRARY_PATH"] = os.path.dirname(paths.NODE_EXE) + os.pathsep + os.path.dirname(paths.PYTHON_EXE)
    return env


def _kill_tree(proc: subprocess.Popen) -> None:
    if paths.IS_WIN:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, creationflags=_NO_WINDOW)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                proc.kill()
            except Exception:
                pass


def _run(cmd: list[str], cwd: str, stdin_text: str, timeout: float) -> dict:
    t0 = time.time()
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd, env=_env(), text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            **_popen_kwargs(),
        )
    except OSError as e:
        return {"status": "INTERNAL_ERROR", "stdout": "", "stderr": f"cannot start runtime: {e}", "time_ms": 0, "exit_code": -1}
    try:
        out, err = proc.communicate(stdin_text, timeout=timeout)
        ms = int((time.time() - t0) * 1000)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=3)
        except Exception:
            out, err = "", ""
        return {"status": "TIME_LIMIT", "stdout": out[-4000:], "stderr": err[-2000:],
                "time_ms": int(timeout * 1000), "exit_code": -9}
    return {
        "status": "OK" if proc.returncode == 0 else "RUNTIME_ERROR",
        "stdout": out[-20000:], "stderr": err[-4000:], "time_ms": ms, "exit_code": proc.returncode,
    }


def new_run_dir() -> str:
    d = os.path.join(paths.WORKSPACE_DIR, "run_" + uuid.uuid4().hex[:10])
    os.makedirs(d, exist_ok=True)
    return d


def write_solution(language: str, code: str, run_dir: str) -> str:
    path = os.path.join(run_dir, "solution." + LANGS[language]["ext"])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(code if code.endswith("\n") else code + "\n")
    return path


def syntax_check(language: str, path: str) -> dict:
    """Devuelve RunResult con status OK o COMPILE_ERROR."""
    if language == "python":
        cmd = [paths.PYTHON_EXE, "-X", "utf8", "-c",
               "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read(),sys.argv[1])", path]
    else:
        cmd = [paths.NODE_EXE, "--check", path]
    r = _run(cmd, os.path.dirname(path), "", 20)
    if r["status"] != "OK":
        r["status"] = "COMPILE_ERROR"
    return r


def execute(language: str, path: str, stdin_text: str, timeout: float) -> dict:
    if language == "python":
        cmd = [paths.PYTHON_EXE, "-X", "utf8", "-I", path]
    else:
        cmd = [paths.NODE_EXE, "--stack-size=65500", path]
    return _run(cmd, os.path.dirname(path), stdin_text, timeout)


def cleanup_workspace(keep_state: bool = True) -> int:
    n = 0
    if not os.path.isdir(paths.WORKSPACE_DIR):
        return 0
    for name in os.listdir(paths.WORKSPACE_DIR):
        full = os.path.join(paths.WORKSPACE_DIR, name)
        if name.startswith("run_") and os.path.isdir(full):
            shutil.rmtree(full, ignore_errors=True)
            n += 1
    return n
