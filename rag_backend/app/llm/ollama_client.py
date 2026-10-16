import requests

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaClient:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.2,
    ) -> str:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
            },
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=180,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

        data = response.json()
        message = data.get("message", {})
        content = message.get("content", "")

        if not content:
            raise RuntimeError(
                f"Ollama returned no text: {data}"
            )

        return content.strip()