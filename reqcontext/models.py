"""Small JSON adapter for a user-configured chat-completions endpoint."""
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class ChatModel:
    def __init__(self, *, base_url, model, api_key=None, timeout=60, max_tokens=3000):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Use a valid HTTP(S) API base URL without embedded credentials")
        if not isinstance(model, str) or not model.strip() or timeout <= 0:
            raise ValueError("Model name and a positive timeout are required")
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model, self.api_key, self.timeout, self.max_tokens = model, api_key, timeout, max_tokens

    @classmethod
    def from_env(cls):
        base_url, model = os.environ.get("REQCONTEXT_BASE_URL"), os.environ.get("REQCONTEXT_MODEL")
        if not base_url or not model:
            raise ValueError("Configure REQCONTEXT_BASE_URL and REQCONTEXT_MODEL, or pass a model callable. Use --retrieval-only for source search without interpretation.")
        return cls(base_url=base_url, model=model, api_key=os.environ.get("REQCONTEXT_API_KEY"))

    def __call__(self, payload):
        # Trusted instructions and untrusted task/source data use different messages.
        instruction = payload["instruction"]
        data = {k: v for k, v in payload.items() if k != "instruction"}
        body = json.dumps({"model": self.model, "messages": [
            {"role": "system", "content": instruction},
            {"role": "user", "content": json.dumps(data)}],
            "response_format": {"type": "json_object"}, "max_tokens": self.max_tokens}).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        with urlopen(Request(self.url, data=body, headers=headers), timeout=self.timeout) as response:
            content = response.read(2_000_001)
        if len(content) > 2_000_000:
            raise ValueError("Model response exceeds transport limit")
        envelope = json.loads(content)
        self.last_usage = envelope.get("usage")
        result = json.loads(envelope["choices"][0]["message"]["content"])
        if not isinstance(result, dict):
            raise ValueError("Model must return a JSON object")
        return result
