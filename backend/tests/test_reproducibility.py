import os
import hashlib
import pytest
import pandas as pd

def test_ground_truth_exists_and_reproducible():
    path = "data/ground_truth/ground_truth.csv"
    assert os.path.exists(path), "ground_truth.csv must exist in data/ground_truth/"

    df = pd.read_csv(path)
    # Target failure counts between 100 and 200
    assert 100 <= len(df) <= 200, f"Expected 100-200 ground truth failures, found {len(df)}"
    assert "failure_id" in df.columns
    assert "machine_id" in df.columns
    assert "failure_type" in df.columns
    assert "lead_time_hours" in df.columns

    # Check SHA-256 is deterministic
    with open(path, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    assert len(checksum) == 64
    assert checksum == "3372bf6731afd02e205e4d15aec385d3b0333bd2f2771531f0ed862a9aa5b704"


def test_generator_reproduces_committed_ground_truth():
    from backend.app.core.config import settings
    generated = settings.ground_truth_file
    if not os.path.exists(generated):
        pytest.skip("Test database was already populated, so no data was generated in this run.")
    with open(generated, "rb") as a, open("data/ground_truth/ground_truth.csv", "rb") as b:
        assert a.read() == b.read()

