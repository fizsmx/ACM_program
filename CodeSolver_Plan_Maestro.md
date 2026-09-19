# CODE SOLVER OFFLINE — PLAN MAESTRO v2

> v2 (2026-09-19). Reemplaza la v1 de 50 fases. Cambios principales: pipeline de 1-2 llamadas al LLM en vez de 6 (en CPU cada llamada cuesta minutos), backend sin dependencias externas (solo stdlib), modelos concretos ya elegidos y descargados, hitos verificables en vez de fases teóricas.

## 1. Objetivo

Herramienta portable en un USB que, sin Internet, sin instalación y sin permisos de administrador, recibe un enunciado de programación competitiva en inglés y devuelve una solución en Python o JavaScript ya probada contra los ejemplos del enunciado.

Flujo de uso en competencia:

```text
Conectar USB → doble clic CodeSolver.bat → se abre el navegador (30-90 s de carga del modelo)
→ pegar enunciado → elegir lenguaje → Solve
→ el sistema genera código, extrae los ejemplos, los ejecuta, y si fallan repara (máx. N intentos)
→ Copy Code
```

### Requisitos no negociables

| Requisito | Cómo se cumple |
|---|---|
| Offline | LLM local (llama.cpp + GGUF). Nada llama a Internet. |
| Sin instalar nada | Python embebido, Node portable y llama.cpp van dentro del USB. |
| Sin admin | Solo procesos de usuario, todo escucha en `127.0.0.1`, se escribe únicamente dentro de la carpeta de la app. |
| Cualquier letra de unidad | Todas las rutas se resuelven desde `APP_ROOT` (carpeta del `.bat`). |
| Sin dependencias pip/npm | El backend usa únicamente la biblioteca estándar de Python. |
| Problemas nuevos | El LLM genera; los ejemplos del enunciado verifican. |
| Rápido | Mínimo de llamadas al LLM; streaming a la UI; presupuesto de razonamiento adaptado a la velocidad medida. |

### Reglas

El sistema debe funcionar dentro de lo que la competencia permita. No se implementará nada orientado a ocultar procesos, saltarse políticas de ejecución (AppLocker, SRP), antivirus ni controles de los organizadores. "Evitar las restricciones" significa **no necesitar** instalación, admin ni Internet, no burlar controles. Confirmar con las reglas del evento que un asistente offline está permitido.

---

## 2. Decisiones técnicas (cerradas)

### 2.1 Motor LLM

- `llama-server.exe` de llama.cpp build **b11046** (2026-09-18). Se incluyen dos builds:
  - `bin/llama/cpu/` (18 MB): despacho automático por CPU (SSE4.2 → AVX2 → AVX-512), funciona en cualquier x64.
  - `bin/llama/vulkan/` (30 MB): usa cualquier GPU con driver Vulkan (Intel/AMD/NVIDIA) sin instalar nada; si Vulkan no está disponible cae a CPU.
- El launcher prueba primero Vulkan; si el proceso muere o no pasa `/health` en el tiempo límite, relanza con CPU.
- API OpenAI-compatible en `http://127.0.0.1:<puerto>/v1/chat/completions` con streaming SSE.
- Flags clave: `--jinja`, `--reasoning-budget N`, `-c` (contexto), `-t` (hilos), `-ngl` (capas GPU), `--no-webui`, `--host 127.0.0.1`.

### 2.2 Modelos (familia Qwen3.5, cuantización Unsloth UD-Q4_K_XL)

| Perfil | RAM libre mínima | Modelo | Tamaño | Notas |
|---|---|---|---|---|
| HIGH | ≥ 10 GB | `Qwen3.5-9B-UD-Q4_K_XL.gguf` | 6.0 GB | LiveCodeBench v6 ≈ 65. El mejor ≤10B disponible. |
| MEDIUM | ≥ 5 GB | `Qwen3.5-4B-UD-Q4_K_XL.gguf` | 2.7 GB | Opción por defecto en PCs de 8 GB. |
| LOW | ≥ 3 GB | `Qwen3.5-2B-UD-Q4_K_XL.gguf` | ~1.5 GB | Solo emergencia. Descarga opcional. |

