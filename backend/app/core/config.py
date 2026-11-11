import os
import json
from typing import List, Union
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI-Based Predictive Maintenance System"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./predictive_maintenance.db")
    SQLITE_FALLBACK: bool = True
    SQLITE_URL: str = "sqlite:///./predictive_maintenance.db"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    # Data generation
    RANDOM_SEED: int = 20261022
    GENERATION_MODE: str = os.getenv("GENERATION_MODE", "starter")  # 'starter' or 'full'

    # Machine Learning
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/ml/saved_models/failure_prediction_rf.joblib")
    METRICS_PATH: str = os.getenv("METRICS_PATH", "../data/reports/model_evaluation_report.json")
    PREDICTION_HORIZON_HOURS: int = 24
    RISK_THRESHOLD_LOW: float = 0.35
    RISK_THRESHOLD_HIGH: float = 0.70

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
