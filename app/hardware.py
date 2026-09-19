"""Detección de hardware sin dependencias externas (ctypes + stdlib)."""
from __future__ import annotations

import ctypes
import os
import subprocess
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


def memory_gb() -> tuple[float, float]:
    """(total_gb, free_gb)"""
    st = _MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
        return 0.0, 0.0
    return st.ullTotalPhys / 2**30, st.ullAvailPhys / 2**30


def has_vulkan() -> bool:
    try:
        ctypes.WinDLL("vulkan-1")
        return True
    except OSError:
        return False


def gpu_names(timeout: float = 6.0) -> list[str]:
    """Best effort; devuelve [] si PowerShell no está disponible o tarda demasiado."""
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
