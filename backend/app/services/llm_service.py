from typing import Any

import httpx

from app.core.config import get_settings


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def chat_completion(self, prompt: str) -> str | None:
        if not self.settings.openrouter_api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://whatsapp-ui-joaocat.duckdns.org",
            "X-Title": "whatsapp-testes",
        }
        payload: dict[str, Any] = {
            "model": self.settings.openrouter_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Voce resume evidencias de mensagens de WhatsApp de forma objetiva e em Portugues BR.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPError:
                # Nao quebra a busca semantica quando a LLM externa estiver indisponivel.
                return None

            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content")
