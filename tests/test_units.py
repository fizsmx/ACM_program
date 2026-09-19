"""Tests unitarios sin LLM. Ejecutar:  runtime\\python\\python.exe -X utf8 tests\test_units.py -v"""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

import compare  # noqa: E402
import examples  # noqa: E402
import runners  # noqa: E402
from solver import extract_code  # noqa: E402

CF = """A. Sum
time limit per test 1 second

You are given n integers. Print their sum.

Input
The first line contains an integer n (1 ≤ n ≤ 10^5). The second line contains n integers a_i (|a_i| ≤ 10^9).

Output
Print one integer — the sum.

Examples
Input
3
1 2 3
Output
6

Input
1
-5
Output
-5

Note
In the first example the sum is 6.
"""

UVA = """Sample Input
2
1 2
3 4

Sample Output
3
7
"""

LEET = """Example 1:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

Example 2:
Input: nums = [3,2,4], target = 6
Output: [1,2]

Constraints:
2 <= nums.length <= 10^4
"""


class TestExamples(unittest.TestCase):
    def test_codeforces(self):
        t = examples.extract_examples(CF)
        self.assertEqual(len(t), 2)
        self.assertEqual(t[0], {"input": "3\n1 2 3\n", "expected": "6\n"})
        self.assertEqual(t[1], {"input": "1\n-5\n", "expected": "-5\n"})

    def test_uva(self):
        t = examples.extract_examples(UVA)
        self.assertEqual(t, [{"input": "2\n1 2\n3 4\n", "expected": "3\n7\n"}])

    def test_leetcode_inline(self):
        t = examples.extract_examples(LEET)
        self.assertEqual(len(t), 2)
        self.assertEqual(t[0]["input"], "nums = [2,7,11,15], target = 9\n")
        self.assertEqual(t[0]["expected"], "[0,1]\n")
        self.assertEqual(t[1]["expected"], "[1,2]\n")

    def test_no_examples(self):
        self.assertEqual(examples.extract_examples("Input\nAn integer n.\nOutput\nPrint n."), [])

    def test_llm_json(self):
        txt = 'Here: [{"input": "1\\n", "expected": "2\\n"}, {"input": "", "expected": "x"}]'
        self.assertEqual(examples.parse_llm_examples(txt), [{"input": "1\n", "expected": "2\n"}])


class TestCompare(unittest.TestCase):
    def test_exact_and_whitespace(self):
        self.assertTrue(compare.compare("6\n", "6")[0])
        self.assertTrue(compare.compare("a b\nc\n", "a b  \r\nc\r\n\n")[0])
        self.assertFalse(compare.compare("6\n", "7\n")[0])
        self.assertFalse(compare.compare("YES\n", "yes\n")[0])

    def test_floats(self):
        self.assertTrue(compare.compare("3.141592653\n", "3.141592654\n")[0])
        self.assertFalse(compare.compare("3.14\n", "3.15\n")[0])

    def test_line_count(self):
        ok, why = compare.compare("1\n2\n", "1\n")
        self.assertFalse(ok)
        self.assertIn("line 2", why)


class TestExtractCode(unittest.TestCase):
    def test_tagged(self):
        txt = "## Analysis\nx\n## Code\n```python\nprint(1)\n```\n"
        self.assertEqual(extract_code(txt, "python"), "print(1)\n")

    def test_prefers_language_block(self):
        txt = "```text\nsample\n```\n```javascript\nconsole.log(1)\n```"
        self.assertEqual(extract_code(txt, "javascript"), "console.log(1)\n")

    def test_none(self):
        self.assertIsNone(extract_code("no code here", "python"))


class TestRunners(unittest.TestCase):
    def _run(self, lang, code, stdin):
        d = runners.new_run_dir()
        p = runners.write_solution(lang, code, d)
        chk = runners.syntax_check(lang, p)
        if chk["status"] != "OK":
            return chk
        return runners.execute(lang, p, stdin, 5)

    def test_python_ok(self):
        r = self._run("python", "import sys\nprint(sum(map(int, sys.stdin.read().split())))\n", "1 2 3\n")
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["stdout"].strip(), "6")

    def test_js_ok(self):
        r = self._run("javascript", "const d=require('fs').readFileSync(0,'utf8').split(/\\s+/).filter(Boolean).map(Number);console.log(d.reduce((a,b)=>a+b,0));\n", "1 2 3\n")
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["stdout"].strip(), "6")

    def test_python_syntax_error(self):
        r = self._run("python", "print(\n", "")
        self.assertEqual(r["status"], "COMPILE_ERROR")

    def test_js_syntax_error(self):
        r = self._run("javascript", "console.log(\n", "")
        self.assertEqual(r["status"], "COMPILE_ERROR")

    def test_timeout(self):
        r = self._run("python", "while True: pass\n", "")
        self.assertEqual(r["status"], "TIME_LIMIT")

    def test_runtime_error(self):
        r = self._run("python", "print(1/0)\n", "")
        self.assertEqual(r["status"], "RUNTIME_ERROR")
        self.assertIn("ZeroDivisionError", r["stderr"])

    @classmethod
    def tearDownClass(cls):
        runners.cleanup_workspace()


if __name__ == "__main__":
    unittest.main()
