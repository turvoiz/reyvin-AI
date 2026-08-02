import time

from ollama import Client

from app.core.settings import settings
from app.core.models import (
    MODELS,
    DEFAULT_MODEL,
    KEEP_ALIVE,
    DEFAULT_CTX,
    DEFAULT_TEMPERATURE,
)

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
