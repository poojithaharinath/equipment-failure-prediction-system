"""Test setup: every run uses its own database, never the application database.

TEST_DATABASE_URL selects a dedicated database (e.g. a separate PostgreSQL database);
otherwise a throwaway SQLite file is created in a temp directory. The session fixture
migrates it and loads the seeded synthetic dataset via the project bootstrap.
"""
import os
import tempfile

import pytest

_scratch = tempfile.mkdtemp(prefix="pm_tests_")

# Must be set before backend.app.core.config is imported; env vars override backend/.env.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///" + os.path.join(_scratch, "test.db").replace("\\", "/"),
)
# Side-effect files from generation/training stay in the temp dir, not committed data/.
os.environ["VALIDATION_REPORT_PATH"] = os.path.join(_scratch, "validation_report.json")
os.environ["GROUND_TRUTH_PATH"] = os.path.join(_scratch, "ground_truth.csv")
os.environ["FEATURE_MATRIX_PATH"] = os.path.join(_scratch, "feature_matrix.csv")
os.environ["METRICS_PATH"] = os.path.join(_scratch, "model_evaluation_report.json")


@pytest.fixture(scope="session", autouse=True)
def prepared_database():
    from backend.app.bootstrap import main as bootstrap
    if bootstrap() != 0:
        pytest.exit("Test database is unavailable; check TEST_DATABASE_URL.", returncode=1)
