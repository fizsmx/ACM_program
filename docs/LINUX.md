# CodeSolver en Linux (Ubuntu)

El mismo USB funciona en Windows y en Ubuntu. No hay que reformatear ni tener dos USB.

## 1. El formato del USB (exFAT) no se toca

exFAT lo reconoce Ubuntu moderno (22.04 y posteriores) de forma automática al conectar el USB.
No reformatees a ext4: perderias todo lo que ya esta y Windows dejaria de leerlo. exFAT es lo correcto para usar el USB en las dos plataformas.

## 2. Preparar el USB con los binarios de Linux (una sola vez, en la maquina de desarrollo)

En la maquina donde armas el USB (con Internet):

```
python3 tools/fetch_deps.py --linux                       # baja llama.cpp, Python y Node de Linux
python3 tools/package.py --dest /ruta/al/USB/CodeSolver --platform both --models 4b,9b
```

- `--platform both` deja en el USB los binarios de Windows y de Linux (por eso corre en ambos).
- `--platform linux` copiaria solo lo de Linux; `--platform win` solo lo de Windows.
- Si armas el USB desde Windows, es lo mismo: `python tools\package.py --dest D:\CodeSolver --platform both --models 4b,9b`.

## 3. Arrancar en la maquina Ubuntu de la competencia

1. Conecta el USB. Ubuntu lo monta solo (normalmente en `/media/<tu-usuario>/<nombre-del-USB>`).
2. Abre una terminal y entra a la carpeta:
   ```
   cd /media/$USER/*/CodeSolver     # ajusta el nombre del USB si hace falta
   ```
3. Arranca:
   ```
   bash CodeSolver.sh
   ```
   (o `chmod +x CodeSolver.sh && ./CodeSolver.sh`).
4. Espera el mensaje `LISTO` y abre en el navegador **http://127.0.0.1:8765/** (se intenta abrir solo).
5. Pega el enunciado, elige Python, pulsa **Solve**. Igual que en Windows.
6. Para cerrar: `Ctrl+C` en la terminal. El modelo se apaga solo.

Modo consola de respaldo (si no hay navegador):
```
bash CodeSolver.sh solve problema.txt --lang python --out solucion.py
```

## 4. Si los binarios no ejecutan ("Permission denied" o "noexec")

Los gestores de archivos de Ubuntu a veces montan el USB con la opcion `noexec`, que impide ejecutar programas desde el USB **aunque tengan permiso de ejecucion**. Esto NO se debe evadir; es una politica del sistema.

Como saber si es tu caso:
```
mount | grep -i codesolver      # o el nombre/punto de montaje del USB
```
Si en la linea aparece `noexec`, la solucion legitima es copiar la carpeta al disco local y correrla desde ahi:
```
cp -r /media/$USER/*/CodeSolver ~/CodeSolver
cd ~/CodeSolver
./CodeSolver.sh
```
Copiar tus propios archivos a tu carpeta personal es una operacion normal de usuario: no necesita administrador ni evade ningun control. Si aun asi algo esta bloqueado, consulta a los organizadores.

## 5. Requisitos de la maquina Ubuntu

- Ubuntu 22.04 o mas nuevo (glibc reciente). Los binarios portables incluyen su propio Python, Node y llama.cpp; no hace falta instalar nada.
- RAM libre: 5 GB para el modelo 4B (perfil MEDIUM), 10 GB para el 9B (HIGH). El launcher elige solo.
- GPU (opcional): si esta el paquete `libvulkan1` y hay driver Vulkan, se usa la GPU automaticamente. Si no, corre en CPU (mas lento pero funciona). El launcher lo detecta y avisa.
- No requiere permisos de administrador, ni Internet, ni instalar paquetes.

## 6. Diferencias con Windows

Ninguna en el uso: misma interfaz, mismos botones, mismos modos (Competition/Developer), mismo `config/config.json`. Solo cambia el lanzador (`CodeSolver.sh` en vez de `CodeSolver.bat`) y los binarios que usa por debajo. Todo se escribe dentro de `CodeSolver/workspace` y `CodeSolver/logs`.

## 7. Reglas

Usa la herramienta solo por la via que autoricen los organizadores. CodeSolver no requiere administrador, no se conecta a Internet y no intenta saltarse controles del sistema (politicas de montaje, permisos, antivirus). Si la maquina impide ejecutar desde USB, la unica via valida es copiar la carpeta al disco con permiso, no evadir la restriccion.
