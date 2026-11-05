from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "HackerCoderAI"
    database_path: str = "data/hackercoderai.sqlite3"
    model_path: str = "data/models/Qwen2.5-3B-Instruct-abliterated-Q4_K_M.gguf"
    model_profile: str = "v4"
    n_ctx: int = 4096
    n_threads: int = 4
    max_tokens: int = 768

    @property
    def model_file(self) -> Path | None:
        path = Path(self.model_path).expanduser() if self.model_path else None
        return path if path and path.is_file() else None

settings = Settings()
