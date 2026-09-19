"""Tests de robustez sin LLM real. Ejecutar:  runtime\\python\\python.exe -X utf8 tests\\test_robustness.py"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

import launcher  # noqa: E402
import paths  # noqa: E402
import runners  # noqa: E402
import server  # noqa: E402
from llm import LlamaClient  # noqa: E402
from solver import Cancelled, Solver, extract_code  # noqa: E402

PY = paths.PYTHON_EXE
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _cfg(**over):
    cfg = paths.load_config()
    cfg.update(over)
    return cfg


def _pid_alive(pid: int) -> bool:
    return launcher.process_name(pid) != ""


class TestChooseProfile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cs_models_")
        self.orig = paths.MODELS_DIR
        paths.MODELS_DIR = self.tmp
        self.cfg = {"profiles": {"HIGH": {"min_free_ram_gb": 10, "model": "big.gguf"},
                                 "MEDIUM": {"min_free_ram_gb": 5, "model": "mid.gguf"},
                                 "LOW": {"min_free_ram_gb": 3, "model": "small.gguf"}}, "force_profile": None}

    def tearDown(self):
        paths.MODELS_DIR = self.orig

    def _fake(self, name, magic=b"GGUF", mb=120):
        with open(os.path.join(self.tmp, name), "wb") as f:
            f.write(magic + b"\0" * (mb * 2**20 - len(magic)))

    def test_no_models(self):
        with self.assertRaises(RuntimeError) as cm:
            launcher.choose_profile(self.cfg, {"ram_free_gb": 32})
        self.assertIn("falta models/big.gguf", str(cm.exception))
        self.assertIn("falta models/small.gguf", str(cm.exception))

    def test_ram_insufficient_falls_back(self):
        self._fake("big.gguf"); self._fake("mid.gguf")
        name, path = launcher.choose_profile(self.cfg, {"ram_free_gb": 6})
        self.assertEqual(name, "MEDIUM")
        self.assertTrue(path.endswith("mid.gguf"))

    def test_ram_insufficient_for_all(self):
        self._fake("small.gguf")
        with self.assertRaises(RuntimeError) as cm:
            launcher.choose_profile(self.cfg, {"ram_free_gb": 1})
        self.assertIn("necesita 3 GB libres, hay 1", str(cm.exception))

    def test_corrupt_model_skipped(self):
        self._fake("big.gguf", magic=b"JUNK"); self._fake("mid.gguf")
        name, _ = launcher.choose_profile(self.cfg, {"ram_free_gb": 32})
        self.assertEqual(name, "MEDIUM")
        ok, why = launcher.check_gguf(os.path.join(self.tmp, "big.gguf"))
        self.assertFalse(ok); self.assertIn("GGUF", why)

    def test_incomplete_model_detected(self):
        self._fake("mid.gguf", mb=1)
        ok, why = launcher.check_gguf(os.path.join(self.tmp, "mid.gguf"))
        self.assertFalse(ok); self.assertIn("incompleta", why)

    def test_force_profile_missing(self):
        self.cfg["force_profile"] = "LOW"
        with self.assertRaises(RuntimeError):
            launcher.choose_profile(self.cfg, {"ram_free_gb": 32})


class TestPorts(unittest.TestCase):
    def test_free_port_skips_busy(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1)
        busy = s.getsockname()[1]
        try:
            self.assertNotEqual(launcher.free_port(busy), busy)
            self.assertEqual(launcher.free_port(busy + 1), busy + 1)
        finally:
            s.close()


class TestProcesses(unittest.TestCase):
    def test_wait_health_process_dies(self):
        proc = subprocess.Popen([PY, "-c", "import sys; sys.exit(3)"], creationflags=_NO_WINDOW)
        client = LlamaClient("http://127.0.0.1:1")  # puerto sin servidor
        t0 = time.time()
        self.assertFalse(launcher.wait_health(client, proc, timeout=20, label="test"))
        self.assertLess(time.time() - t0, 10)

    def test_kill_stale_llm_does_not_kill_other_process(self):
        proc = subprocess.Popen([PY, "-c", "import time; time.sleep(30)"], creationflags=_NO_WINDOW)
        try:
            os.makedirs(paths.WORKSPACE_DIR, exist_ok=True)
            with open(paths.LLM_PID_FILE, "w") as f:
                f.write(str(proc.pid))
            self.assertFalse(launcher.kill_stale_llm())
            time.sleep(0.5)
            self.assertIsNone(proc.poll(), "mató un proceso que no era llama-server")
            self.assertFalse(os.path.exists(paths.LLM_PID_FILE))
        finally:
            proc.kill()
            proc.wait()

    def test_process_name(self):
        proc = subprocess.Popen([PY, "-c", "import time; time.sleep(10)"], creationflags=_NO_WINDOW)
        try:
            self.assertEqual(launcher.process_name(proc.pid), "python.exe")
        finally:
            proc.kill()
        proc.wait()
        time.sleep(0.3)
        self.assertEqual(launcher.process_name(proc.pid), "")

    def test_rotate_logs(self):
        tmp = tempfile.mkdtemp(prefix="cs_logs_")
        orig = paths.LOGS_DIR
        paths.LOGS_DIR = tmp
        try:
            for i in range(20):
                open(os.path.join(tmp, f"session_2026_{i:02d}.log"), "w").close()
            open(os.path.join(tmp, "llama_cpu.log"), "w").close()
            launcher.rotate_logs(15)
            left = sorted(os.listdir(tmp))
            self.assertEqual(len([f for f in left if f.startswith("session_")]), 15)
            self.assertIn("llama_cpu.log", left)
            self.assertNotIn("session_2026_00.log", left)
        finally:
            paths.LOGS_DIR = orig


class TestRunnerTimeout(unittest.TestCase):
    def test_time_limit_kills_child_tree(self):
        code = ("import subprocess, sys, time\n"
                "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                "print(p.pid, flush=True)\n"
                "time.sleep(60)\n")
        d = runners.new_run_dir()
        path = runners.write_solution("python", code, d)
        r = runners.execute("python", path, "", timeout=2)
        self.assertEqual(r["status"], "TIME_LIMIT")
        child = int(r["stdout"].split()[0])
        time.sleep(1)
        self.assertFalse(_pid_alive(child), f"el proceso hijo {child} sigue vivo tras TIME_LIMIT")

    def test_reads_all_stdin_then_eof(self):
        code = "import sys\nd = sys.stdin.read()\nprint(len(d))\n"
        d = runners.new_run_dir()
        path = runners.write_solution("python", code, d)
        r = runners.execute("python", path, "abc\n", timeout=5)
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["stdout"].strip(), "4")

    def test_huge_stdout_truncated(self):
        code = "import sys\nsys.stdout.write('x' * 200000)\n"
        d = runners.new_run_dir()
        path = runners.write_solution("python", code, d)
        r = runners.execute("python", path, "", timeout=5)
        self.assertEqual(r["status"], "OK")
        self.assertLessEqual(len(r["stdout"]), 20000)

    @classmethod
    def tearDownClass(cls):
        runners.cleanup_workspace()


class FakeLLM(LlamaClient):
    """Emite tokens lentamente y respeta cancel; sirve para probar cancelación y timeout."""

    def __init__(self, tokens=None, delay=0.05, forever=False):
        super().__init__("http://127.0.0.1:1")
        self.tokens = tokens or ["## Analysis\n- x\n## Code\n```python\n", "print(1)\n", "```\n"]
        self.delay, self.forever = delay, forever

    def chat(self, messages, *, cancel=None, **kw):
        self.last_timings = None
        i = 0
        while True:
            for t in self.tokens:
                if cancel is not None and cancel.is_set():
                    return
                time.sleep(self.delay)
                yield "content", t
            i += 1
            if not self.forever:
                return


class TestSolverCancel(unittest.TestCase):
    def test_extract_code_none(self):
        self.assertIsNone(extract_code("no code", "python"))

    def test_cancel_stops_quickly(self):
        cfg = _cfg(solve_timeout_seconds=600)
        s = Solver(FakeLLM(delay=0.05, forever=True), cfg, {"reasoning_budget": 0})
        cancel = threading.Event()
        events = []
        threading.Timer(0.4, cancel.set).start()
        t0 = time.time()
        with self.assertRaises(Cancelled):
            s.solve("Input\n1\nOutput\n1\n", "python", events.append, cancel,
                    tests=[{"input": "1\n", "expected": "1\n"}], use_reasoning=False)
        self.assertLess(time.time() - t0, 3)

    def test_solve_timeout_inside_generation(self):
        cfg = _cfg(solve_timeout_seconds=1)
        s = Solver(FakeLLM(delay=0.05, forever=True), cfg, {"reasoning_budget": 0})
        cancel = threading.Event()
        events = []
        t0 = time.time()
        res = s.solve("problem", "python", events.append, cancel, tests=[{"input": "1\n", "expected": "1\n"}],
                      use_reasoning=False)
        self.assertEqual(res["status"], "TIMEOUT")
        self.assertLess(time.time() - t0, 4)
        self.assertTrue(any(e["type"] == "status" and "time limit" in e["text"].lower() for e in events))

    def test_full_fake_solve_passes(self):
        cfg = _cfg()
        s = Solver(FakeLLM(delay=0.0), cfg, {"reasoning_budget": 0})
        res = s.solve("p", "python", lambda e: None, threading.Event(),
                      tests=[{"input": "\n", "expected": "1\n"}], use_reasoning=False)
        self.assertEqual(res["status"], "PASS")
        runners.cleanup_workspace()


class TestServerWithoutLLM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = _cfg()
        cls.port = launcher.free_port(18900)
        runtime = {"port_llm": 1, "profile": "TEST", "model": "none", "backend": "none", "gen_tps": 0,
                   "prompt_tps": 0, "reasoning_budget": 0}
        cls.httpd = server.serve(cfg, runtime, cls.port)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _post(self, path, body):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_solve_returns_503_when_llm_down(self):
        code, body = self._post("/api/solve", {"problem": "x", "language": "python"})
        self.assertEqual(code, 503)
        self.assertIn("LLM engine not responding", body["error"])

    def test_status_reports_llm_down(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/status", timeout=10) as r:
            self.assertFalse(json.loads(r.read().decode())["llm_ok"])

    def test_run_still_works_without_llm(self):
        code, body = self._post("/api/run", {"code": "print(2+2)", "language": "python", "input": ""})
        self.assertEqual(code, 200)
        self.assertEqual(body["stdout"].strip(), "4")

    def test_bad_language(self):
        code, _ = self._post("/api/run", {"code": "x", "language": "cobol", "input": ""})
        self.assertEqual(code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=1)
