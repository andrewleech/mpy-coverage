"""Pytest integration for the trial-based integration tests.

Generates one pytest test per trial function from test_coverage.py.
Tests are skipped if the micropython binary is not available.
"""

import pytest

from tests.test_coverage import ALL_TRIALS, MPY_BINARY
import os

requires_micropython = pytest.mark.skipif(
    not MPY_BINARY or not os.path.exists(MPY_BINARY),
    reason="micropython binary not found (set MPY_BINARY env var)",
)


def _make_test(trial_fn):
    @requires_micropython
    def test(self):
        assert trial_fn()
    test.__doc__ = trial_fn.__doc__
    return test


class TestCoverageTrials:
    """Integration tests requiring a micropython binary."""
    pass


for _trial in ALL_TRIALS:
    setattr(TestCoverageTrials, f"test_{_trial.__name__}", _make_test(_trial))
