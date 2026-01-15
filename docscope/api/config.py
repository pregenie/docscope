"""API configuration"""

from typing import List, Optional
from pydantic import BaseSettings, Field


class APIConfig(BaseSettings):
    """API configuration settings"""
    
    # Application settings
    app_name: str = "DocScope API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="DOCSCOPE_HOST")
    port: int = Field(default=8080, env="DOCSCOPE_PORT")
    workers: int = Field(default=4, env="DOCSCOPE_WORKERS")
    reload: bool = Field(default=False, env="DOCSCOPE_RELOAD")
    
    # CORS settings
    cors_enabled: bool = True
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # API settings
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Authentication
    auth_enabled: bool = False
    secret_key: str = Field(default="change-this-secret-key", env="DOCSCOPE_SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: Optional[str] = Field(default=None, env="DOCSCOPE_DATABASE_URL")
    
    # Search index
    search_index_dir: str = Field(default="~/.docscope/search_index", env="DOCSCOPE_INDEX_DIR")
    
    # WebSocket settings
    ws_enabled: bool = True
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 10
    
    # File upload settings
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_upload_extensions: List[str] = [
        ".md", ".txt", ".pdf", ".json", ".yaml", ".yml",
        ".py", ".js", ".go", ".rs", ".java", ".cpp", ".c",
        ".html", ".htm", ".xml", ".csv", ".tsv"
    ]
    
    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    
    # Monitoring
    metrics_enabled: bool = True
    health_check_enabled: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global config instance
api_config = APIConfig()