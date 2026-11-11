import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.ml.train import train_and_evaluate_models

router = APIRouter(prefix="/model-evaluation", tags=["Model Performance & Evaluation"])

@router.get("")
def get_model_evaluation_metrics(db: Session = Depends(get_db)):
    report_path = settings.metrics_file
    if os.path.exists(report_path):
        try:
            with open(report_path, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback: run evaluation
    return train_and_evaluate_models()

@router.post("/train")
def trigger_model_training(db: Session = Depends(get_db)):
    metrics = train_and_evaluate_models()
    return {
        "message": "Model re-trained and evaluated successfully.",
        "report": metrics
    }

