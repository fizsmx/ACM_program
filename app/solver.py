"""Orquestación: extraer ejemplos → generar → validar sintaxis → ejecutar → comparar → reparar → repensar."""
from __future__ import annotations

import re
import threading
import time
from typing import Callable

import compare
import examples as ex
import paths
import runners
from llm import LlamaClient, LLMError

Emit = Callable[[dict], None]

_FENCE = {"python": "python", "javascript": "javascript"}
_LABEL = {"python": "Python 3", "javascript": "JavaScript (Node.js)"}


class Cancelled(Exception):
    pass


def extract_code(text: str, language: str) -> str | None:
    """Toma el último bloque ``` del lenguaje; si no hay etiquetado, el último bloque cualquiera."""
    blocks = re.findall(r"```([a-zA-Z0-9_+-]*)[ \t]*\n(.*?)```", text, re.DOTALL)
    if not blocks:
        return None
    want = {"python": ("python", "py", "python3"), "javascript": ("javascript", "js", "node")}[language]
    tagged = [b for tag, b in blocks if tag.lower() in want]
    code = (tagged or [b for _, b in blocks])[-1]
    return code.strip("\n") + "\n"


def _analysis_text(content: str) -> str:
    m = re.search(r"## (?:Analysis|Diagnosis)\s*(.*?)(?=\n## |```|$)", content, re.DOTALL)
    return m.group(1).strip() if m else ""


