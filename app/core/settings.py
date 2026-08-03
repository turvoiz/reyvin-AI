from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_HOST: str = "http://localhost:11434"
    WORKSPACE_ROOT: str = "."
    API_KEY: str = ""


settings = Settings()
