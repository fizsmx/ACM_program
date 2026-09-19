# CodeSolver Offline — Manual de uso

Versión del 2026-09-19. Para la carpeta `CodeSolver` del USB.

---

## 0. Antes de la competencia (5 minutos, en casa)

1. Conecta el USB en cualquier PC y abre la carpeta `CodeSolver`.
2. Abre una consola en esa carpeta (Shift + clic derecho → "Abrir ventana de PowerShell aquí") y ejecuta:
   ```
   .\CodeSolver.bat --check
   ```
   Debe terminar en `Resultado: TODO OK`. Si algo sale `[ERROR]`, mira la sección 7.
3. Comprueba que existen `models\Qwen3.5-4B-UD-Q4_K_XL.gguf` (2.7 GB) y, opcionalmente, `models\Qwen3.5-9B-UD-Q4_K_XL.gguf` (5.6 GB).
4. Lleva el USB y, si puedes, el cargador de la laptop: en batería el modelo va a la mitad de velocidad.

Confirma con las reglas del evento que un asistente offline está permitido. La herramienta no oculta nada ni evade políticas del sistema.

---

## 1. Arrancar

1. Conecta el USB. Da igual la letra (D:, E:, F:…).
2. Doble clic en `CodeSolver.bat`. Aparece una ventana negra. **No la cierres mientras uses el programa.**
3. Espera. Verás:
   ```
   RAM: ... | CPUs lógicas: ... | Vulkan: sí/no
   Perfil: MEDIUM  Modelo: Qwen3.5-4B-UD-Q4_K_XL.gguf (2.7 GB)
   Iniciando motor LLM (vulkan|cpu, presupuesto de pensamiento N tok)...
   cargando modelo... 45 s
   Midiendo velocidad... 6.4 tok/s generación
   Presupuesto de razonamiento: 804 tokens → ~3 min 55 s por intento
   ################################################################
   #   LISTO  →  abre en el navegador:  http://127.0.0.1:8765/    #
   ################################################################
   ```
4. El navegador se abre solo. Si no, abre cualquier navegador y escribe `http://127.0.0.1:8765/`.

Tiempo total de arranque desde USB: 1 a 2 minutos (carga del modelo + medición).

**Lee la línea "tok/s" y "por intento":** es la velocidad real de esa PC. Si dice menos de 3 tok/s, cada problema tardará más de 6 minutos por intento; considera usar la herramienta solo para los problemas que no sepas hacer.

Opciones al arrancar (desde consola):

| Comando | Para qué |
|---|---|
| `CodeSolver.bat` | Normal: elige el mejor modelo que quepa en la RAM libre |
| `CodeSolver.bat --profile MEDIUM` | Fuerza el 4B (más rápido). Úsalo si la PC es lenta |
| `CodeSolver.bat --profile HIGH` | Fuerza el 9B (más listo, 2x más lento). Solo con GPU o PC potente |
| `CodeSolver.bat --cpu` | No usar GPU/Vulkan (si el arranque con Vulkan falla o se cuelga) |
| `CodeSolver.bat --check` | Diagnóstico sin cargar el modelo |
| `CodeSolver.bat solve prob.txt --lang python --out sol.py` | Modo consola, si el navegador está bloqueado (con el launcher abierto en otra ventana) |

---

## 2. La pantalla

```
┌─────────────────────────────────┬─────────────────────────────────┐
│ Language [Python 3 ▼] ☑Thinking │ fase · tiempo      [Run] [Copy] │
│           [Solve] [Cancel] [Clear]│ Análisis (input/output/idea)    │
│ ┌─────────────────────────────┐ │ ┌─────────────────────────────┐ │
│ │ Pega aquí el enunciado      │ │ │ Código (editable)           │ │
│ │ COMPLETO                    │ │ │                             │ │
│ └─────────────────────────────┘ │ └─────────────────────────────┘ │
│ ▸ Sample tests (2)  [+ add]     │ #1 PASS 114ms  #2 PASS 95ms     │
│   input | expected | ×          │ ▸ Model thinking                │
└─────────────────────────────────┴─────────────────────────────────┘
```