- Qwen3.5 tiene *thinking mode* (razona antes de responder). Mejora mucho en problemas algorítmicos pero cuesta tokens. Se controla con `--reasoning-budget` calculado según la velocidad medida al arrancar.
- **Hallazgo (2026-09-19):** llama-server b11046 ignora `reasoning_budget` por petición; solo funciona como flag de arranque `--reasoning-budget N` (+ `--reasoning-budget-message`). Por eso el launcher arranca con un presupuesto provisional (caché de velocidad por máquina o `default_tokens`), mide tok/s y reinicia el motor solo si el ideal difiere > 50 %. Apagar el thinking por petición sí funciona (`chat_template_kwargs.enable_thinking=false`).
- **Velocidades medidas** en la laptop de desarrollo (i9-13900H **en batería**, OneDrive sincronizando; tomar como peor caso): 4B Q4 ≈ 5-6 tok/s (CPU y Vulkan/Iris Xe iguales en generación; Vulkan 2.5x mejor en prompt), 9B ≈ 2 tok/s, Qwen2.5-Coder-7B ≈ 3 tok/s. A esas velocidades el 9B es inviable en CPU; HIGH solo tiene sentido con GPU dedicada o CPU rápida conectada a corriente. Decisión pendiente de M4: thinking limitado vs sin thinking + más reparaciones.
- Muestreo recomendado por Qwen para código: `temperature 0.6, top_p 0.95, top_k 20` en modo thinking; para reparaciones `temperature 0.2`.
- Qwen2.5-Coder-7B-Instruct queda como candidato de benchmark (sin thinking, más rápido), no como default.

### 2.3 Runtimes

- Python embebido **3.12.10** (`runtime/python/`, 11 MB). Sin pip, sin site-packages: por eso el backend es solo stdlib.
- Node **24.21.0 LTS** (`runtime/node/`, 30 MB sin `npm/` y `node_modules/`, que se eliminan al empaquetar).
- El código generado se ejecuta con esos mismos binarios (nunca `python`/`node` del PATH).

### 2.4 Backend y frontend

- Un solo proceso `app/server.py` (stdlib: `http.server`, `json`, `urllib`, `subprocess`, `threading`).
  - Sirve `web/` (HTML/CSS/JS vanilla, sin frameworks, sin CDN).
  - Proxy con streaming hacia llama-server.
  - Runners de Python y JS con timeout, carpeta temporal por ejecución y captura de stdout/stderr/tiempo.
  - Orquestación: solve → extraer ejemplos → ejecutar → comparar → reparar.
- UI: dos modos. **Competition** (mínimo: enunciado, lenguaje, Solve, código, tests, Copy) y **Developer** (prompts, respuestas crudas, tiempos).
- Modo CLI de respaldo: `CodeSolver.bat solve problema.txt --lang py` por si el navegador está bloqueado.

### 2.5 Pipeline de resolución (mínimas llamadas al LLM)

```text
1. Enunciado ─► extractor de ejemplos por regex (Sample Input/Output, Input:/Output:, Example)
                 └ si no encuentra ninguno: 1 llamada corta al LLM solo para extraer ejemplos (JSON)
2. 1 llamada "solve": el modelo razona (budget limitado) y devuelve
      ANALYSIS (3-6 líneas: input, output, restricciones, idea, complejidad) + CODE (bloque único)
3. Ejecutar cada ejemplo con el runtime correspondiente (timeout configurable)
4. Comparar salida (normalizando espacios/finales de línea; tolerancia opcional para floats)
5. Si falla: 1 llamada "repair" con código + input + esperado + obtenido + stderr. Repetir hasta max_repair_attempts.
6. Si tras N reparaciones sigue fallando: 1 llamada "rethink" que obliga a cambiar de enfoque/algoritmo.
```

Coste típico en CPU de 4 núcleos con el 4B (~12 tok/s): prompt 15 s + razonamiento 60-90 s + código 40 s ≈ 2-3 min por intento. Con el 9B en CPU ~2x más. Con GPU Vulkan bastante menos. El launcher muestra tok/s reales y el tiempo estimado por intento.

### 2.6 Contratos JSON entre módulos

