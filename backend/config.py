from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MongoDB
    mongo_url: str
    db_name: str = "linkrecovery_db"
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    
    # JWT
    jwt_secret_key: str = "your-secret-key-here-replace-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Emergent LLM key for AI recommendations
    emergent_llm_key: str = ""
    
    # CORS
    cors_origins: str = "*"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()