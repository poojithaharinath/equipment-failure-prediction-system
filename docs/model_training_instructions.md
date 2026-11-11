# Model Training Instructions

## Overview

`backend/app/ml/train.py` trains two classifiers on features from `FeatureExtractor.build_chronological_dataset()` and always saves the Random Forest as the model used for inference.

```bash
python -m backend.app.data_generation.generator --mode starter --seed 20261022
python -m backend.app.ml.train
```

Run both commands from the project root. Training reads the database configured by `DATABASE_URL` (PostgreSQL by default; see `backend/.env.example`). The API can start the same function with `POST /api/model-evaluation/train`.

## Outputs

| File | Written by |
|---|---|
| `backend/app/ml/saved_models/failure_prediction_rf.joblib` | `joblib.dump` of the bundle below. Path comes from `settings.MODEL_PATH`. |
| `data/processed/feature_matrix.csv` | The full chronological frame, including `failure_in_24h` |
| `data/reports/model_evaluation_report.json` | Train/test sizes plus champion and baseline metrics |

`FailurePredictor` in `backend/app/ml/predictor.py` loads that joblib file. If the file is missing or unreadable, `FailurePredictor` raises `ModelNotAvailableError`: prediction endpoints return `503` and `/health` reports the model as `UNAVAILABLE`. It does not fall back to a heuristic or call the training code. `python -m backend.app.bootstrap` trains the model when the artifact is absent.

## How rows are built 

`train_and_evaluate_models()` calls:

```python
extractor.build_chronological_dataset(time_step_days=1.0, prediction_horizon_hours=24)
```

`time_step_days` is accepted and not used. The extractor loads telemetry once, groups it by machine, and samples:

- 25 timestamps spread from 2 days after the first reading across 86 days
- extra points 18, 12, 6, and 2 hours before each failure on that machine, when the point still sits inside the series

The label `failure_in_24h` is 1 when `failure_events` has a timestamp for the same machine in `(as_of_time, as_of_time + 24h]`. `data/ground_truth/ground_truth.csv` is not an input.

Features, all computed from data at or before `as_of_time`, are the 11 names in `FEATURE_COLUMNS`:

| Feature | Rule in `build_chronological_dataset` |
|---|---|
| `avg_temperature_24h` | Mean temperature in the past 24 hours, else 65.0 |
| `max_temperature_24h` | Max temperature in that window, else 68.0 |
| `avg_vibration_24h` | Mean vibration in that window, else 1.8 |
| `vibration_trend` | Mean vibration over the past 6 hours divided by `max(0.5, avg_vibration_24h)` |
| `pressure_fluctuation_24h` | Standard deviation of pressure, else 1.5 when fewer than 2 points |
| `current_fluctuation_24h` | Standard deviation of current, else 2.0 when fewer than 2 points |
| `avg_rpm_24h` | Mean RPM, else 1650.0 |
| `operating_hours` | `machines.operating_hours` |
| `missing_sensor_count` | How many of the five sensor types are absent from the 24-hour window |
| `previous_failure_count` | Failures for the machine strictly before `as_of_time` |
| `previous_maintenance_count` | Work orders scheduled strictly before `as_of_time` |

`vibration_trend` is a 6-hour to 24-hour level ratio. It is not `(last - first) / first`.

## Split and models

The frame is sorted by `as_of_time`. The first 75% is the training set and the last 25% is the test set. Rows are not shuffled.

`StandardScaler` is fit on the training features only. It is applied to the logistic regression matrices. The random forest is fit and scored on the unscaled matrices:

```python
RandomForestClassifier(
    n_estimators=120,
    max_depth=8,
    class_weight="balanced",
    random_state=settings.RANDOM_SEED,  # 20261022
    n_jobs=-1,
)
LogisticRegression(
    class_weight="balanced",
    max_iter=1000,
    random_state=settings.RANDOM_SEED,
)
```


Random Forest probabilities come from `predict_proba` on unscaled test rows. Logistic regression probabilities come from the scaled test rows.

The saved bundle always contains the random forest, even when logistic regression has the higher F1 score. `comparison_summary.winner` is whichever model has `f1_score` greater than or equal to the other. On the checked-in starter report that winner is `LogisticRegression`. Inference still loads the random forest file.

Bundle keys written by `train.py`:

```python
{
    "model": rf,
    "scaler": scaler,
    "feature_columns": FEATURE_COLUMNS,
    "trained_at": "<UTC ISO timestamp>",
    "metrics": rf_metrics,
    "random_seed": settings.RANDOM_SEED,
    "prediction_horizon_hours": 24,
    "threshold_low": settings.RISK_THRESHOLD_LOW,    # 0.35
    "threshold_high": settings.RISK_THRESHOLD_HIGH,  # 0.70
}
```

Train and test sizes are fields on the evaluation report (`train_set_size`, `test_set_size`), not keys inside the joblib bundle.

## Checked-in starter report

`data/reports/model_evaluation_report.json` from the current starter dataset:

| | Random Forest (saved model) | Logistic Regression (baseline) |
|---|---|---|
| Accuracy | 0.9372 | 0.9463 |
| Precision | 0.9420 | 0.9388 |
| Recall | 0.7647 | 0.8118 |
| F1 | 0.8442 | 0.8707 |
| ROC-AUC | 0.9368 | 0.9120 |
| Confusion matrix | TN 586, FP 8, FN 40, TP 130 | TN 585, FP 9, FN 32, TP 138 |

Report sizes: 2,292 train rows, 764 test rows, 170 positive test labels. Retraining overwrites these numbers.

## Risk labels at inference time

`FailurePredictor.predict_for_machine()` maps probability with the thresholds stored in the bundle, falling back to settings:

| Probability | Category |
|---|---|
| `>= 0.70` | High Risk |
| `>= 0.35` and `< 0.70` | Medium Risk |
| `< 0.35` | Low Risk |

`explain_prediction()` compares a subset of features with fixed healthy baselines (temperature 65, peak temperature 68, vibration 1.8, vibration trend 1.0, pressure fluctuation 1.5, current fluctuation 2.0, operating hours 5000). It keeps up to four upward deviations and turns each share of the total deviation into `severity_impact_pct`. Recommendation text depends on whether probability is above the high threshold, at or above the low threshold, or below it.

## Checks

```bash
python -m pytest backend/tests/test_ml.py backend/tests/test_api.py -v
```

`test_model_evaluation_report` expects `champion_model.accuracy` in `GET /api/model-evaluation`. That endpoint reads `data/reports/model_evaluation_report.json`.
