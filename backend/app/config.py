import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    CORS_ORIGINS: str = "*"

    # Fraud Detection Engine Parameters
    LARGE_TRANSACTION_THRESHOLD: float = 10000.0
    HIGH_VELOCITY_TX_COUNT: int = 5
    HIGH_VELOCITY_WINDOW_HOURS: int = 24
    SMURFING_SUB_THRESHOLD: float = 10000.0
    SMURFING_MIN_ACCOUNTS: int = 3
    CIRCULAR_MIN_DEPTH: int = 3
    CIRCULAR_MAX_DEPTH: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
