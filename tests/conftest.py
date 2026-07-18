"""Shared test fixtures."""
import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _isolate_env():
    """Prevent tests from reading the real .env file."""
    with patch.dict(os.environ, {}, clear=False):
        yield
