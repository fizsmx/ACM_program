"""Servidor HTTP local (stdlib): sirve la UI, expone la API y transmite el progreso por SSE."""
from __future__ import annotations

import json
import logging
import mimetypes
import os
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import paths
import runners
from llm import LlamaClient
from solver import Cancelled, Solver

log = logging.getLogger("server")


class State:
    def __init__(self, cfg: dict, runtime: dict):
        self.cfg = cfg
        self.runtime = runtime
        self.client = LlamaClient(f"http://127.0.0.1:{runtime['port_llm']}", timeout=float(cfg["solve_timeout_seconds"]))
        self.solver = Solver(self.client, cfg, runtime)
        self.lock = threading.Lock()  # una resolución a la vez
        self.cancel = threading.Event()
        self.busy_phase = None


STATE: State | None = None


class Handler(BaseHTTPRequestHandler):
    server_version = "CodeSolver/0.1"

    def log_message(self, fmt, *args):  # silenciar el log por defecto
        log.debug("%s " + fmt, self.address_string(), *args)

    # ----------------------------------------------------------- helpers
    def _json(self, obj, status=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            return {}

    def _static(self, rel: str):
        rel = rel.split("?")[0]
        if rel in ("", "/"):
            rel = "/index.html"
        full = os.path.normpath(os.path.join(paths.WEB_DIR, rel.lstrip("/")))
        if not full.startswith(paths.WEB_DIR) or not os.path.isfile(full):
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

    def _sse(self, obj: dict):
        try:
            self.wfile.write(("data: " + json.dumps(obj, ensure_ascii=False) + "\n\n").encode("utf-8"))
            self.wfile.flush()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            # el navegador cerró la pestaña/conexión: no seguir gastando tokens
            STATE.cancel.set()
            log.info("cliente SSE desconectado; cancelando la generación")
            raise Cancelled()

    # ----------------------------------------------------------- routes
    def do_GET(self):
        st = STATE
        if self.path.startswith("/api/status"):
            ok, _ = st.client.health()
            return self._json({"llm_ok": ok, "busy": st.busy_phase, "runtime": st.runtime,
                               "config": {k: st.cfg[k] for k in ("language", "max_repair_attempts", "test_timeout_seconds")}})
        if self.path.startswith("/api/"):
            return self._json({"error": "not found"}, 404)
        return self._static(self.path)

    def do_POST(self):
        st = STATE
        body = self._body()
        try:
            if self.path == "/api/solve":
                return self._solve(body)
            if self.path == "/api/run":
                return self._run(body)
            if self.path == "/api/cancel":
                st.cancel.set()
                return self._json({"ok": True})
            if self.path == "/api/reset":
                st.cancel.set()
                n = runners.cleanup_workspace()
                return self._json({"ok": True, "removed": n})
            return self._json({"error": "not found"}, 404)
        except Exception as e:  # noqa
            log.error("POST %s failed: %s\n%s", self.path, e, traceback.format_exc())
            try:
                return self._json({"error": str(e)}, 500)
            except Exception:
                pass

    def _solve(self, body: dict):
        st = STATE
        problem = (body.get("problem") or "").strip()
        language = body.get("language") or st.cfg["language"]
        tests = body.get("tests")
        statement_lang = body.get("statement_lang") or "auto"
        use_reasoning = bool(body.get("reasoning", True)) and bool(st.cfg["reasoning"]["enabled"])
        if not problem:
            return self._json({"error": "empty problem"}, 400)
        if language not in runners.LANGS:
            return self._json({"error": "unsupported language"}, 400)
        ok, why = st.client.health()
        if not ok:
            return self._json({"error": f"LLM engine not responding ({why}). Restart CodeSolver.bat."}, 503)
        if not st.lock.acquire(blocking=False):
            return self._json({"error": "busy: another solve is running (cancel it first)"}, 409)
        try:
            st.cancel = threading.Event()
            st.busy_phase = "solve"
            self._sse_start()
            emit = self._sse
            try:
                result = st.solver.solve(problem, language, emit, st.cancel,
                                         tests=tests if isinstance(tests, list) and tests else None,
                                         use_reasoning=use_reasoning, statement_lang=statement_lang)
                emit({"type": "done", **result})
            except Cancelled:
                try:
                    emit({"type": "cancelled"})
                except Cancelled:
                    pass  # el cliente ya no está
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                st.cancel.set()
            except Exception as e:  # noqa
                log.error("solve failed: %s\n%s", e, traceback.format_exc())
                emit({"type": "error", "message": str(e)})
        finally:
            st.busy_phase = None
            st.lock.release()

    def _run(self, body: dict):
        st = STATE
        code, language = body.get("code") or "", body.get("language") or "python"
        stdin_text = body.get("input") or ""
        if language not in runners.LANGS or not code.strip():
            return self._json({"error": "bad request"}, 400)
        d = runners.new_run_dir()
        path = runners.write_solution(language, code, d)
        chk = runners.syntax_check(language, path)
        if chk["status"] == "COMPILE_ERROR":
            return self._json(chk)
        return self._json(runners.execute(language, path, stdin_text, float(st.cfg["test_timeout_seconds"])))


def serve(cfg: dict, runtime: dict, port: int) -> ThreadingHTTPServer:
    global STATE
    STATE = State(cfg, runtime)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    return httpd
