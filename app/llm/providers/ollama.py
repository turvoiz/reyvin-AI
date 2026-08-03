import time

from ollama import Client

from app.core.models import (
    DEFAULT_CTX,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    KEEP_ALIVE,
    MODELS,
)
from app.core.settings import settings

client = Client(host=settings.OLLAMA_HOST)


class OllamaProvider:
    def chat(
        self,
        model: str,
        message: str,
        thinking: bool = False,
    ):

        real_model = MODELS.get(model, MODELS[DEFAULT_MODEL])

        start = time.perf_counter()

        response = client.chat(
            model=real_model,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            think=thinking,
            keep_alive=KEEP_ALIVE,
            options={
                "temperature": DEFAULT_TEMPERATURE,
                "num_ctx": DEFAULT_CTX,
            },
        )

        elapsed = round((time.perf_counter() - start) * 1000)

        return {
            "response": response.message.content,
            "elapsed_ms": elapsed,
        }


ollama_provider = OllamaProvider()
