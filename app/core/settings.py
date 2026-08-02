from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_HOST: str = "http://localhost:11434"


settings = Settings()
