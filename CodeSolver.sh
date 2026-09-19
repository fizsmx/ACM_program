#!/usr/bin/env bash
# Lanzador de CodeSolver para Linux (Ubuntu). Corre desde el mismo USB que la version Windows.
# Uso:
#   ./CodeSolver.sh                 -> arranca el modelo + interfaz web (http://127.0.0.1:8765/)
#   ./CodeSolver.sh --profile HIGH  -> opciones que entiende el launcher (--profile, --cpu, --no-browser, --check...)
#   ./CodeSolver.sh solve prob.txt --lang python --out sol.py   -> modo consola
set -euo pipefail

# APP_ROOT = carpeta de este script, resolviendo symlinks. Funciona con ./CodeSolver.sh o bash CodeSolver.sh.
APP_ROOT="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$APP_ROOT"

export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$APP_ROOT/app"

PY="$APP_ROOT/runtime/python-linux/bin/python3"

if [[ ! -x "$PY" && ! -f "$PY" ]]; then
  echo "ERROR: falta el runtime de Linux ($PY)."
  echo "En la maquina de desarrollo (con Internet) ejecuta:  python3 tools/fetch_deps.py --linux"
  echo "y vuelve a empaquetar el USB con:  python3 tools/package.py --dest <USB>/CodeSolver --platform both"
  exit 1
fi

# En exFAT los archivos pierden el bit de ejecucion. Se lo devolvemos (best-effort).
chmod_ok=1
for f in \
  "$APP_ROOT/runtime/python-linux/bin/python3" \
  "$APP_ROOT/runtime/node-linux/bin/node" \
  "$APP_ROOT/bin/llama/linux-cpu/llama-server" \
  "$APP_ROOT/bin/llama/linux-vulkan/llama-server"; do
  if [[ -e "$f" ]]; then
    chmod +x "$f" 2>/dev/null || chmod_ok=0
  fi
done
if [[ "$chmod_ok" -eq 0 ]]; then
  echo "AVISO: no se pudo dar permiso de ejecucion a los binarios (sistema de archivos de solo lectura o 'noexec')."
  echo "       Si el USB esta montado con 'noexec', copia la carpeta al disco local y ejecutala desde ahi:"
  echo "         cp -r \"$APP_ROOT\" ~/CodeSolver && cd ~/CodeSolver && ./CodeSolver.sh"
  echo "       (ver docs/LINUX.md)"
fi

# Modo consola de respaldo:  ./CodeSolver.sh solve problema.txt ...
if [[ "${1:-}" == "solve" ]]; then
  shift
  exec "$PY" -X utf8 "$APP_ROOT/app/cli.py" "$@"
fi

set +e
"$PY" -X utf8 "$APP_ROOT/app/launcher.py" "$@"
rc=$?
set -e
if [[ "$rc" -ne 0 ]]; then
  echo
  echo "CodeSolver termino con error $rc. Revisa la carpeta logs/ (session_*.log y llama_*.log)."
fi
exit "$rc"
