from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI-Powered Website Link Analysis API"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    request_timeout_seconds: int = 15
    max_extracted_chars: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()