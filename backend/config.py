from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    jwt_secret_key: str = os.getenv("SESSION_SECRET", "your-secret-key-here-replace-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
