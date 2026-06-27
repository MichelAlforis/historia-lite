"""Configuration centralisee pour Historia Lite"""
import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration de l'application Historia Lite"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_reload: bool = False
    debug: bool = False

    # CORS Configuration
    cors_origins: List[str] = [
        "https://historia.alforis.fr",
    ]

    # Ollama Configuration (use localhost with SSH tunnel, or server IP directly)
    ollama_url: str = "http://localhost:11434"  # Via SSH tunnel: ssh -L 11434:localhost:11434 root@159.69.108.234
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout: float = 10.0  # Reduced from 30s for faster fallback
    ollama_tiers: List[int] = [1, 2]
    ollama_rate_limit: float = 1.0  # Minimum seconds between requests
    ollama_cache_ttl: int = 5  # Cache decisions for N ticks

    # Game Configuration
    default_seed: int = 42
    tick_interval: float = 1.0

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Singleton instance
settings = Settings()