- **Barra superior**: modelo, perfil, tok/s y presupuesto de pensamiento. Verde = motor listo. Rojo = el launcher se cerró.
- **Language**: Python 3 (por defecto) o JavaScript (Node).
- **Thinking**: si está marcado, el modelo razona antes de escribir el código (mejor calidad, +1-2 min). Desmárcalo para problemas triviales o si la PC es muy lenta.
- **Sample tests**: los ejemplos extraídos del enunciado. Puedes corregirlos, borrarlos o añadir más. Se usan para verificar el código.
- **Fase · tiempo**: qué está haciendo (`solve`, `testing`, `repair 1/2`, `rethink`) y cuánto lleva.
- **Código**: se va escribiendo en vivo. Es editable: puedes retocarlo y pulsar **Run with input** para probarlo con una entrada tuya.
- **Pastillas de tests**: `PASS` verde, `WRONG_ANSWER`/`RUNTIME_ERROR` rojo, `TIME_LIMIT` amarillo. Clic en una pastilla para ver salida esperada vs obtenida y el error.
- **Developer mode** (arriba a la derecha): muestra un log técnico con tiempos y tokens. No hace falta en competencia.

---

## 3. Resolver un problema (flujo normal)

1. **Copia el enunciado completo**: título, descripción, formato de entrada, formato de salida, restricciones y **todos los ejemplos**. Sin los ejemplos el sistema no puede verificar nada.
2. Pégalo en el cuadro de la izquierda. Elige el lenguaje.
3. Pulsa **Solve** (o Ctrl + Enter).
4. Mira el panel "Sample tests": si aparecieron los ejemplos correctos, bien. Si falta alguno o la salida esperada está mal cortada, corrígelo mientras el modelo piensa (los cambios se usan si vuelves a pulsar Solve; el intento actual usa los que había).
5. Espera. Verás el pensamiento (desplegable) y luego el código escribiéndose. Después se ejecutan los tests.
6. Resultado:
   - **✔ All sample tests passed** → pulsa **Copy code**, pégalo en el juez y envía. Antes, un vistazo rápido: ¿lee toda la entrada? ¿imprime exactamente el formato pedido?
   - **repair 1/2, repair 2/2**: falló un ejemplo; el modelo recibe el fallo y corrige. Cada reparación cuesta un intento completo (~3-4 min).
   - **rethink**: tras dos reparaciones sigue fallando; el modelo cambia de enfoque desde cero.
   - **✖ Still failing** o **⏱ Time limit reached**: no lo consiguió en 10 minutos. Ver sección 4.
   - **⚠ No sample tests: code NOT verified**: no había ejemplos reconocibles. El código NO está probado. Añade un test con **+ add** y vuelve a Solve.

Tiempos orientativos con el 4B a ~6 tok/s: 2.5-4 min si acierta a la primera; hasta 10 min (límite) si necesita reparar.

---

## 4. Cuando no lo resuelve

Por orden de lo más rápido a lo más lento:

1. **Lee el código y el análisis.** Muchas veces el algoritmo es correcto y falla un detalle de formato (un espacio, mayúsculas de "YES", una línea final). Arréglalo a mano en el panel de código y prueba con **Run with input**.
2. **Revisa los tests extraídos.** Si el "expected" tiene una frase de explicación pegada o le falta una línea, el sistema marcará WRONG_ANSWER aunque el código esté bien. Corrige el test y pulsa Solve otra vez.
3. **Vuelve a pulsar Solve.** El modelo es no determinista: el mismo enunciado puede salir bien en el segundo intento. Si el problema es simple, desmarca Thinking para que sea más rápido.
4. **Simplifica el enunciado.** Si tiene historia larga, deja solo: qué se pide, formato de entrada, formato de salida, restricciones y ejemplos. Menos texto = menos tiempo de prompt y menos confusión.
5. **Da una pista.** Añade al final del enunciado una línea como `Hint: use binary search on the answer` o `Hint: BFS from all sources at once`. El modelo la seguirá.
6. **Cambia de modelo.** Si la PC tiene GPU o es rápida (>8 tok/s con el 4B), cierra y relanza con `--profile HIGH`. El 9B acierta más problemas de grafos/DP.
7. Si nada funciona en 15 minutos, pasa a otro problema. La herramienta rinde mejor en problemas fáciles y medios; en los difíciles úsala para obtener una base sobre la que trabajar tú.

