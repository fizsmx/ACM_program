"""Empaqueta CodeSolver en una carpeta de destino (USB) de forma incremental e idempotente.

Uso (desde la raíz del proyecto, con el Python del sistema o el embebido):
    python tools/package.py --dest D:\\CodeSolver --models 4b,9b
    python tools/package.py                      # -> dist/CodeSolver, todos los modelos presentes

- Copia solo archivos nuevos o con tamaño/mtime distinto (los modelos se saltan si el tamaño coincide).
- Borra en destino lo que ya no existe en origen, salvo workspace/ y logs/.
- Excluye .git, tools/downloads, workspace, logs, dist, __pycache__, *.pyc, basura de npm en runtime/node, *.part.
- Genera MANIFEST.txt (ruta, tamaño, sha256; los modelos solo con tamaño).
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_ALIASES = {
    "4b": "Qwen3.5-4B-UD-Q4_K_XL.gguf",
    "9b": "Qwen3.5-9B-UD-Q4_K_XL.gguf",
    "2b": "Qwen3.5-2B-UD-Q4_K_XL.gguf",
    "coder7b": "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
}

# rutas relativas (con /) excluidas siempre; los patrones se comparan con fnmatch contra la ruta relativa
EXCLUDE_DIRS = {
    ".git", "tools/downloads", "workspace", "logs", "dist", "runtime/node/node_modules",
    # basura de npm/corepack del Node portable de Linux (no se usa; ahorra ~30 MB)
    "runtime/node-linux/lib/node_modules/npm", "runtime/node-linux/lib/node_modules/corepack",
}
EXCLUDE_PATTERNS = [
    "*/__pycache__/*", "__pycache__/*", "*.pyc", "*.part",
    "runtime/node/npm*", "runtime/node/npx*", "runtime/node/corepack*", "runtime/node/install_tools.bat",
    "runtime/node/nodevars.bat", "runtime/node/CHANGELOG.md", "MANIFEST.txt",
    "runtime/node-linux/bin/npm", "runtime/node-linux/bin/npx", "runtime/node-linux/bin/corepack",
    "runtime/node-linux/CHANGELOG.md",
]

# binarios propios de cada plataforma (para --platform); son prefijos de ruta o archivos sueltos
WIN_ONLY = {"bin/llama/cpu", "bin/llama/vulkan", "runtime/python", "runtime/node", "CodeSolver.bat"}
LINUX_ONLY = {"bin/llama/linux-cpu", "bin/llama/linux-vulkan", "runtime/python-linux", "runtime/node-linux", "CodeSolver.sh"}

BIG = 64 * 1024 * 1024  # a partir de aquí se muestra progreso


def rel(path: str, base: str) -> str:
    return os.path.relpath(path, base).replace("\\", "/")


def platform_excludes(platform: str) -> set[str]:
    """Prefijos/archivos a excluir según --platform (win | linux | both)."""
    if platform == "win":
        return set(LINUX_ONLY)
    if platform == "linux":
        return set(WIN_ONLY)
    return set()


def excluded(r: str, with_tests: bool, extra_dirs: frozenset[str] = frozenset()) -> bool:
    parts = r.split("/")
    for i in range(1, len(parts) + 1):
        prefix = "/".join(parts[:i])
        if prefix in EXCLUDE_DIRS or prefix in extra_dirs:
            return True
    if not with_tests and parts[0] == "tests":
        return True
    return any(fnmatch.fnmatch(r, p) for p in EXCLUDE_PATTERNS)


def wanted_models(spec: str | None) -> set[str] | None:
    if not spec:
        return None  # todos los que existan
    out = set()
    for tok in spec.split(","):
        tok = tok.strip().lower()
        if not tok:
            continue
        if tok in MODEL_ALIASES:
            out.add(MODEL_ALIASES[tok])
        else:
            out.add(tok)  # nombre de archivo literal
    return out


def collect(with_tests: bool, models: set[str] | None, extra_dirs: frozenset[str] = frozenset()) -> list[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        r_dir = rel(dirpath, ROOT)
        r_dir = "" if r_dir == "." else r_dir
        # podar directorios excluidos
        dirnames[:] = [d for d in sorted(dirnames) if not excluded((r_dir + "/" + d).lstrip("/"), with_tests, extra_dirs)]
        for fn in sorted(filenames):
            r = (r_dir + "/" + fn).lstrip("/")
            if excluded(r, with_tests, extra_dirs):
                continue
            if r.startswith("models/"):
                if not fn.lower().endswith(".gguf"):
                    continue
                if models is not None and fn not in models:
                    continue
            files.append(r)
    return files


def same(src: str, dst: str, is_model: bool) -> bool:
    if not os.path.exists(dst):
        return False
    ss, ds = os.stat(src), os.stat(dst)
    if ss.st_size != ds.st_size:
        return False
    if is_model:
        return True  # los modelos solo por tamaño (exFAT redondea mtime y copiar 6 GB de más es caro)
    return abs(ss.st_mtime - ds.st_mtime) <= 2.0  # exFAT/FAT tienen resolución de 2 s


def copy_with_progress(src: str, dst: str, label: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    size = os.path.getsize(src)
    tmp = dst + ".copying"
    t0 = time.time()
    done = 0
    last = 0.0
    with open(src, "rb") as fi, open(tmp, "wb") as fo:
        while True:
            chunk = fi.read(8 * 1024 * 1024)
            if not chunk:
                break
            fo.write(chunk)
            done += len(chunk)
            if size >= BIG and time.time() - last > 2:
                last = time.time()
                rate = done / 1e6 / max(time.time() - t0, 1e-6)
                print(f"    {label}: {100 * done / size:5.1f}%  {done / 1e6:7.0f} MB  {rate:5.1f} MB/s", flush=True)
    shutil.copystat(src, tmp)
    if os.path.exists(dst):
        os.remove(dst)
    os.replace(tmp, dst)
    if size >= BIG:
        print(f"    {label}: listo en {time.time() - t0:.0f} s ({size / 1e6 / max(time.time() - t0, 1e-6):.1f} MB/s)", flush=True)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _under(r: str, prefixes: frozenset[str]) -> bool:
    parts = r.split("/")
    return any("/".join(parts[:i]) in prefixes for i in range(1, len(parts) + 1))


def prune(dest: str, keep: set[str], protected: frozenset[str] = frozenset()) -> int:
    """Borra en destino archivos/dirs que no están en `keep` (rutas relativas), salvo workspace/, logs/
    y los prefijos `protected` (p. ej. los binarios de la otra plataforma cuando se usa --platform)."""
    protected = frozenset(protected | {"workspace", "logs"})
    removed = 0
    for dirpath, dirnames, filenames in os.walk(dest, topdown=False):
        r_dir = rel(dirpath, dest)
        r_dir = "" if r_dir == "." else r_dir
        if r_dir and _under(r_dir, protected):
            continue
        for fn in filenames:
            r = (r_dir + "/" + fn).lstrip("/")
            if r == "MANIFEST.txt":
                continue
            if r not in keep and not _under(r, protected):
                os.remove(os.path.join(dirpath, fn))
                removed += 1
        for d in dirnames:
            full = os.path.join(dirpath, d)
            rd = (r_dir + "/" + d).lstrip("/")
            if _under(rd, protected):
                continue
            try:
                if not os.listdir(full):
                    os.rmdir(full)
            except OSError:
                pass
    return removed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", default=os.path.join(ROOT, "dist", "CodeSolver"))
    ap.add_argument("--models", default=None, help="alias separados por coma: 4b,9b,2b,coder7b o nombres de archivo")
    ap.add_argument("--platform", choices=("win", "linux", "both"), default="both",
                    help="qué binarios incluir: win (.exe), linux (mismo USB para Ubuntu) o both (ambos, default)")
    ap.add_argument("--without-tests", action="store_true", help="no copiar tests/ (bench.py los necesita)")
    ap.add_argument("--no-prune", action="store_true", help="no borrar en destino lo que sobra")
    ap.add_argument("--no-manifest", action="store_true")
    a = ap.parse_args()

    dest = os.path.abspath(a.dest)
    if os.path.normcase(dest) == os.path.normcase(ROOT) or os.path.normcase(ROOT).startswith(os.path.normcase(dest) + os.sep):
        print("ERROR: el destino no puede ser la carpeta del proyecto ni contenerla")
        return 2
    models = wanted_models(a.models)
    if models is not None:
        missing = [m for m in models if not os.path.exists(os.path.join(ROOT, "models", m))]
        if missing:
            print("ERROR: modelos no encontrados en models/: " + ", ".join(missing))
            return 2

    extra_dirs = frozenset(platform_excludes(a.platform))
    t0 = time.time()
    files = collect(with_tests=not a.without_tests, models=models, extra_dirs=extra_dirs)
    total_bytes = sum(os.path.getsize(os.path.join(ROOT, r)) for r in files)
    print(f"Origen : {ROOT}\nDestino: {dest}\nPlataforma: {a.platform}\nArchivos: {len(files)}  ({total_bytes / 2**30:.2f} GB)")
    os.makedirs(dest, exist_ok=True)

    copied = skipped = copied_bytes = 0
    for r in files:
        src = os.path.join(ROOT, r)
        dst = os.path.join(dest, r)
        is_model = r.startswith("models/")
        if same(src, dst, is_model):
            skipped += 1
            continue
        size = os.path.getsize(src)
        if size >= BIG:
            print(f"  copiando {r} ({size / 2**30:.2f} GB)", flush=True)
        copy_with_progress(src, dst, os.path.basename(r))
        copied += 1
        copied_bytes += size

    removed = 0 if a.no_prune else prune(dest, set(files))
    for d in ("workspace", "logs"):
        os.makedirs(os.path.join(dest, d), exist_ok=True)

    if not a.no_manifest:
        mpath = os.path.join(dest, "MANIFEST.txt")
        with open(mpath, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# CodeSolver package  {time.strftime('%Y-%m-%d %H:%M:%S')}\n# ruta\ttamaño\tsha256\n")
            for r in files:
                p = os.path.join(dest, r)
                size = os.path.getsize(p)
                digest = "-" if r.startswith("models/") else sha256(p)
                f.write(f"{r}\t{size}\t{digest}\n")

    dt = time.time() - t0
    dest_total = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(dest) for fn in fns)
    print(f"\nCopiados {copied} ({copied_bytes / 2**30:.2f} GB), sin cambios {skipped}, eliminados {removed}. "
          f"Tamaño en destino {dest_total / 2**30:.2f} GB. Tiempo {dt:.0f} s"
          + (f" ({copied_bytes / 1e6 / dt:.1f} MB/s)" if copied_bytes and dt > 0 else "") + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
