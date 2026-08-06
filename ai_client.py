"""Free text and image generation.

Text has two selectable backends (``AIClient(backend=...)``):

- **g4f** (GPT4Free) -- keyless. It routes across community providers, so any one
  being down is normal; ``chat()`` retries across a small model list. Convenient
  but flaky and sometimes slow.
- **groq** -- the Groq API, free on a personal key from console.groq.com. Fast and
  reliable; OpenAI-compatible, so ``chat()`` POSTs to their ``/chat/completions``
  and retries across `GROQ_MODELS`. The chosen backend and key persist via
  ``save_ai_config`` / ``load_ai_config`` (``ai_config.json``, generated not
  checked in; ``GROQ_API_KEY`` in the environment is the default key).

Images always come from **Pollinations** (``GET image.pollinations.ai/prompt/…`` →
JPEG, keyless); its keyless *text* endpoint is paywalled, hence g4f/groq for text.

Everything degrades gracefully: a failed call raises ``AIError`` with a readable
message, and ``try_image`` returns ``None`` rather than raising, so a document is
still produced when only the illustration service is briefly unavailable.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from io import BytesIO
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

IMAGE_ENDPOINT = "https://image.pollinations.ai/prompt/"
USER_AGENT = "Mozilla/5.0 (compatible; research document exporter/1.0)"

# Text backends. g4f is keyless but flaky; Groq is fast and reliable on a free API
# key (https://console.groq.com). Images always come from Pollinations.
BACKENDS = ("g4f", "groq")
G4F_MODELS = ("gpt-4o-mini", "gpt-4o", "gpt-4", "llama-3.1-70b")
GROQ_MODELS = ("llama-3.3-70b-versatile", "llama-3.1-8b-instant")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

#: Persisted backend choice + key (generated, not checked in). The default key
#: comes from the environment, then a local .env file next to this module.
AI_CONFIG_FILE = Path(__file__).with_name("ai_config.json")
ENV_FILE = Path(__file__).with_name(".env")


def _dotenv() -> dict[str, str]:
    """Parse ``KEY=VALUE`` lines from a local .env (no dependency)."""
    values: dict[str, str] = {}
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                values[key.strip()] = val.strip().strip('"').strip("'")
        except OSError:
            pass
    return values


def default_groq_key() -> str:
    """Groq key from the environment, else the local .env file."""
    return os.environ.get("GROQ_API_KEY") or _dotenv().get("GROQ_API_KEY", "")


class AIError(RuntimeError):
    """A generation call failed after retries."""


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset({"GET"}))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = USER_AGENT
    return session


def load_ai_config() -> dict:
    """Return {'backend', 'groq_api_key'}.

    A Groq key found in the environment or .env makes **Groq the default engine**;
    a saved ``ai_config.json`` (the user's last GUI choice) then overrides both.
    """
    key = default_groq_key()
    cfg = {"backend": "groq" if key else "g4f", "groq_api_key": key}
    if AI_CONFIG_FILE.exists():
        try:
            data = json.loads(AI_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if data.get("backend") in BACKENDS:
                    cfg["backend"] = data["backend"]
                if data.get("groq_api_key"):
                    cfg["groq_api_key"] = data["groq_api_key"]
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save_ai_config(backend: str, groq_api_key: str) -> None:
    data = {"backend": backend if backend in BACKENDS else "g4f",
            "groq_api_key": (groq_api_key or "").strip()}
    tmp = AI_CONFIG_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(AI_CONFIG_FILE)


class AIClient:
    def __init__(self, backend: str = "g4f", groq_api_key: str | None = None,
                 session: requests.Session | None = None,
                 models: tuple[str, ...] | None = None) -> None:
        self.backend = backend if backend in BACKENDS else "g4f"
        self.groq_api_key = (groq_api_key or "").strip()
        self.session = session or make_session()
        self.models = models or (GROQ_MODELS if self.backend == "groq" else G4F_MODELS)
        self._g4f_client = None

    # -------------------------------------------------------------------- text
    def chat(self, prompt: str, system: str | None = None, timeout: int = 180) -> str:
        """Return the assistant's reply from the selected backend."""
        if self.backend == "groq":
            return self._chat_groq(prompt, system, timeout)
        return self._chat_g4f(prompt, system, timeout)

    def _g4f(self):
        """Lazily construct the g4f client (import is slow, ~seconds)."""
        if self._g4f_client is None:
            try:
                from g4f.client import Client
            except ImportError as exc:  # pragma: no cover - depends on install
                raise AIError("g4f is not installed. Run 'pip install g4f'.") from exc
            self._g4f_client = Client()
        return self._g4f_client

    def _chat_g4f(self, prompt: str, system: str | None, timeout: int) -> str:
        client = self._g4f()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_error = "Unknown error"
        for model in self.models:
            for attempt in range(2):
                try:
                    response = client.chat.completions.create(
                        model=model, messages=messages, web_search=False, timeout=timeout)
                    content = (response.choices[0].message.content or "").strip()
                    if content:
                        return content
                    last_error = "Empty response"
                except Exception as exc:  # g4f raises many provider-specific types
                    last_error = f"{type(exc).__name__}: {exc}"[:120]
                    time.sleep(1.5)
        raise AIError(f"Text generation failed (g4f): {last_error}")

    def _chat_groq(self, prompt: str, system: str | None, timeout: int) -> str:
        if not self.groq_api_key:
            raise AIError("A Groq API key is required. Enter it on the Generate tab.")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        headers = {"Authorization": f"Bearer {self.groq_api_key}",
                   "Content-Type": "application/json"}
        last_error = "Unknown error"
        for model in self.models:
            for attempt in range(3):
                try:
                    response = self.session.post(
                        GROQ_ENDPOINT, headers=headers, timeout=timeout,
                        json={"model": model, "messages": messages, "temperature": 0.7})
                except requests.RequestException as exc:
                    last_error = f"Connection failed: {exc}"[:120]
                    time.sleep(2)
                    continue
                if response.status_code == 401:
                    raise AIError("The Groq API key is invalid.")
                if response.status_code == 404:
                    last_error = f"Model not found: {model}"
                    break  # try the next model
                if response.status_code == 429:
                    last_error = "Groq rate limit (429)"
                    time.sleep(5)
                    continue
                if response.status_code != 200:
                    last_error = f"HTTP {response.status_code}: {response.text[:80]}"
                    time.sleep(2)
                    continue
                try:
                    content = (response.json()["choices"][0]["message"]["content"] or "").strip()
                except (ValueError, KeyError, IndexError) as exc:
                    last_error = f"Failed to parse response: {exc}"
                    continue
                if content:
                    return content
                last_error = "Empty response"
        raise AIError(f"Text generation failed (Groq): {last_error}")

    # ------------------------------------------------------------------- image
    def image(self, prompt: str, width: int = 768, height: int = 512,
              seed: int | None = None, timeout: int = 120) -> BytesIO:
        """Return a generated image as a seekable BytesIO (JPEG)."""
        url = IMAGE_ENDPOINT + urllib.parse.quote(prompt, safe="")
        params = {"width": width, "height": height, "nologo": "true"}
        if seed is not None:
            params["seed"] = seed
        try:
            response = self.session.get(url, params=params, timeout=timeout)
        except requests.RequestException as exc:
            raise AIError(f"Image generation connection failed: {exc}") from exc
        if response.status_code != 200:
            raise AIError(f"Image generation failed (HTTP {response.status_code})")
        if not response.headers.get("Content-Type", "").startswith("image"):
            raise AIError("Response is not an image")
        buffer = BytesIO(response.content)
        buffer.seek(0)
        return buffer

    def try_image(self, prompt: str, **kwargs) -> BytesIO | None:
        """Image generation that returns None instead of raising.

        Illustrations are a nice-to-have; a document should still be produced when
        the image service is briefly unavailable.
        """
        for attempt in range(2):
            try:
                return self.image(prompt, **kwargs)
            except AIError:
                if attempt == 0:
                    time.sleep(2)
        return None
