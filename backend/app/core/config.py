"""
Application configuration management using Pydantic settings.
"""
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Job Aggregation Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_DB: int = 1
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External API Keys
    INDEED_API_KEY: str = ""
    LINKEDIN_RSS_URLS: Union[str, List[str]] = ""
    
    # Stripe Payment
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Scraping Configuration
    SCRAPING_USER_AGENT: str = "Mozilla/5.0 (compatible; JobBot/1.0)"
    SCRAPING_RATE_LIMIT_LINKEDIN: int = 10
    SCRAPING_RATE_LIMIT_INDEED: int = 20
    SCRAPING_RATE_LIMIT_NAUKRI: int = 5
    SCRAPING_RATE_LIMIT_MONSTER: int = 5
    SCRAPE_DO_TOKEN: str = ""
    
    # Provider API Keys
    SCRAPER_API_KEY: str = ""
    SCRAPING_BEE_KEY: str = ""
    DECODO_API_TOKEN: str = ""
    BRIGHT_DATA_API_KEY: str = ""
    BRIGHT_DATA_ZONE: str = ""
    DIFFBOT_TOKEN: str = ""
    PARSEHUB_API_KEY: str = ""
    PARSEHUB_PROJECT_ID: str = ""
    BROWSE_AI_API_KEY: str = ""
    BROWSE_AI_ROBOT_ID: str = ""
    SCRAPE_STORM_API_KEY: str = ""
    DATABAR_API_KEY: str = ""
    
    # File Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_PATH: str = "./uploads"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    # Alerting (Requirement 15.5, 15.7)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ADMIN_EMAIL: str = ""
    FROM_EMAIL: str = ""
    SLACK_WEBHOOK_URL: str = ""
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("LINKEDIN_RSS_URLS", mode="before")
    @classmethod
    def parse_linkedin_urls(cls, v):
        """Parse comma-separated LinkedIn RSS URLs into a list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v:
            return [url.strip() for url in v.split(",")]
        return []
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
