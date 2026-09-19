"""Descarga todas las dependencias binarias de CodeSolver (solo para la maquina de desarrollo).

Uso:  python tools/fetch_deps.py [--only llama,python,node,model9b,model4b] [--skip-models]
Es idempotente y reanuda descargas interrumpidas (HTTP Range).
"""
from __future__ import annotations
import argparse, os, sys, time, zipfile, shutil, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(ROOT, "tools", "downloads")

LLAMA_TAG = "b11046"
NODE_VER = "24.21.0"
PY_VER = "3.12.10"

ITEMS = {
    "llama_cpu": dict(
        url=f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_TAG}/llama-{LLAMA_TAG}-bin-win-cpu-x64.zip",
        file=f"llama-{LLAMA_TAG}-cpu.zip", extract_to="bin/llama/cpu"),
    "llama_vulkan": dict(
        url=f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_TAG}/llama-{LLAMA_TAG}-bin-win-vulkan-x64.zip",
        file=f"llama-{LLAMA_TAG}-vulkan.zip", extract_to="bin/llama/vulkan"),
    "python": dict(
        url=f"https://www.python.org/ftp/python/{PY_VER}/python-{PY_VER}-embed-amd64.zip",
        file=f"python-{PY_VER}-embed.zip", extract_to="runtime/python"),
    "node": dict(
        url=f"https://nodejs.org/dist/v{NODE_VER}/node-v{NODE_VER}-win-x64.zip",
        file=f"node-v{NODE_VER}.zip", extract_to="runtime/node"),
    "model9b": dict(
        url="https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-UD-Q4_K_XL.gguf",
        file="Qwen3.5-9B-UD-Q4_K_XL.gguf", copy_to="models"),
    "model4b": dict(
        url="https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-UD-Q4_K_XL.gguf",
        file="Qwen3.5-4B-UD-Q4_K_XL.gguf", copy_to="models"),
    "coder7b": dict(
        url="https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        file="Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf", copy_to="models"),
    "model2b": dict(
        url="https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-UD-Q4_K_XL.gguf",
        file="Qwen3.5-2B-UD-Q4_K_XL.gguf", copy_to="models"),
}
DEFAULT = ["llama_cpu", "llama_vulkan", "python", "node", "model9b", "model4b"]


def remote_size(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "codesolver-fetch"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers.get("Content-Length") or 0)


def download(url: str, dest: str) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    part = dest + ".part"
    total = remote_size(url)
    if os.path.exists(dest) and (total == 0 or os.path.getsize(dest) == total):
        print(f"  ok (ya existe) {os.path.basename(dest)}")
        return
    have = os.path.getsize(part) if os.path.exists(part) else 0
    if total and have >= total:
        os.replace(part, dest); return
    headers = {"User-Agent": "codesolver-fetch"}
    if have:
        headers["Range"] = f"bytes={have}-"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r, open(part, "ab" if have else "wb") as f:
        if have and r.status != 206:  # servidor no soporta reanudar
            f.seek(0); f.truncate(); have = 0
        done, t0, last = have, time.time(), 0.0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk); done += len(chunk)
            if time.time() - last > 2:
                last = time.time()
                mb = done / 1e6; rate = (done - have) / 1e6 / max(time.time() - t0, 1e-6)
                pct = f"{100*done/total:5.1f}%" if total else "   ?%"
                print(f"  {pct} {mb:8.0f} MB  {rate:5.1f} MB/s", flush=True)
    if total and os.path.getsize(part) != total:
        raise RuntimeError(f"tamano incorrecto para {dest}: {os.path.getsize(part)} != {total}")
    os.replace(part, dest)


def extract(zip_path: str, target: str) -> None:
    if os.path.isdir(target) and os.listdir(target):
        print(f"  ok (ya extraido) {target}"); return
    tmp = target + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(tmp)
    entries = os.listdir(tmp)
    src = os.path.join(tmp, entries[0]) if len(entries) == 1 and os.path.isdir(os.path.join(tmp, entries[0])) else tmp
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.move(src, target)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"  extraido -> {target}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="lista separada por comas: " + ",".join(ITEMS))
    ap.add_argument("--skip-models", action="store_true")
    a = ap.parse_args()
    names = a.only.split(",") if a.only else DEFAULT
    if a.skip_models:
        names = [n for n in names if not n.startswith("model")]
    for n in names:
        it = ITEMS[n]
        # los modelos se descargan directo a models/ (evita duplicar varios GB)
        dest = os.path.join(ROOT, it["copy_to"], it["file"]) if "copy_to" in it else os.path.join(DL, it["file"])
        print(f"[{n}] {it['url']}")
        download(it["url"], dest)
        if "extract_to" in it:
            extract(dest, os.path.join(ROOT, it["extract_to"]))
    print("LISTO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
