"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App settings
    app_name: str = "Lenskart Contextual Search"
    debug: bool = True
    
    # API Keys
    groq_api_key: str = ""
    
    # Database paths
    sqlite_db_path: str = "./data/lenskart.db"
    chroma_db_path: str = "./data/chroma_db"
    
    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # LLM Model
    llm_model: str = "llama-3.1-70b-versatile"
    
    # Search settings
    default_top_k: int = 10
    semantic_weight: float = 0.6
    behavior_weight: float = 0.4
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

