"""Local-only R2 fixtures; never call model services or change legacy data."""
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v3.common import read_json, read_jsonl
from cbm_drift_v3.prepare import derive_sequences, build_request_plans
from cbm_drift_v3.controlled_cases import build_controlled


@pytest.fixture(scope="session")
def config():
    return read_json(ROOT / "config/experiment_gpu4_r2.json")


@pytest.fixture(scope="session")
def source():
    return read_jsonl(ROOT.parent / "cbm_drift_diagnostic_v2/data/evidence_sequences.jsonl")


@pytest.fixture(scope="session")
def sequences(source):
    return derive_sequences(source)


@pytest.fixture(scope="session")
def plans(config, sequences):
    return build_request_plans(config, sequences)


@pytest.fixture(scope="session")
def controlled(sequences, tmp_path_factory):
    path = tmp_path_factory.mktemp("controlled")
    report = build_controlled(sequences, path)
    return read_jsonl(path / "cases.jsonl"), read_jsonl(path / "expected_labels.jsonl"), report


@pytest.fixture(scope="session")
def judge_config():
    return read_json(ROOT / "config/judge_controlled_r2.json")
