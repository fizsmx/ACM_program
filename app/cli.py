"""Modo consola de respaldo (por si el navegador está bloqueado). Requiere que el launcher esté corriendo.

Uso:  runtime\python\python.exe app\cli.py problema.txt [--lang python|javascript] [--out solucion.py] [--no-reasoning]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request

import paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("problem_file")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-reasoning", action="store_true")
    a = ap.parse_args()
    try:
        rt = json.load(open(paths.RUNTIME_STATE_FILE, encoding="utf-8"))
    except OSError:
        print("El launcher no está corriendo (no existe workspace/runtime.json). Ejecuta CodeSolver.bat primero.")
        return 2
    cfg = paths.load_config()
    lang = a.lang or cfg["language"]
    problem = open(a.problem_file, encoding="utf-8").read()
    body = json.dumps({"problem": problem, "language": lang, "reasoning": not a.no_reasoning}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{rt['port_web']}/api/solve", data=body,
                                 headers={"Content-Type": "application/json"})
    final_code = None
    with urllib.request.urlopen(req, timeout=3600) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            ev = json.loads(line[5:])
            t = ev["type"]
            if t == "token":
                sys.stdout.write(ev["text"] if ev["channel"] == "content" else "")
                sys.stdout.flush()
            elif t == "phase":
                print(f"\n=== {ev['name']} ===")
            elif t == "examples":
                print(f"[{len(ev['tests'])} sample tests, source={ev['source']}]")
            elif t == "test_result":
                print(f"  test {ev['index'] + 1}: {ev['status']} ({ev['time_ms']} ms) {ev.get('detail', '')}")
            elif t == "done":
                final_code = ev["code"]
                print(f"\n=== {ev['status']} in {ev['seconds']} s ===")
            elif t in ("error", "cancelled"):
                print(f"\n=== {t}: {ev.get('message', '')} ===")
    if final_code and a.out:
        open(a.out, "w", encoding="utf-8", newline="\n").write(final_code)
        print("guardado en", a.out)
    return 0 if final_code else 1


if __name__ == "__main__":
    sys.exit(main())
