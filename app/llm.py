"""Cliente mínimo (stdlib) para llama-server con API OpenAI-compatible y streaming SSE."""
from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, Iterator


class LLMError(RuntimeError):
    pass


class LlamaClient:
    def __init__(self, base_url: str, timeout: float = 600.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------ util
    def _post(self, path: str, body: dict, timeout: float | None = None):
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        return urllib.request.urlopen(req, timeout=timeout or self.timeout)

    def health(self) -> tuple[bool, str]:
        try:
            with urllib.request.urlopen(self.base_url + "/health", timeout=3) as r:
                return r.status == 200, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return False, f"{e.code}"
        except Exception as e:  # conexión rechazada, etc.
            return False, str(e)

    # ------------------------------------------------------------------ chat
    def chat(self, messages: list[dict], *, temperature=0.6, top_p=0.95, top_k=20,
             max_tokens=2048, reasoning_budget: int = -1, stream: bool = True,
             cancel: threading.Event | None = None) -> Iterator[tuple[str, str]]:
        """Genera pares (canal, texto) con canal ∈ {'reasoning', 'content'}.

        En modo no-stream genera un único par por canal. Al terminar, `self.last_timings`
        contiene los timings del servidor si los envió.
        """
        body = {
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_tokens": max_tokens,
            "stream": stream,
            "reasoning_format": "deepseek",
            "cache_prompt": True,
        }
        # NOTA: llama-server b11046 ignora "reasoning_budget" por petición; el límite real lo pone el
        # flag --reasoning-budget con el que el launcher arranca el servidor. Aquí solo se puede apagar.
        if reasoning_budget == 0:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        self.last_timings = None
        try:
            resp = self._post("/v1/chat/completions", body)
        except urllib.error.HTTPError as e:
            raise LLMError(f"llama-server HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")
        except Exception as e:
            raise LLMError(f"No se pudo contactar llama-server: {e}")

        with resp:
            if not stream:
                obj = json.loads(resp.read().decode("utf-8"))
                self.last_timings = obj.get("timings")
                msg = obj["choices"][0]["message"]
                if msg.get("reasoning_content"):
                    yield "reasoning", msg["reasoning_content"]
                yield "content", msg.get("content") or ""
                return
            for raw in resp:
                if cancel is not None and cancel.is_set():
                    break
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if "timings" in obj:
                    self.last_timings = obj["timings"]
                for ch in obj.get("choices", []):
                    delta = ch.get("delta") or {}
                    if delta.get("reasoning_content"):
                        yield "reasoning", delta["reasoning_content"]
                    if delta.get("content"):
                        yield "content", delta["content"]

    def complete_text(self, messages: list[dict], on_token: Callable[[str, str], None] | None = None,
                      **kw) -> tuple[str, str, float]:
        """Devuelve (reasoning, content, segundos). Llama a on_token(canal, texto) por fragmento."""
        t0 = time.time()
        reasoning, content = [], []
        gen = self.chat(messages, **kw)
        try:
            for channel, text in gen:
                (reasoning if channel == "reasoning" else content).append(text)
                if on_token:
                    on_token(channel, text)
        finally:
            # Cerrar el generador cierra la respuesta HTTP (with resp:) y llama-server aborta la generación.
            gen.close()
        return "".join(reasoning), "".join(content), time.time() - t0

    def benchmark(self, n_tokens: int = 48) -> dict:
        """Mide tokens/s de generación y de prompt con una petición corta sin thinking."""
        msgs = [{"role": "user", "content": "Count from 1 to 40 separated by commas. Output only the numbers."}]
        t0 = time.time()
        list(self.chat(msgs, temperature=0.0, max_tokens=n_tokens, reasoning_budget=0, stream=False))
        dt = time.time() - t0
        t = self.last_timings or {}
        return {
            "gen_tps": round(float(t.get("predicted_per_second") or (n_tokens / dt)), 1),
            "prompt_tps": round(float(t.get("prompt_per_second") or 0.0), 1),
            "seconds": round(dt, 1),
        }
