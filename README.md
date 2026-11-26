<div align="center">

# CodeSolver Offline

**Portable, 100% offline competitive programming AI assistant** powered by local LLMs (**`llama.cpp` + GGUF models** with automatic Vulkan GPU / CPU acceleration), automated sample-test extraction, sandboxed code execution, and an iterative **self-repair & rethink loop** for Python and JavaScript.

[![Python 3.12](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF_Local_LLM-38B2AC?style=for-the-badge&logo=meta&logoColor=white)](https://github.com/ggerganov/llama.cpp)
[![Vulkan / CPU](https://img.shields.io/badge/Inference-Vulkan_GPU_%2F_CPU-0F4C5C?style=for-the-badge)](https://www.vulkan.org/)
[![Zero Dependencies](https://img.shields.io/badge/Zero_Install-USB_Portable-161B22?style=for-the-badge)](https://github.com/fizsmx/ACM_program)
[![License: MIT](https://img.shields.io/badge/License-MIT-38B2AC?style=for-the-badge)](./LICENSE)

</div>

---

## How It Works (Solve → Test → Repair → Rethink)

Every generated solution is strictly syntax-checked and executed against the problem's sample inputs inside the bundled portable runtime — a solution is **never** marked `PASS` unless it passes the extracted examples.

```mermaid
flowchart TD
  A["Problem Statement (Codeforces / UVa / LeetCode)"] --> B["Example Extractor (Regex + LLM Fallback)"]
  B --> C["Local LLM Inference (llama.cpp GGUF · Qwen3.5 4B/9B)"]
  C --> D["Code Extraction & Syntax Validation"]
  D --> E["Sandboxed Runner (Portable Python 3.12 / Node 24 + Timeout)"]
  E -->|"All Samples Match"| F["PASS — Verified Solution Ready to Copy"]
  E -->|"Mismatch / Runtime Error"| G{"Attempts < max_repair_attempts?"}
  G -->|"Yes"| H["Repair Prompt (Input, Expected, Actual, Stderr)"]
  H --> C
  G -->|"No"| I["Rethink Prompt (Alternative Algorithm Approach)"]
  I --> C
```

---

## Key Features

- **100% Offline & Zero-Install Portability** — Runs directly from a local folder or USB drive with embedded **Python 3.12**, **Node 24**, and **`llama.cpp`** binaries (no admin privileges or Internet required).
- **Hardware-Aware Profile Auto-Selection** — Automatically detects available free RAM and Vulkan GPU support to select between `MEDIUM` (4B model, ~5 GB RAM) and `HIGH` (9B model, ~10 GB RAM).
- **Zero-Framework Architecture** — Backend written purely with the Python Standard Library (`app/`) and a lightweight Vanilla HTML/JS web UI (`web/`) served on `http://127.0.0.1:8765/`.
- **Web UI + CLI Fallback** — Paste statements into the browser UI or invoke headless solving straight from the terminal.
- **Automated Unit Tests** — Includes 17 offline unit tests (`tests/test_units.py`) validating example parsing, output comparison, runners, and code extraction without requiring a loaded LLM.

---

## Repository Layout

| Directory / File | Purpose |
| :--- | :--- |
| `app/` | Zero-dependency Python backend (server, example parser, solver loop, sandboxed runners) |
| `web/` | Lightweight local web interface (Vanilla HTML/CSS/JS) |
| `prompts/` | Structured prompts (`solve`, `repair`, `rethink`, `extract_examples`) |
| `config/config.json` | Hardware profiles, timeouts, ports, and sampling configuration |
| `tests/` | Offline unit test suite (`test_units.py`) and benchmark problems |
| `tools/` | Developer utilities (`fetch_deps.py` to bundle `llama.cpp`, runtimes & GGUF models; `bench.py`) |
| `CodeSolver.bat` / `CodeSolver.sh` | Cross-platform one-click launchers |

---

## Quick Start

### 1. Prepare Portable Bundle (Development Machine with Internet)

```bash
# Download llama.cpp, portable Python/Node runtimes, and Qwen3.5 9B/4B GGUF models
python tools/fetch_deps.py

# Optional extra models
python tools/fetch_deps.py --only coder7b,model2b

# Run the offline unit test suite (no LLM required)
python -X utf8 tests/test_units.py -v
```

### 2. Offline Usage

- **Web UI:** Run `CodeSolver.bat` (Windows) or `./CodeSolver.sh` (Linux/macOS), open `http://127.0.0.1:8765/`, paste a statement, pick Python or JavaScript, and press **Solve** (`Ctrl + Enter`).
- **CLI Mode:**

```bash
CodeSolver.bat solve problem.txt --lang python --out solution.py
```

---

## Ethics & Fair Use

This tool does not hide processes or bypass system/proctoring restrictions. Always verify that offline assistants are permitted under the rules of your event or practice environment before use.

See also [CodeSolver_Plan_Maestro.md](./CodeSolver_Plan_Maestro.md) and [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md).

---

## License

Released under the [MIT License](./LICENSE).

<div align="center">
  Built by <a href="https://github.com/fizsmx"><strong>Fisbert Chavez (@fizsmx)</strong></a>
</div>
