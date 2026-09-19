# CodeSolver en USB

## 1. Preparar el USB (máquina de desarrollo, una sola vez)

Requisitos del USB: 10 GB libres para 4B + 9B (3.5 GB si solo va el 4B). Formato exFAT o NTFS (FAT32 no admite archivos > 4 GB, el 9B no cabría). USB 3.x recomendado: el modelo se lee entero al arrancar.

```
python tools\package.py --dest D:\CodeSolver --models 4b,9b
```

- Es incremental: la primera vez copia todo; las siguientes solo lo que cambió (los modelos se saltan si el tamaño coincide). Vuelve a ejecutarlo después de cada cambio en `app/`, `web/`, `prompts/` o `config/`.
- Excluye `.git`, descargas, logs, temporales y la basura de npm. Genera `MANIFEST.txt` con tamaños y sha256.
- `--models 4b` copia solo el modelo de 2.7 GB (suficiente para PCs de 8 GB de RAM). `--without-tests` omite `tests/`.
- Tiempo medido en un USB 2.0/3.0 lento (escritura ~13-27 MB/s): 8.5 GB en 640 s (~11 min).

Cambia `D:` por la letra que tenga el USB en tu máquina. La letra no importa para el programa: todas las rutas son relativas a la carpeta `CodeSolver`.

## 2. Arrancar en la PC de la competencia

1. Conecta el USB. Abre la carpeta `CodeSolver` (la letra puede ser D:, E:, F:… da igual).
2. Doble clic en `CodeSolver.bat`. Se abre una ventana negra; no la cierres mientras uses el programa.
3. El launcher detecta RAM/GPU, elige el modelo y lo carga. Cuando aparece el recuadro `LISTO → http://127.0.0.1:8765/`, se abre el navegador solo. Si no se abre, escribe esa dirección en cualquier navegador (Edge siempre está en Windows).
4. Pega el enunciado, elige el lenguaje, pulsa **Solve**, espera, **Copy code**.
5. Al terminar, cierra la ventana negra: el modelo se apaga solo y los temporales se limpian.

Opciones útiles (escribir en una consola `cmd` dentro de la carpeta):

```
CodeSolver.bat --profile MEDIUM     fuerza el modelo 4B (más rápido)
CodeSolver.bat --profile HIGH       fuerza el 9B (mejor, ~2x más lento)
CodeSolver.bat --cpu                no usar GPU/Vulkan
CodeSolver.bat solve prob.txt --lang python --out sol.py    modo consola (si el navegador está bloqueado)
```

## 3. Qué esperar (tiempos medidos el 2026-09-19 desde el USB, laptop i9-13900H con Iris Xe, en batería)

| | 4B (MEDIUM) | 9B (HIGH) |
|---|---|---|
| Carga del modelo desde USB (primera vez, en frío) | 45 s | ~2-4 min estimado (14 s medidos, pero con el archivo aún en caché del sistema tras copiarlo) |
| Generación | 6.7 tok/s | 3.7 tok/s |
| Por intento (768 tokens de pensamiento + código) | ~3 min 10 s medidos (p001: PASS 2/2 al primer intento) | ~6 min 30 s estimados |

En una PC de competencia típica (4 núcleos, sin GPU, 8 GB) el 4B rondará 3-6 tok/s: cuenta 3-5 minutos por problema. El 9B en CPU sin GPU dedicada queda por debajo de 2-3 tok/s: **no recomendado** salvo que la PC tenga GPU con Vulkan o CPU potente conectada a corriente. El launcher muestra los tok/s reales y la estimación por intento al arrancar; si es mala, cierra y relanza con `--profile MEDIUM`.

Todo se escribe dentro de `CodeSolver\workspace` y `CodeSolver\logs` en el propio USB. En `C:` no se crea nada (verificado).

## 4. Qué NO hacer

- No extraigas el USB con la ventana negra abierta: el modelo se lee desde el USB y el programa se caerá.
- No lo ejecutes desde dentro de un ZIP ni desde una carpeta sincronizada (OneDrive/Drive): copia la carpeta entera.
- No cierres el navegador pensando que apaga el programa: lo que apaga todo es cerrar la ventana negra (o Ctrl+C en ella).
- No uses FAT32 si llevas el 9B.
- No intentes saltarte políticas de la PC (SmartScreen, AppLocker, antivirus): si la política bloquea el `.exe` o el `.bat`, consulta a los organizadores. El programa no requiere permisos de administrador ni Internet, pero sí poder ejecutar programas desde el USB.

## 5. Si algo falla

Ver `docs/TROUBLESHOOTING.md`. Los logs de la sesión están en `CodeSolver\logs\session_*.log` y `llama_*.log` en el USB.
