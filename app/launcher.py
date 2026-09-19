"""Launcher: detecta hardware, elige modelo, arranca llama-server (Vulkan → CPU), espera /health,
mide velocidad, arranca el backend y abre el navegador. Ctrl+C o cerrar la ventana apaga todo."""
from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser

import hardware
import jobobject
import paths
import runners
from llm import LlamaClient

log = logging.getLogger("launcher")
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_JOB = jobobject.try_create()  # los hijos mueren si el launcher muere (cierre de ventana incluido)


# --------------------------------------------------------------------------- util
def setup_logging() -> str:
    paths.ensure_dirs()
    try:  # que los mensajes salgan al instante aunque stdout esté redirigido
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    logfile = os.path.join(paths.LOGS_DIR, time.strftime("session_%Y%m%d_%H%M%S.log"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler(sys.stdout)])
    return logfile


def free_port(start: int, tries: int = 6) -> int:
    for p in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    raise RuntimeError(f"No hay puertos libres entre {start} y {start + tries - 1}")


def kill_stale_llm() -> None:
    """Mata un llama-server de una sesión anterior que no se cerró (PID guardado)."""
    if not os.path.exists(paths.LLM_PID_FILE):
        return
    try:
        pid = int(open(paths.LLM_PID_FILE).read().strip())
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, creationflags=_NO_WINDOW).stdout
        if "llama-server" in out:
            log.warning("Cerrando llama-server huérfano (PID %s) de una sesión anterior", pid)
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, creationflags=_NO_WINDOW)
    except Exception as e:
        log.debug("kill_stale_llm: %s", e)
    finally:
        try:
            os.remove(paths.LLM_PID_FILE)
        except OSError:
            pass


# --------------------------------------------------------------------------- selección
def choose_profile(cfg: dict, hw: dict) -> tuple[str, str]:
    """Devuelve (nombre_perfil, ruta_modelo). Prefiere el perfil más alto cuyo modelo exista y quepa en RAM libre."""
    order = ["HIGH", "MEDIUM", "LOW"]
    forced = cfg.get("force_profile")
    if forced:
        order = [forced]
    available = {f for f in os.listdir(paths.MODELS_DIR)} if os.path.isdir(paths.MODELS_DIR) else set()
    reasons = []
    for name in order:
        prof = cfg["profiles"][name]
        model = prof["model"]
        if model not in available:
            reasons.append(f"{name}: falta models/{model}")
            continue
        if not forced and hw["ram_free_gb"] < prof["min_free_ram_gb"]:
            reasons.append(f"{name}: necesita {prof['min_free_ram_gb']} GB libres, hay {hw['ram_free_gb']}")
            continue
        return name, os.path.join(paths.MODELS_DIR, model)
    raise RuntimeError("Ningún perfil utilizable:\n  " + "\n  ".join(reasons))


def llama_args(exe: str, model: str, port: int, cfg: dict, hw: dict, gpu: bool, budget: int) -> list[str]:
    threads = cfg.get("threads") or hardware.recommended_threads(hw["logical_cpus"])
    r = cfg["reasoning"]
    args = [exe, "-m", model, "--host", "127.0.0.1", "--port", str(port),
            "-c", str(cfg["context_size"]), "-t", str(threads), "-np", "1",
            "--jinja", "--no-webui", "--reasoning-format", "deepseek", "--log-timestamps",
            "-ngl", str(cfg.get("gpu_layers", 99) if gpu else 0),
            # el presupuesto de pensamiento SOLO funciona como flag del servidor (no por petición)
            "--reasoning-budget", str(budget if r["enabled"] else 0)]
    if r["enabled"] and r.get("budget_message"):
        args += ["--reasoning-budget-message", r["budget_message"]]
    return args


