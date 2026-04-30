from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    s3_bucket: str = "ai-research"
    s3_endpoint_url: str = "http://localhost:9000"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"

    celery_broker_url: str = "redis://localhost:6379/0"
    tavily_api_key: str = ""

    max_agent_steps: int = 10
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 8
    embedding_cache_ttl: int = 3600
    rag_rewrite_queries: bool = True
    memory_summarise_threshold: int = 20

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
