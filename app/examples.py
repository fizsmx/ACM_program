"""Extracción de ejemplos (input/expected) del enunciado por heurísticas de regex.

Formatos soportados:
  - "Sample Input [N]" / "Sample Output [N]"  (UVa, ICPC, Kattis)
  - "Examples" seguido de bloques "Input" / "Output"  (Codeforces)
  - "Example N:" con "Input: ..." / "Output: ..." inline  (LeetCode / AtCoder-like)
  - "Input" / "Output" como encabezados de línea en cualquier parte, filtrando prosa.
Si no se encuentra nada, el solver recurre al LLM (prompts/extract_examples.txt).
"""
from __future__ import annotations

import json
import re

_HDR = re.compile(
    r"^[ \t]*(?:#+\s*|\*\*)?(?P<kind>sample\s+input|sample\s+output|example\s+input|example\s+output|input|output)"
    r"(?:[ \t]*(?:#|№)?[ \t]*\d+)?[ \t]*(?:\*\*)?[ \t]*:?[ \t]*(?P<inline>\S.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
_EXAMPLES_HDR = re.compile(r"^[ \t]*(?:#+\s*|\*\*)?(examples?|samples?|sample\s+tests?|test\s+cases?)\s*(?:\*\*)?\s*:?[ \t]*$",
                           re.IGNORECASE | re.MULTILINE)
_STOP_HDR = re.compile(r"^[ \t]*(?:#+\s*|\*\*)?(note|notes|explanation|constraints|hint|scoring|subtasks?)\b",
                       re.IGNORECASE)


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
        if _STOP_HDR.match(ln):
            break
        out.append(ln)
    return "\n".join(out)


def _clean(block: str) -> str:
    block = _cut_at_stop(block)
    block = block.replace("\r\n", "\n").strip("\n")
    # quitar fences markdown
    block = re.sub(r"^\s*```[a-zA-Z]*\s*$", "", block, flags=re.MULTILINE)
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
        kind = "input" if "input" in h.group("kind").lower() else "output"
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
