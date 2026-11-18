"""Operational guard tests; no provider access and no real artifact mutation."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

path = Path(__file__).resolve().parents[1] / 'scripts/safe_resume.py'
spec = importlib.util.spec_from_file_location('cbm_safe_resume_test', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_queue_tampering_rejected_before_online():
    with patch.object(module, 'file_hash', return_value='tampered'):
        with pytest.raises(ValueError, match='queue changed'):
            module.validate_queue()


def test_current_frozen_queue():
    module.validate_queue()
