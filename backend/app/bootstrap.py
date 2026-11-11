"""Prepare a fresh environment: schema, generated data, and model artifact.

Idempotent: data is generated only when the plants table is empty, and the model
is trained only when the configured artifact is missing.

    python -m backend.app.bootstrap
"""
import logging
import os
import sys

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, check_database, init_db
from backend.app.models.plant import Plant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bootstrap")


def main() -> int:
    db_status = check_database()
    if db_status["status"] != "CONNECTED":
        logger.error("Database unavailable (%s): %s", db_status["backend"], db_status.get("error"))
        return 1

    init_db()

    db = SessionLocal()
    try:
        has_data = db.query(Plant).first() is not None
        if not has_data:
            from backend.app.data_generation.generator import SyntheticDataGenerator
            logger.info("Database is empty; generating %s dataset with seed %s", settings.GENERATION_MODE, settings.RANDOM_SEED)
            summary = SyntheticDataGenerator(seed=settings.RANDOM_SEED, mode=settings.GENERATION_MODE, db=db).run()
            logger.info("Generated: %s", summary)
        else:
            logger.info("Database already populated; skipping data generation.")
    finally:
        db.close()

    if not os.path.exists(settings.model_file):
        from backend.app.ml.train import train_and_evaluate_models
        logger.info("Model artifact missing at %s; training.", settings.model_file)
        train_and_evaluate_models()
    else:
        logger.info("Model artifact present at %s", settings.model_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
