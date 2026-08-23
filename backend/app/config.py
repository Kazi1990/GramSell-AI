from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = Field(min_length=1)
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    google_genai_use_vertexai: bool = True
    gemini_model: str = "gemini-3.1-flash-lite"
    vertex_decision_model: str = "gemini-3.1-flash-lite"
    google_maps_api_key: str | None = None
    maps_mcp_url: str = "https://mapstools.googleapis.com/mcp"
    maps_timeout_seconds: float = Field(default=30.0, ge=5, le=120)
    maps_read_timeout_seconds: float = Field(default=90.0, ge=10, le=300)
    google_weather_api_key: str | None = None
    google_cloud_storage_bucket: str | None = None
    frontend_origin: str = "http://localhost:3000"
    max_agent_message_chars: int = Field(default=12000, ge=100, le=50000)
    max_request_body_bytes: int = Field(default=1048576, ge=16384, le=10485760)
    write_api_key_required: bool = False
    internal_api_key: str | None = None
    auth_token_secret: str | None = None
    auth_token_ttl_seconds: int = Field(default=86400, ge=900, le=604800)
    model_timeout_seconds: float = Field(default=45.0, ge=5, le=120)
    weather_timeout_seconds: float = Field(default=15.0, ge=3, le=60)
    database_pool_size: int = Field(default=5, ge=1, le=30)
    database_max_overflow: int = Field(default=10, ge=0, le=50)
    social_publish_providers: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.app_env.lower() == "production":
            if not self.google_genai_use_vertexai:
                raise ValueError("Vertex AI must be enabled in production.")
            if not self.google_cloud_project:
                raise ValueError("GOOGLE_CLOUD_PROJECT is required in production.")
            if not self.internal_api_key and not self.auth_token_secret:
                raise ValueError("AUTH_TOKEN_SECRET or INTERNAL_API_KEY is required in production.")
            self.write_api_key_required = True
        return self

settings = Settings()
