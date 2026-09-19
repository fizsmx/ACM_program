"""Extracción de ejemplos (input/expected) del enunciado por heurísticas de regex.

Formatos soportados (inglés y español):
  - "Sample Input [N]" / "Sample Output [N]"  (UVa, ICPC, Kattis)
  - "Entrada de ejemplo" / "Salida de ejemplo", "Entrada" / "Salida", "Ejemplo de entrada/salida"
  - "Examples"/"Ejemplos" seguido de bloques "Input"/"Output" o "Entrada"/"Salida"  (Codeforces)
  - "Example N:"/"Ejemplo N:" con "Input:"/"Entrada:" / "Output:"/"Salida:" inline  (LeetCode-like)
  - "Input"/"Entrada" / "Output"/"Salida" como encabezados de línea, filtrando prosa.
Si no se encuentra nada, el solver recurre al LLM (prompts/extract_examples.txt).
"""
from __future__ import annotations

import json
import re

# palabras clave de entrada/salida en inglés y español
_IN = r"sample\s+input|example\s+input|entrada\s+de\s+ejemplo|ejemplo\s+de\s+entrada|input|entrada"
_OUT = r"sample\s+output|example\s+output|salida\s+de\s+ejemplo|ejemplo\s+de\s+salida|output|salida"
_EXWORD = r"examples?|samples?|sample\s+tests?|test\s+cases?|ejemplos?|casos?\s+de\s+prueba|casos?\s+de\s+ejemplo"

_HDR = re.compile(
    r"^[ \t]*(?:#+\s*|\*\*)?(?P<kind>" + _IN + r"|" + _OUT + r")"
    r"(?:[ \t]*(?:#|№|n[°º])?[ \t]*\d+)?[ \t]*(?:\*\*)?[ \t]*:?[ \t]*(?P<inline>\S.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
_EXAMPLES_HDR = re.compile(r"^[ \t]*(?:#+\s*|\*\*)?(?:" + _EXWORD + r")\s*(?:\*\*)?\s*:?[ \t]*$",
                           re.IGNORECASE | re.MULTILINE)
_STOP_HDR = re.compile(
    r"^[ \t]*(?:#+\s*|\*\*)?(note|notes|explanation|constraints|hint|scoring|subtasks?"
    r"|nota|notas|explicaci[oó]n|restricciones|pista|subtareas?)\b",
    re.IGNORECASE)
# "Example 2:", "Ejemplo 3", "Test case 1", "Caso de prueba 2"...: separan ejemplos.
_EXAMPLE_N_HDR = re.compile(
    r"^[ \t]*(?:#+\s*|\*\*)?(?:" + _EXWORD + r")\s*(?:#|№|n[°º])?\s*\d*\s*(?:\*\*)?\s*:?[ \t]*$",
    re.IGNORECASE)
# Cualquier encabezado markdown con texto ("### Something") termina el bloque.
_MD_HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]+[A-Za-z]")
_FENCE = re.compile(r"^\s*```")


def _looks_like_prose(block: str) -> bool:
    lines = [ln for ln in block.splitlines() if ln.strip()]
    if not lines:
        return True
    long_sentences = sum(1 for ln in lines if len(ln.split()) >= 9 and re.search(r"[a-zA-Z]{3,}\s+[a-zA-Z]{3,}\s+[a-zA-Z]{3,}", ln))
    if long_sentences >= max(1, len(lines) // 2):
        return True
    # frases cortas de especificación: terminan en punto y tienen >= 2 palabras alfabéticas
    short_sentences = sum(1 for ln in lines if ln.rstrip().endswith(".") and len(re.findall(r"[A-Za-z]{2,}", ln)) >= 2)
    return short_sentences >= max(1, (len(lines) + 1) // 2)


def _cut_at_stop(block: str) -> str:
    out = []
    for ln in block.splitlines():
        if _STOP_HDR.match(ln) or _EXAMPLE_N_HDR.match(ln) or _MD_HEADING.match(ln):
            break
        out.append(ln)
    return "\n".join(out)


def _strip_fences(block: str) -> str:
    """Si el bloque contiene fences ``` balanceados, conserva solo su contenido (descarta la
    explicación en prosa que suele seguir a un ejemplo, p.ej. en AtCoder). Si están
    desbalanceados, solo elimina las líneas de fence."""
    lines = block.split("\n")
    fences = [i for i, ln in enumerate(lines) if _FENCE.match(ln)]
    if not fences:
        return block
    if len(fences) % 2:
        return "\n".join(ln for ln in lines if not _FENCE.match(ln))
    out: list[str] = []
    for a, b in zip(fences[0::2], fences[1::2]):
        out.extend(lines[a + 1:b])
    return "\n".join(out)


def _drop_trailing_prose(block: str) -> str:
    """Elimina párrafos finales (separados por línea en blanco) que parecen prosa explicativa."""
    paras = re.split(r"\n[ \t]*\n", block.strip("\n"))
    while len(paras) > 1 and _looks_like_prose(paras[-1]):
        paras.pop()
    return "\n\n".join(paras)


def _clean(block: str) -> str:
    block = _cut_at_stop(block)
    block = block.replace("\r\n", "\n").strip("\n")
    block = _strip_fences(block)
    block = _drop_trailing_prose(block)
    lines = [ln.rstrip() for ln in block.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def extract_examples(statement: str) -> list[dict]:
    text = statement.replace("\r\n", "\n")
    # Si existe un encabezado "Examples"/"Samples", ignorar todo lo anterior (especificación de Input/Output).
    m = _EXAMPLES_HDR.search(text)
    region = text[m.end():] if m else text
    heads = list(_HDR.finditer(region))
    items: list[tuple[str, str]] = []  # (kind, block)
    for i, h in enumerate(heads):
        k = h.group("kind").lower()
        kind = "input" if ("input" in k or "entrada" in k) else "output"
        inline = h.group("inline")
        end = heads[i + 1].start() if i + 1 < len(heads) else len(region)
        body = region[h.end():end]
        if inline:
            # formato inline: "Input: 3 4" o "Input: nums = [1,2]" — el resto del bloque puede continuar en líneas siguientes
            body = inline + ("\n" + body if body.strip() else "")
        items.append((kind, _clean(body)))
    tests: list[dict] = []
    i = 0
    while i < len(items) - 1:
        k1, b1 = items[i]
        k2, b2 = items[i + 1]
        if k1 == "input" and k2 == "output" and b1 and b2 and not _looks_like_prose(b1) and not _looks_like_prose(b2):
            tests.append({"input": b1 + "\n", "expected": b2 + "\n"})
            i += 2
        else:
            i += 1
    # dedupe conservando orden
    seen, uniq = set(), []
    for t in tests:
        key = (t["input"], t["expected"])
        if key not in seen:
            seen.add(key)
            uniq.append(t)
    return uniq


def parse_llm_examples(text: str) -> list[dict]:
    """Valida el JSON devuelto por el LLM: lista de {input, expected} con strings."""
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for it in data if isinstance(data, list) else []:
        if isinstance(it, dict) and isinstance(it.get("input"), str) and isinstance(it.get("expected"), str):
            inp, exp = it["input"].strip("\n"), it["expected"].strip("\n")
            if inp.strip() and exp.strip():
                out.append({"input": inp + "\n", "expected": exp + "\n"})
    return out
