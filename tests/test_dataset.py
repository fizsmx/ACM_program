"""Dataset de enunciados: comprueba el extractor de ejemplos y las soluciones de referencia.

Ejecutar:  runtime\\python\\python.exe -X utf8 tests\\test_dataset.py

Para cada tests/problems/*.md:
  (a) extract_examples devuelve tantos ejemplos como declara el comentario `<!-- samples: N -->`;
  (b) ni el input ni el expected contienen prosa (ninguna línea con más de 8 palabras alfabéticas);
  (c) tests/problems/solutions/pNNN.py pasa todos los ejemplos extraídos según app/compare.py.
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

import compare  # noqa: E402
import examples  # noqa: E402

PROBLEMS_DIR = os.path.join(ROOT, "tests", "problems")
SOLUTIONS_DIR = os.path.join(PROBLEMS_DIR, "solutions")
MAX_WORDS_PER_LINE = 8
_SAMPLES_RE = re.compile(r"<!--\s*samples\s*:\s*(\d+)\s*-->")


def _python_exe() -> str:
    embedded = os.path.join(ROOT, "runtime", "python", "python.exe")
    return embedded if os.path.exists(embedded) else sys.executable


def _run_solution(path: str, stdin: str) -> str:
    proc = subprocess.run(
        [_python_exe(), "-X", "utf8", "-I", path],
        input=stdin, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{os.path.basename(path)} exit {proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout


def _prose_lines(block: str) -> list[str]:
    return [ln for ln in block.splitlines() if len(re.findall(r"[A-Za-z]+", ln)) > MAX_WORDS_PER_LINE]


class TestDataset(unittest.TestCase):
    pass


def _make_test(md_path: str):
    name = os.path.basename(md_path)
    pid = name.split("_", 1)[0]
    sol_path = os.path.join(SOLUTIONS_DIR, f"{pid}.py")

    def test(self: unittest.TestCase):
        with open(md_path, encoding="utf-8") as fh:
            statement = fh.read()
        m = _SAMPLES_RE.search(statement)
        self.assertIsNotNone(m, f"{name}: falta el comentario <!-- samples: N -->")
        expected_count = int(m.group(1))
        tests = examples.extract_examples(statement)
        # (a) número de ejemplos
        self.assertEqual(len(tests), expected_count,
                         f"{name}: se esperaban {expected_count} ejemplos, se extrajeron {len(tests)}: {tests!r}")
        # (b) sin prosa y con terminador de línea
        for idx, t in enumerate(tests, 1):
            for key in ("input", "expected"):
                self.assertTrue(t[key].endswith("\n"), f"{name} ejemplo {idx}: {key} no termina en salto de línea")
                self.assertTrue(t[key].strip(), f"{name} ejemplo {idx}: {key} vacío")
                bad = _prose_lines(t[key])
                self.assertFalse(bad, f"{name} ejemplo {idx}: prosa en {key}: {bad!r}")
        # (c) la solución de referencia pasa los ejemplos
        self.assertTrue(os.path.exists(sol_path), f"{name}: falta la solución {sol_path}")
        for idx, t in enumerate(tests, 1):
            out = _run_solution(sol_path, t["input"])
            ok, why = compare.compare(t["expected"], out)
            self.assertTrue(ok, f"{name} ejemplo {idx}: {why}\ninput={t['input']!r}\nexpected={t['expected']!r}\ngot={out!r}")

    test.__name__ = f"test_{pid}_{os.path.splitext(name)[0].split('_', 1)[-1]}"
    return test


_problem_files = sorted(glob.glob(os.path.join(PROBLEMS_DIR, "*.md")))
if not _problem_files:
    raise RuntimeError(f"no hay enunciados en {PROBLEMS_DIR}")
for _p in _problem_files:
    _t = _make_test(_p)
    setattr(TestDataset, _t.__name__, _t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
