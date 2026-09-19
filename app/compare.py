"""Comparación de salidas al estilo de un juez: tolerante a espacios finales y CRLF, no al contenido."""
from __future__ import annotations

FLOAT_TOL = 1e-6


def normalize(text: str) -> list[str]:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _tokens_equal(a: str, b: str) -> bool:
    if a == b:
        return True
    try:
        fa, fb = float(a), float(b)
    except ValueError:
        return False
    return abs(fa - fb) <= FLOAT_TOL * max(1.0, abs(fa), abs(fb))


def compare(expected: str, actual: str) -> tuple[bool, str]:
    """Devuelve (ok, explicación). Primero comparación exacta por líneas, luego por tokens
    con tolerancia numérica (para problemas de salida flotante)."""
    e, a = normalize(expected), normalize(actual)
    if e == a:
        return True, "exact match"
    et, at = " ".join(e).split(), " ".join(a).split()
    if len(et) == len(at) and all(_tokens_equal(x, y) for x, y in zip(et, at)):
        return True, "token match (whitespace/float tolerance)"
    # explicación corta
    for i in range(max(len(e), len(a))):
        le = e[i] if i < len(e) else "<missing>"
        la = a[i] if i < len(a) else "<missing>"
        if le != la:
            return False, f"line {i + 1}: expected {le!r}, got {la!r}"
    return False, "outputs differ"