def start_llama(cfg: dict, hw: dict, model: str, port: int, kind: str, budget: int) -> tuple[subprocess.Popen, str]:
    exe = paths.llama_server_exe(kind)
    if not os.path.exists(exe):
        raise RuntimeError(f"No existe {exe}")
    logfile = os.path.join(paths.LOGS_DIR, f"llama_{kind}.log")
    args = llama_args(exe, model, port, cfg, hw, gpu=(kind != "cpu"), budget=budget)
    log.info("Arrancando llama-server [%s]: %s", kind, " ".join(args[1:]))
    lf = open(logfile, "w", encoding="utf-8")
    proc = subprocess.Popen(args, cwd=paths.llama_dir(kind), stdout=lf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, creationflags=_NO_WINDOW)
    if _JOB is not None and not _JOB.assign(proc):
        log.warning("No se pudo asignar llama-server al Job Object; se usará el PID file como respaldo")
    with open(paths.LLM_PID_FILE, "w") as f:
        f.write(str(proc.pid))
    return proc, logfile


def wait_health(client: LlamaClient, proc: subprocess.Popen, timeout: float, label: str) -> bool:
    t0 = time.time()
    last = 0
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            log.error("llama-server [%s] terminó con código %s", label, proc.returncode)
            return False
        ok, _ = client.health()
        if ok:
            log.info("Modelo listo en %.0f s", time.time() - t0)
            return True
        if time.time() - last > 5:
            last = time.time()
            print(f"  cargando modelo... {int(time.time() - t0)} s", flush=True)
        time.sleep(1)
    log.error("Timeout esperando /health (%s s)", timeout)
    return False


def tail(path: str, n: int = 30) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return "".join(f.readlines()[-n:])
    except OSError:
        return ""


def stop(proc: subprocess.Popen | None) -> None:
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
    try:
        os.remove(paths.LLM_PID_FILE)
    except OSError:
        pass


def reasoning_budget(cfg: dict, gen_tps: float) -> int:
    r = cfg["reasoning"]
    if not r["enabled"]:
        return 0
    b = int(gen_tps * float(r["seconds_budget"]))
    return max(int(r["min_tokens"]), min(int(r["max_tokens"]), b))


def hw_signature(hw: dict, model: str, kind: str) -> str:
    return f"{hw['logical_cpus']}|{hw['ram_total_gb']}|{','.join(hw['gpus'])}|{os.path.basename(model)}|{kind}"


SPEED_CACHE = os.path.join(paths.LOGS_DIR, "speed_cache.json")


def cached_speed(sig: str) -> float | None:
    try:
        return json.load(open(SPEED_CACHE, encoding="utf-8")).get(sig)
    except Exception:
        return None


def save_speed(sig: str, tps: float) -> None:
    try:
        d = json.load(open(SPEED_CACHE, encoding="utf-8"))
    except Exception:
        d = {}
    d[sig] = tps
    json.dump(d, open(SPEED_CACHE, "w", encoding="utf-8"), indent=1)


