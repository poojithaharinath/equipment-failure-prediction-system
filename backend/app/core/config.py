from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


def resolve_path(path: str) -> str:
    """Resolve a configured path relative to the project root, independent of the working directory."""
    p = Path(path)
    return str(p if p.is_absolute() else PROJECT_ROOT / p)


class Settings(BaseSettings):
    # Process environment variables take precedence over backend/.env.
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI-Based Predictive Maintenance System"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/predictive_maintenance"

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Data generation
    RANDOM_SEED: int = 20261022
    GENERATION_MODE: str = "starter"  # 'starter' or 'full'

    # Machine Learning and report artifacts (relative paths are resolved from the project root)
    MODEL_PATH: str = "backend/app/ml/saved_models/failure_prediction_rf.joblib"
    METRICS_PATH: str = "data/reports/model_evaluation_report.json"
    VALIDATION_REPORT_PATH: str = "data/reports/validation_report.json"
    FEATURE_MATRIX_PATH: str = "data/processed/feature_matrix.csv"
    GROUND_TRUTH_PATH: str = "data/ground_truth/ground_truth.csv"
    PREDICTION_HORIZON_HOURS: int = 24
    RISK_THRESHOLD_LOW: float = 0.35
    RISK_THRESHOLD_HIGH: float = 0.70

    @property
    def model_file(self) -> str:
        return resolve_path(self.MODEL_PATH)

    @property
    def metrics_file(self) -> str:
        return resolve_path(self.METRICS_PATH)

    @property
    def validation_report_file(self) -> str:
        return resolve_path(self.VALIDATION_REPORT_PATH)

    @property
    def feature_matrix_file(self) -> str:
        return resolve_path(self.FEATURE_MATRIX_PATH)

    @property
    def ground_truth_file(self) -> str:
        return resolve_path(self.GROUND_TRUTH_PATH)


settings = Settings()