**Botón Cancel**: para la generación al instante (útil si ves en el pensamiento que va por mal camino). **Clear**: limpia todo para el siguiente problema.

---

## 5. Consejos que suben la tasa de acierto

- Pega el enunciado **en inglés** tal cual está; no lo traduzcas.
- Incluye siempre las **restricciones** (N ≤ 10^5, etc.): el modelo las usa para elegir la complejidad.
- Si el enunciado dice "T test cases", asegúrate de que el ejemplo pegado incluye la primera línea con T.
- Para salidas con decimales, revisa que el número de decimales del código coincida con el pedido.
- Python: si el juez es estricto con el tiempo y N ≥ 10^6, prueba JavaScript (Node es 3-10x más rápido en bucles). Cambia el selector y pulsa Solve.
- Problemas **interactivos** (los que leen y escriben por turnos) no están soportados: los tests no pueden verificarlos.
- No pulses Solve dos veces: el sistema atiende un problema a la vez y responderá "busy".

---

## 6. Cerrar

Cierra la ventana negra (o Ctrl + C en ella). El modelo se apaga solo y se borran los temporales. Espera a que la ventana desaparezca antes de sacar el USB. **Nunca saques el USB con la ventana abierta**: el modelo se lee desde ahí.

---

## 7. Problemas frecuentes

| Qué ves | Qué hacer |
|---|---|
| `Ningún perfil utilizable: necesita X GB libres, hay Y` | Cierra programas. Si sigue, `CodeSolver.bat --profile MEDIUM`. Con menos de 3 GB libres no arranca. |
| `Falló el arranque con vulkan` y sigue con cpu | Normal. Es el respaldo automático. |
| `Timeout esperando /health` | USB muy lento o antivirus escaneando el modelo. Espera y reintenta; segunda vez suele ser más rápido. |
| El navegador no abre | Escribe `http://127.0.0.1:8765/` a mano en Edge/Chrome/Firefox. |
| Barra superior en rojo, "backend unreachable" | La ventana negra se cerró. Vuelve a ejecutar `CodeSolver.bat`. |
| "busy: another solve is running" | Pulsa Cancel y espera 5 s. |
| Todo WRONG_ANSWER aunque el código parece bien | Revisa los tests extraídos (sección 4, punto 2). |
| Menos de 3 tok/s | Conecta el cargador, cierra otros programas, usa `--profile MEDIUM` y desmarca Thinking. |
| Windows/SmartScreen bloquea el `.bat` o `.exe` | Es política de la PC. Pregunta a los organizadores. No hay forma legítima de saltarla y la herramienta no lo intenta. |

Logs para diagnosticar: `logs\session_*.log` (el más reciente) y `logs\llama_*.log`.

---

## 8. Qué esperar (medido el 2026-09-19 desde el USB, laptop i9 en batería)

| | 4B (MEDIUM) | 9B (HIGH) |
|---|---|---|
| Carga inicial desde USB | 45 s | 2-4 min |
| Velocidad | 6.4 tok/s | 3.7 tok/s |
| Por intento | ~3-4 min | ~6-7 min |
| Acierto en el dataset de prueba (fáciles/medios) | 5 de 6 resueltos al primer intento en las dos corridas completadas hasta ahora; benchmark de 27 problemas en curso | sin medir |

En una PC de competencia típica sin GPU y con 4 núcleos espera 3-6 tok/s con el 4B. El 9B en CPU no es práctico salvo con GPU o CPU potente.

---

## 9. Resumen de una página (para imprimir)

```
ARRANCAR   doble clic CodeSolver.bat → esperar "LISTO" → navegador http://127.0.0.1:8765/
RESOLVER   pegar enunciado COMPLETO con ejemplos → Python → Solve → esperar 3-4 min
VERIFICAR  pastillas verdes = pasó los ejemplos → Copy code → enviar al juez
SI FALLA   1) revisar tests extraídos  2) corregir a mano + Run with input
           3) Solve otra vez (sin Thinking si es fácil)  4) añadir "Hint: ..."  5) otro problema
CERRAR     cerrar la ventana negra, esperar, sacar el USB
NUNCA      sacar el USB con la ventana abierta / pulsar Solve dos veces / esperar milagros en difíciles
```