class Solver:
    def __init__(self, client: LlamaClient, cfg: dict, runtime: dict):
        self.client = client
        self.cfg = cfg
        self.runtime = runtime  # {'gen_tps':..., 'reasoning_budget':...}

    # ----------------------------------------------------------------- helpers
    def _prompt(self, name: str, language: str, **kw) -> str:
        txt = paths.read_prompt(name)
        rules = paths.read_prompt(f"rules_{language}.txt")
        rep = {"LANGUAGE_LABEL": _LABEL[language], "FENCE": _FENCE[language], "LANGUAGE_RULES": rules, **kw}
        for k, v in rep.items():
            txt = txt.replace("{" + k + "}", v)
        return txt

    def _llm(self, messages, emit: Emit, cancel: threading.Event, *, temperature: float,
             reasoning: bool, phase: str) -> str:
        s = self.cfg["sampling"]
        budget = self.runtime.get("reasoning_budget", 1024) if reasoning else 0
        emit({"type": "phase", "name": phase, "reasoning_budget": budget})

        def on_token(channel, text):
            if cancel.is_set():
                raise Cancelled()
            emit({"type": "token", "channel": channel, "text": text})

        try:
            reasoning_txt, content, secs = self.client.complete_text(
                messages, on_token=on_token, temperature=temperature, top_p=s["top_p"], top_k=s["top_k"],
                max_tokens=int(s["max_answer_tokens"]) + max(0, budget), reasoning_budget=budget if budget > 0 else 0,
                cancel=cancel)
        except LLMError as e:
            raise RuntimeError(str(e))
        if cancel.is_set():
            raise Cancelled()
        t = self.client.last_timings or {}
        emit({"type": "llm_done", "phase": phase, "seconds": round(secs, 1),
              "reasoning_chars": len(reasoning_txt), "content_chars": len(content),
              "gen_tps": t.get("predicted_per_second"), "prompt_tps": t.get("prompt_per_second")})
        return content

    def _get_tests(self, problem: str, emit: Emit, cancel: threading.Event) -> list[dict]:
        tests = ex.extract_examples(problem)
        source = "regex"
        if not tests:
            emit({"type": "status", "text": "No samples found by parser; asking the model to extract them..."})
            msgs = [{"role": "user", "content": self._prompt("extract_examples.txt", "python", PROBLEM=problem)}]
            content = self._llm(msgs, emit, cancel, temperature=0.0, reasoning=False, phase="extract_examples")
            tests = ex.parse_llm_examples(content)
            source = "llm"
        emit({"type": "examples", "source": source, "tests": tests})
        return tests

    def run_tests(self, language: str, code: str, tests: list[dict], emit: Emit, cancel: threading.Event) -> list[dict]:
        run_dir = runners.new_run_dir()
        path = runners.write_solution(language, code, run_dir)
        chk = runners.syntax_check(language, path)
        results = []
        if chk["status"] == "COMPILE_ERROR":
            r = {"index": 0, "status": "COMPILE_ERROR", "stdout": "", "stderr": chk["stderr"], "time_ms": 0,
                 "detail": "syntax error"}
            emit({"type": "test_result", **r})
            return [r]
        timeout = float(self.cfg["test_timeout_seconds"])
        for i, t in enumerate(tests):
            if cancel.is_set():
                raise Cancelled()
            rr = runners.execute(language, path, t["input"], timeout)
            if rr["status"] == "OK":
                ok, detail = compare.compare(t["expected"], rr["stdout"])
                status = "PASS" if ok else "WRONG_ANSWER"
            else:
                status, detail = rr["status"], rr["stderr"][-500:] or rr["status"]
            r = {"index": i, "status": status, "stdout": rr["stdout"][-3000:], "stderr": rr["stderr"][-1500:],
                 "time_ms": rr["time_ms"], "detail": detail}
            results.append(r)
            emit({"type": "test_result", **r})
        return results

    @staticmethod
    def _failure_report(tests: list[dict], results: list[dict]) -> str:
        parts = []
        for r in results:
            if r["status"] == "PASS":
                continue
            if r["status"] == "COMPILE_ERROR":
                parts.append(f"### Syntax/compile error\n```\n{r['stderr'][-1500:]}\n```")
                continue
            t = tests[r["index"]]
            parts.append(
                f"### Test {r['index'] + 1}: {r['status']}\nInput:\n```\n{t['input'].rstrip()}\n```\n"
                f"Expected output:\n```\n{t['expected'].rstrip()}\n```\n"
                f"Your output:\n```\n{(r['stdout'] or '').rstrip()[:1500]}\n```\n"
                + (f"stderr:\n```\n{r['stderr'][-1200:]}\n```\n" if r['stderr'] else "")
                + f"({r['detail']}, {r['time_ms']} ms)")
            if len(parts) >= 3:
                break
        return "\n\n".join(parts)

    # ----------------------------------------------------------------- main
    def solve(self, problem: str, language: str, emit: Emit, cancel: threading.Event,
              tests: list[dict] | None = None, use_reasoning: bool = True) -> dict:
        t_start = time.time()
        max_repairs = int(self.cfg["max_repair_attempts"])
        if tests is None:
            tests = self._get_tests(problem, emit, cancel)
        else:
            emit({"type": "examples", "source": "user", "tests": tests})

        system = self._prompt("solve.txt", language)
        user = f"Problem statement:\n\"\"\"\n{problem.strip()}\n\"\"\"\n\nSolve it in {_LABEL[language]}."
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        s = self.cfg["sampling"]

        attempts: list[dict] = []
        code, content = None, ""
        for attempt in range(max_repairs + 2):  # 0 = solve, 1..N = repair, N+1 = rethink
            if attempt == 0:
                phase, temp, reasoning = "solve", s["temperature"], use_reasoning
            elif attempt <= max_repairs:
                phase, temp, reasoning = f"repair {attempt}/{max_repairs}", s["repair_temperature"], use_reasoning
                messages.append({"role": "user", "content": self._prompt("repair.txt", language) + "\n\n" + report})
            else:
                phase, temp, reasoning = "rethink", s["temperature"], use_reasoning
                messages = [{"role": "system", "content": system}, {"role": "user", "content": user},
                            {"role": "assistant", "content": content},
                            {"role": "user", "content": self._prompt("rethink.txt", language) + "\n\n" + report}]
            content = self._llm(messages, emit, cancel, temperature=temp, reasoning=reasoning, phase=phase)
            code = extract_code(content, language)
            if code is None:
                emit({"type": "status", "text": "Model returned no code block; asking again strictly."})
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"You did not include a code block. Reply with ONLY the complete program inside a single ```{_FENCE[language]} block."})
                content = self._llm(messages, emit, cancel, temperature=temp, reasoning=False, phase=phase + " (retry)")
                code = extract_code(content, language)
                if code is None:
                    raise RuntimeError("The model did not return code.")
            messages.append({"role": "assistant", "content": content})
            emit({"type": "code", "attempt": attempt, "code": code, "analysis": _analysis_text(content)})

            if not tests:
                emit({"type": "status", "text": "No sample tests available: code is UNVERIFIED."})
                attempts.append({"attempt": attempt, "status": "UNVERIFIED"})
                return {"status": "UNVERIFIED", "code": code, "attempts": attempts, "seconds": round(time.time() - t_start, 1)}

            results = self.run_tests(language, code, tests, emit, cancel)
            passed = sum(1 for r in results if r["status"] == "PASS")
            attempts.append({"attempt": attempt, "phase": phase, "passed": passed, "total": len(tests)})
            emit({"type": "attempt_done", "attempt": attempt, "passed": passed, "total": len(tests)})
            if passed == len(tests):
                return {"status": "PASS", "code": code, "attempts": attempts, "seconds": round(time.time() - t_start, 1)}
            report = self._failure_report(tests, results)
            if time.time() - t_start > float(self.cfg["solve_timeout_seconds"]):
                emit({"type": "status", "text": "Solve time limit reached."})
                break
        return {"status": "FAIL", "code": code, "attempts": attempts, "seconds": round(time.time() - t_start, 1)}
