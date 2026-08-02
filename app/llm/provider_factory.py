import os

from app.llm.providers.fake import fake_provider
from app.llm.providers.ollama import ollama_provider


def get_provider():

    if os.getenv("LLM_PROVIDER") == "fake":
        return fake_provider

    return ollama_provider
