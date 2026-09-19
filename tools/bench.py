"""Benchmark: resuelve todos los problemas de tests/problems/ contra el backend en marcha y resume resultados.

Uso: python tools/bench.py [--lang python|javascript] [--no-reasoning] [--filter p00] [--port 8765]
Requiere que CodeSolver.bat (launcher) esté corriendo. Escribe logs/bench_<fecha>.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def solve(port: int, problem: str, lang: str, reasoning: bool) -> dict:
    body = json.dumps({"problem": problem, "language": lang, "reasoning": reasoning}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/solve", data=body, headers={"Content-Type": "application/json"})
    out = {"status": "ERROR", "attempts": [], "seconds": 0, "llm": []}
    with urllib.request.urlopen(req, timeout=7200) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            ev = json.loads(line[5:])
            if ev["type"] == "llm_done":
                out["llm"].append({k: ev.get(k) for k in ("phase", "seconds", "reasoning_chars", "content_chars", "gen_tps")})
            elif ev["type"] == "examples":
                out["n_tests"] = len(ev["tests"])
            elif ev["type"] in ("done", "error", "cancelled"):
                out.update({k: v for k, v in ev.items() if k != "code"})
                out["status"] = ev.get("status", ev["type"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="python")
    ap.add_argument("--no-reasoning", action="store_true")
    ap.add_argument("--filter", default="")
    ap.add_argument("--port", type=int, default=None)
    a = ap.parse_args()
    port = a.port or json.load(open(os.path.join(ROOT, "workspace", "runtime.json"), encoding="utf-8"))["port_web"]
    files = sorted(f for f in glob.glob(os.path.join(ROOT, "tests", "problems", "*.md")) if a.filter in os.path.basename(f))
    results = []
    for f in files:
        name = os.path.basename(f)
        t0 = time.time()
        print(f"{name} ...", end="", flush=True)
        try:
            r = solve(port, open(f, encoding="utf-8").read(), a.lang, not a.no_reasoning)
        except Exception as e:
            r = {"status": "ERROR", "error": str(e), "attempts": []}
        r["name"], r["wall"] = name, round(time.time() - t0, 1)
        results.append(r)
        print(f" {r['status']} en {r['wall']}s, {len(r.get('attempts', []))} intento(s)")
    n = len(results)
    first = sum(1 for r in results if r["status"] == "PASS" and len(r["attempts"]) == 1)
    later = sum(1 for r in results if r["status"] == "PASS" and len(r["attempts"]) > 1)
    print(f"\nResumen ({a.lang}, reasoning={'off' if a.no_reasoning else 'on'}): {n} problemas | "
          f"PASS 1er intento {first} | PASS tras reparar {later} | FAIL {n - first - later} | "
          f"tiempo medio {sum(r['wall'] for r in results) / max(n, 1):.0f}s")
    out = os.path.join(ROOT, "logs", time.strftime("bench_%Y%m%d_%H%M%S.json"))
    json.dump({"lang": a.lang, "reasoning": not a.no_reasoning, "results": results}, open(out, "w", encoding="utf-8"), indent=2)
    print("detalle:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
