# Solución de problemas

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `Ningún perfil utilizable: falta models/...` | No se copió el modelo al USB | Copiar el `.gguf` a `models/` o forzar otro perfil: `CodeSolver.bat --profile LOW` |
| `necesita X GB libres, hay Y` | Poca RAM libre | Cerrar programas; usar `--profile MEDIUM` o `LOW` |
| `Falló el arranque con vulkan` y luego arranca con cpu | Driver Vulkan roto o GPU sin memoria | Normal, es el fallback. Para saltarlo: `CodeSolver.bat --cpu` |
| Timeout esperando /health | USB muy lento (USB 2.0) o antivirus escaneando el modelo | Esperar; subir `health_timeout_seconds` en config; copiar la carpeta al disco local si está permitido |
| El navegador no se abre | Navegador bloqueado o sin asociación | Abrir manualmente la URL impresa en la consola; o usar `CodeSolver.bat solve archivo.txt` |
| `backend unreachable` en la UI | El launcher se cerró | Volver a ejecutar `CodeSolver.bat` |
| Muy lento (< 3 tok/s) | Laptop en batería, CPU vieja, modelo 9B en CPU | Conectar a corriente; `--profile MEDIUM`; desmarcar "Thinking" en la UI |
| `busy: another solve is running` | Hay una resolución en curso | Pulsar Cancel y reintentar |
| Tests siempre WRONG_ANSWER aunque el código parece bien | Ejemplos mal extraídos del enunciado | Editar los tests en el panel "Sample tests" y volver a Solve |
| `No sample tests: code NOT verified` | El enunciado no tiene ejemplos reconocibles | Añadir un test manual con "+ add" |
| Queda un `llama-server.exe` en el Administrador de tareas | Cierre forzado de la ventana | El siguiente arranque lo cierra solo; o `taskkill /F /IM llama-server.exe` |
| Windows SmartScreen / política bloquea el `.exe` | Política de la institución | No se debe evadir. Consultar a los organizadores. |

Logs: `logs/session_*.log` (launcher y backend), `logs/llama_cpu.log` / `logs/llama_vulkan.log` (modelo).
