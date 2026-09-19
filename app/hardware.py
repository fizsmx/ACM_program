"""Detección de hardware sin dependencias externas (ctypes + stdlib). Windows y Linux."""
from __future__ import annotations

import ctypes
import os
import subprocess

import paths

if paths.IS_WIN:
    from ctypes import wintypes

    class _MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]


def _memory_gb_linux() -> tuple[float, float]:
    total = avail = 0.0
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1]) / 2**20  # kB -> GB
                elif line.startswith("MemAvailable:"):
                    avail = int(line.split()[1]) / 2**20
    except OSError:
        pass
    return total, avail


def memory_gb() -> tuple[float, float]:
    """(total_gb, free_gb)"""
    if not paths.IS_WIN:
        return _memory_gb_linux()
    st = _MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return 0.0, 0.0
    return st.ullTotalPhys / 2**30, st.ullAvailPhys / 2**30


def has_vulkan() -> bool:
    if paths.IS_WIN:
        try:
            ctypes.WinDLL("vulkan-1")
            return True
        except OSError:
            return False
    for lib in ("libvulkan.so.1", "libvulkan.so"):
        try:
            ctypes.CDLL(lib)
            return True
        except OSError:
            continue
    return False


def _gpu_names_linux(timeout: float = 4.0) -> list[str]:
    names: list[str] = []
    # 1) lspci si está disponible
    try:
        out = subprocess.run(["lspci"], capture_output=True, text=True, timeout=timeout)
        for line in out.stdout.splitlines():
            low = line.lower()
            if " vga " in low or "3d controller" in low or "display controller" in low:
                names.append(line.split(":", 2)[-1].strip())
    except Exception:
        pass
    if names:
        return names
    # 2) /sys/class/drm (nombres de dispositivo, best effort)
    try:
        import glob
        for card in glob.glob("/sys/class/drm/card[0-9]/device/uevent"):
            with open(card) as f:
                for line in f:
                    if line.startswith("DRIVER="):
                        names.append(line.strip().split("=", 1)[1])
    except Exception:
        pass
    return names


def gpu_names(timeout: float = 6.0) -> list[str]:
    """Best effort; devuelve [] si no se puede determinar."""
    if not paths.IS_WIN:
        return _gpu_names_linux(min(timeout, 4.0))
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join '|'"],
            capture_output=True, text=True, timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return [s.strip() for s in out.stdout.strip().split("|") if s.strip()]
    except Exception:
        return []


def detect() -> dict:
    total, free = memory_gb()
    logical = os.cpu_count() or 4
    return {
        "ram_total_gb": round(total, 1),
        "ram_free_gb": round(free, 1),
        "logical_cpus": logical,
        "vulkan": has_vulkan(),
        "gpus": gpu_names(),
    }


def recommended_threads(logical_cpus: int) -> int:
    # llama.cpp rinde mejor con hilos ~ núcleos físicos; sin esa info, usar la mitad de los lógicos (mín 2).
    return max(2, min(logical_cpus, max(2, logical_cpus // 2)))


if __name__ == "__main__":
    import json
    print(json.dumps(detect(), indent=2))