Solo dos objetos cruzan módulos: `TestCase {input, expected}` y `RunResult {status, stdout, stderr, time_ms, exit_code}` con `status ∈ {PASS, WRONG_ANSWER, RUNTIME_ERROR, TIME_LIMIT, COMPILE_ERROR, INTERNAL_ERROR}`. La respuesta del LLM se parsea de texto (bloques ```), nunca se confía en JSON libre del modelo salvo en la extracción de ejemplos, que se valida.

---

## 3. Estructura del proyecto

```text
CodeSolver/
├── CodeSolver.bat          # launcher (doble clic). Determina APP_ROOT y lanza app/launcher.py con runtime/python
├── app/
│   ├── launcher.py         # detecta hardware, elige modelo/perfil, arranca llama-server, espera /health, arranca server.py, abre navegador
│   ├── server.py           # HTTP server (stdlib) + API + proxy streaming
│   ├── llm.py              # cliente de llama-server (chat completions, streaming, budget)
│   ├── solver.py           # orquestación solve/test/repair
│   ├── examples.py         # extracción de ejemplos por regex (+ fallback LLM)
│   ├── runners.py          # ejecución sandbox-lite de Python/JS con timeout
│   ├── compare.py          # comparador de salidas
│   ├── hardware.py         # RAM/CPU/GPU, perfiles
│   ├── paths.py            # APP_ROOT y rutas portables
│   └── cli.py              # modo consola de respaldo
├── web/                    # index.html, app.js, style.css (sin CDN)
├── prompts/                # solve.txt, repair.txt, rethink.txt, extract_examples.txt
├── config/config.json      # perfiles, timeouts, puertos, muestreo
├── bin/llama/{cpu,vulkan}/
├── runtime/{python,node}/
├── models/*.gguf
├── tests/problems/         # enunciados + soluciones de referencia para benchmark
├── tools/                  # solo desarrollo: fetch_deps.py, bench.py, package.py
├── workspace/              # temporales de ejecución (se limpia al salir)
├── logs/
└── docs/
```

---

## 4. Hitos (cada uno termina con una prueba que pasa)

### M0 — Bootstrap  ✅ 2026-09-19
- Estructura de carpetas, `tools/fetch_deps.py` idempotente y reanudable.
- Descargados: llama.cpp cpu+vulkan b11046, Python 3.12.10 embed, Node 24.21.0, modelos 9B y 4B.
- **Prueba:** `runtime/python/python.exe -V`, `runtime/node/node.exe -v`, `llama-server --version` funcionan desde la carpeta.

### M1 — LLM local en marcha  ✅ 2026-09-19
- `hardware.py`: RAM total/libre (ctypes → `GlobalMemoryStatusEx`), hilos, detección de `vulkan-1.dll`.
- `launcher.py`: elige perfil y modelo, lanza llama-server (Vulkan → CPU fallback), espera `/health`, mide tok/s con un prompt corto, calcula `reasoning_budget`, escribe `workspace/runtime.json`, apaga limpio (Ctrl+C / cierre) y mata huérfanos de sesiones previas (PID guardado).
- **Prueba:** `CodeSolver.bat` arranca sin Internet y responde "hola" desde el modelo; al cerrar no quedan `llama-server.exe`.

### M2 — Solve end-to-end (MVP usable)  ✅ 2026-09-19 (primer problema resuelto PASS 2/2 desde la API; falta el dataset completo)
- `prompts/`, `llm.py` (streaming), `examples.py`, `runners.py`, `compare.py`, `solver.py`, `server.py`, `web/`.
- Endpoints: `GET /api/status`, `POST /api/solve` (SSE: fases, tokens, tests, reparaciones), `POST /api/run` (código + input manual), `POST /api/cancel`, `POST /api/reset`.
- **Prueba:** los 3 problemas iniciales en `tests/problems/` se resuelven en Python y JS desde la UI. Tests unitarios de `examples.py` y `compare.py`.

### M3 — Robustez
- Timeouts en todo; cancelación; limpieza de `workspace/`; logs por sesión en `logs/`; mensajes claros para: modelo ausente/corrupto, RAM insuficiente, puerto ocupado, llama-server no arranca, navegador no abre (imprimir URL), código inválido, TLE.
- Recuperación: al arrancar, detectar `llama-server` de una sesión anterior y cerrarlo.
- **Prueba:** simulaciones de fallo de la tabla de la sección 6; cuenta de usuario estándar sin admin; USB en letra distinta.

### M4 — Calidad de soluciones
- `tests/problems/`: 30-50 problemas variados (arrays, strings, math, sorting, binary search, hashing, two pointers, BFS/DFS, greedy, DP, simulación) con ejemplos y tests ocultos.
- `tools/bench.py`: resuelve todos, mide aciertos primer intento / tras reparación / fallo, tiempo medio, tokens. Compara 9B vs 4B vs Qwen2.5-Coder-7B y distintos `reasoning_budget`.
- Ajustar prompts a partir de los fallos (lectura rápida de stdin, formato exacto de salida, múltiples casos, BigInt en JS, recursión → iterativo en Python, `sys.setrecursionlimit`).
- **Prueba:** ≥ 70 % del dataset resuelto con el perfil MEDIUM en menos de 4 min por problema.

### M5 — Empaquetado y validación real
- `tools/package.py`: copia solo lo necesario a `dist/CodeSolver/` (sin `.git`, `tools/downloads`, `npm`, `node_modules`, logs, workspace), genera `MANIFEST.txt` con hashes.
- Pruebas obligatorias: (1) Wi-Fi/Ethernet apagados; (2) cuenta sin admin; (3) USB en otra PC con otra letra; (4) PC limpia sin Python/Node/Git; (5) PC de 8 GB de RAM sin GPU.
- Docs: `README.md` (arranque, requisitos, modos), `docs/TROUBLESHOOTING.md`.
- **Prueba:** checklist de la sección 7 completa.

### M6 — Opcional
- Soporte C++ (bundle de `w64devkit` ~100 MB) si la competencia lo valora.
- Biblioteca de plantillas de algoritmos inyectada al prompt según categoría detectada.
- Modo "hint": explica el enfoque sin dar código.

---

## 5. Configuración (`config/config.json`)

```json
{
  "language": "python",
  "port_backend": 8765,
  "port_llm": 8766,
  "max_repair_attempts": 2,
  "test_timeout_seconds": 5,
  "solve_timeout_seconds": 600,
  "reasoning": { "enabled": true, "seconds_budget": 90, "min_tokens": 512, "max_tokens": 4096 },
  "sampling": { "temperature": 0.6, "top_p": 0.95, "top_k": 20, "repair_temperature": 0.2 },
  "context_size": 16384,
  "profiles": {
    "HIGH":   { "min_free_ram_gb": 10, "model": "Qwen3.5-9B-UD-Q4_K_XL.gguf" },
    "MEDIUM": { "min_free_ram_gb": 5,  "model": "Qwen3.5-4B-UD-Q4_K_XL.gguf" },
    "LOW":    { "min_free_ram_gb": 3,  "model": "Qwen3.5-2B-UD-Q4_K_XL.gguf" }
  },
  "force_profile": null,
  "prefer_gpu": true,
  "copy_model_to_local_temp": false
}
```

`copy_model_to_local_temp`: si el USB es lento (USB 2.0 ≈ 30 MB/s → 6 GB tardan 3-4 min en cargar), copiar el modelo a `%TEMP%` puede acelerar el arranque. Solo si las reglas lo permiten y hay disco.

---

## 6. Modos de fallo y respuesta

| Situación | Comportamiento |
|---|---|
| Modelo no encontrado | Listar `models/`, indicar cuál falta y con qué perfil. Ofrecer el siguiente perfil inferior. |
| RAM insuficiente para todos los perfiles | Mensaje claro con RAM libre y mínima necesaria. |
| Vulkan falla | Reintento automático con build CPU. |
| llama-server no pasa `/health` en 180 s | Mostrar últimas 30 líneas de su log y salir. |
| Puerto ocupado | Probar los 5 puertos siguientes. |
| Navegador no abre | Imprimir la URL en consola; modo CLI disponible. |
| LLM devuelve sin bloque de código | Reintento con instrucción más estricta (1 vez), luego error visible. |
| Código con error de sintaxis | Se trata como COMPILE_ERROR y entra al ciclo de reparación. |
| TLE en tests | Se reporta TIME_LIMIT y el prompt de reparación pide mejor complejidad. |
| Cierre inesperado | Al siguiente arranque se mata el PID guardado y se limpia `workspace/`. |

---

## 7. Checklist de aceptación final

- [ ] Arranca desde USB con doble clic, en letra D:, E: o cualquier otra.
- [ ] Funciona con red desactivada.
- [ ] Funciona en cuenta sin administrador.
- [ ] Funciona en PC sin Python/Node/Git instalados.
- [ ] Funciona en PC de 8 GB sin GPU (perfil MEDIUM).
- [ ] Muestra tok/s y tiempo estimado al arrancar.
- [ ] Resuelve problemas nuevos en inglés en Python y JavaScript.
- [ ] Extrae ejemplos del enunciado y los ejecuta.
- [ ] Repara fallos y cambia de enfoque si es necesario.
- [ ] Todo tiene timeout y se puede cancelar.
- [ ] Limpia temporales y no deja procesos huérfanos.
- [ ] Modo Competition y Developer; modo CLI de respaldo.
- [ ] ≥ 70 % del dataset de benchmark resuelto.
- [ ] README y TROUBLESHOOTING escritos.

---

## 8. Principio de diseño

> El modelo propone, los ejemplos del enunciado verifican, el sistema repara. Nunca se muestra como "resuelto" un código que no pasó los ejemplos.