# --------------------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="CodeSolver")
    ap.add_argument("--profile", help="forzar perfil HIGH/MEDIUM/LOW")
    ap.add_argument("--cpu", action="store_true", help="no usar GPU/Vulkan")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--port", type=int, help="puerto del backend")
    a = ap.parse_args(argv)

    logfile = setup_logging()
    print("=" * 64)
    print("  CodeSolver Offline  —  APP_ROOT =", paths.APP_ROOT)
    print("=" * 64)
    cfg = paths.load_config()
    if a.profile:
        cfg["force_profile"] = a.profile.upper()
    if a.cpu:
        cfg["prefer_gpu"] = False

    kill_stale_llm()
    runners.cleanup_workspace()

    hw = hardware.detect()
    log.info("Hardware: %s", json.dumps(hw))
    print(f"  RAM: {hw['ram_free_gb']} GB libres de {hw['ram_total_gb']} | CPUs lógicas: {hw['logical_cpus']} | "
          f"Vulkan: {'sí' if hw['vulkan'] else 'no'} | GPU: {', '.join(hw['gpus']) or '?'}")

    try:
        profile, model = choose_profile(cfg, hw)
    except RuntimeError as e:
        print("\nERROR:", e)
        return 2
    print(f"  Perfil: {profile}  Modelo: {os.path.basename(model)} ({os.path.getsize(model) / 2**30:.1f} GB)")

    port_llm = free_port(int(cfg["port_llm"]))
    port_web = a.port or free_port(int(cfg["port_backend"]))
    client = LlamaClient(f"http://127.0.0.1:{port_llm}")

    kinds = []
    if cfg.get("prefer_gpu") and hw["vulkan"] and os.path.exists(paths.llama_server_exe("vulkan")):
        kinds.append("vulkan")
    kinds.append("cpu")

    proc, used = None, None
    r_cfg = cfg["reasoning"]
    budget = int(r_cfg.get("default_tokens", 768))
    for kind in kinds:
        cached = cached_speed(hw_signature(hw, model, kind))
        if cached:
            budget = reasoning_budget(cfg, cached)
        print(f"  Iniciando motor LLM ({kind}, presupuesto de pensamiento {budget} tok)...")
        proc, llog = start_llama(cfg, hw, model, port_llm, kind, budget)
        if wait_health(client, proc, float(cfg["health_timeout_seconds"]), kind):
            used = kind
            break
        stop(proc)
        print(f"  Falló el arranque con {kind}. Últimas líneas de {llog}:\n{tail(llog, 15)}")
    if used is None:
        print("\nERROR: no se pudo iniciar el modelo. Revisa logs/llama_*.log")
        return 3

    print("  Midiendo velocidad...", end="", flush=True)
    try:
        bench = client.benchmark()
    except Exception as e:
        log.warning("benchmark falló: %s", e)
        bench = {"gen_tps": 5.0, "prompt_tps": 0.0, "seconds": 0}
    print(f" {bench['gen_tps']} tok/s generación, {bench['prompt_tps']} tok/s prompt")
    save_speed(hw_signature(hw, model, used), bench["gen_tps"])
    ideal = reasoning_budget(cfg, bench["gen_tps"])
    if r_cfg["enabled"] and abs(ideal - budget) > float(r_cfg.get("restart_if_deviation", 0.5)) * budget:
        print(f"  Ajustando presupuesto de pensamiento {budget} → {ideal} tokens (reinicio rápido del motor)...")
        stop(proc)
        proc, llog = start_llama(cfg, hw, model, port_llm, used, ideal)
        if not wait_health(client, proc, float(cfg["health_timeout_seconds"]), used):
            print("\nERROR: el motor no volvió a arrancar. Revisa logs/llama_*.log")
            return 3
        budget = ideal
    budget = budget if r_cfg["enabled"] else 0
    est = int(budget / max(bench["gen_tps"], 0.1) + 700 / max(bench["gen_tps"], 0.1))
    print(f"  Presupuesto de razonamiento: {budget} tokens  → ~{est // 60} min {est % 60} s por intento")

    runtime = {"profile": profile, "model": os.path.basename(model), "backend": used, "port_llm": port_llm,
               "port_web": port_web, "gen_tps": bench["gen_tps"], "prompt_tps": bench["prompt_tps"],
               "reasoning_budget": budget, "hardware": hw, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(paths.RUNTIME_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(runtime, f, indent=2)

    import server
    httpd = server.serve(cfg, runtime, port_web)
    url = f"http://127.0.0.1:{port_web}/"
    print(f"\n  LISTO →  {url}\n  (Ctrl+C para salir)\n")
    if cfg.get("open_browser", True) and not a.no_browser:
        try:
            webbrowser.open(url)
        except Exception as e:
            log.warning("No se pudo abrir el navegador: %s", e)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        while True:
            time.sleep(1)
            if proc.poll() is not None:
                print("\nERROR: llama-server se cerró inesperadamente. Ver logs.")
                return 4
    except KeyboardInterrupt:
        print("\n  Cerrando...")
    finally:
        httpd.shutdown()
        stop(proc)
        runners.cleanup_workspace()
        log.info("Sesión terminada. Log: %s", logfile)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
