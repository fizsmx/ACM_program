# CodeSolver Offline

Asistente portable de programación competitiva: pega un enunciado en inglés, elige Python o JavaScript y obtén una solución ya verificada contra los ejemplos del enunciado. Funciona sin Internet, sin instalación y sin permisos de administrador, desde una carpeta o un USB.

## Uso (competencia)

1. Conecta el USB y haz doble clic en `CodeSolver.bat`.
2. Espera el mensaje `LISTO → http://127.0.0.1:8765/` (se abre el navegador solo; si no, copia la URL).
3. Pega el enunciado completo, elige el lenguaje y pulsa **Solve** (o Ctrl+Enter).
4. Revisa los tests: verde = pasó los ejemplos. **Copy code** y listo.
5. Cierra la ventana negra al terminar (apaga el modelo y limpia temporales).

Modo consola de respaldo, con el launcher abierto en otra ventana:

```
CodeSolver.bat solve problema.txt --lang python --out sol.py
```

## Requisitos de la PC de destino

- Windows 10/11 x64.
- RAM libre: 5 GB para el perfil MEDIUM (modelo 4B), 10 GB para HIGH (9B). El launcher elige solo.
- GPU opcional: si hay driver Vulkan se usa automáticamente; si no, CPU.
- No hace falta Python, Node ni nada instalado.

## Qué hay dentro

| Carpeta | Contenido |
|---|---|
| `app/` | Backend en Python (solo biblioteca estándar) |
| `web/` | Interfaz (HTML/JS sin frameworks) |
| `prompts/` | Prompts del modelo: solve, repair, rethink, extract_examples |
| `bin/llama/{cpu,vulkan}/` | llama.cpp b11046 |
| `runtime/python/`, `runtime/node/` | Python 3.12 embebido y Node 24 portable |
| `models/` | Modelos GGUF (Qwen3.5 9B / 4B) |
| `config/config.json` | Perfiles, timeouts, puertos, muestreo |
| `tests/` | Tests unitarios y problemas de benchmark |
| `tools/` | Solo desarrollo: `fetch_deps.py`, `bench.py` |
| `workspace/`, `logs/` | Temporales y registros de cada sesión |

## Preparar el paquete (máquina de desarrollo, con Internet)

```
python tools/fetch_deps.py            # llama.cpp, Python, Node, modelos 9B y 4B
python tools/fetch_deps.py --only coder7b,model2b   # opcionales
runtime\python\python.exe -X utf8 tests\test_units.py   # 17 tests sin LLM
```

## Cómo funciona

1. Se extraen los ejemplos del enunciado con regex (Codeforces, UVa, LeetCode…); si no hay, se le pide al modelo.
2. Una llamada al modelo produce análisis + código (con "thinking" limitado por un presupuesto de tokens calculado a partir de la velocidad medida al arrancar).
3. El código se valida (sintaxis) y se ejecuta contra cada ejemplo con el runtime incluido y timeout.
4. Si falla, se envía el fallo (input, esperado, obtenido, stderr) para reparar, hasta `max_repair_attempts`; después un intento "rethink" cambia de enfoque.
5. Nunca se muestra como PASS un código que no pasó los ejemplos.

## Reglas

Esta herramienta no oculta procesos ni evade políticas del sistema o de la competencia. Verifica con las reglas del evento que un asistente offline está permitido antes de usarla.

Ver también `CodeSolver_Plan_Maestro.md` (plan) y `docs/TROUBLESHOOTING.md`.
