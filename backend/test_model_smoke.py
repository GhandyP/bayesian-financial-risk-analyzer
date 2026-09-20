"""Smoke tests for the real PyMC sampling path.

Unlike ``test_main.py``, these tests run the actual sampler against the pinned
dependencies: they are the only tests that execute the code path a real request
takes. They are slow (minutes), so they are marked ``slow`` and excluded
from the default suite by ``pytest.ini``.

Run the slow suite on its own, excluding ``test_main.py`` so its ``pymc`` stub
never reaches this process:

    pytest -m slow --ignore=backend/test_main.py -v

Keep them in a separate pytest process from ``test_main.py``: that module
replaces ``pymc`` in ``sys.modules`` with a ``MagicMock``. The guard below fails
loudly instead of silently passing against that stub.
"""

from __future__ import annotations

import base64
import math
import sys
import types
from pathlib import Path

import numpy as np
import pytest

# Add the repository root to the path for imports (same pattern as test_main.py).
MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

pytestmark = pytest.mark.slow

RETURNS = [-0.012, 0.008, -0.004, 0.01, -0.006, 0.007, -0.003, 0.005, -0.002, 0.004]

# The API defaults. The accepted minimum (500 draws) does not converge on
# fat-tailed data, and even on this payload it lands close enough to the ESS
# threshold that an environment difference could fail the test for a reason
# unrelated to the code path it exists to cover.
SAMPLING = {"draws": 2000, "tune": 1000}

PNG_BASE64_PREFIX = "iVBORw0KGgo"


@pytest.fixture(autouse=True)
def _require_real_pymc() -> None:
    """Fail loudly when pymc is a stub rather than silently passing against it."""
    import pymc as pm

    if not isinstance(pm.sample, types.FunctionType):
        pytest.fail(
            "pymc is not the real package (a stub is installed in sys.modules). "
            "Run this file on its own: pytest backend/test_model_smoke.py -m slow"
        )


def test_real_sampling_path_produces_a_finite_positive_var() -> None:
    """The default (cheap) request path must return sane, non-materialized results."""
    from Analisis_Riesgo_PyMC import MIN_DEGREES_OF_FREEDOM, run_risk_analysis

    result = run_risk_analysis(
        RETURNS, investment_amount=1_000_000.0, loss_threshold=50_000.0, **SAMPLING
    )

    assert math.isfinite(result.var_value)
    assert result.var_value > 0, "a 95% VaR on losses must be a positive amount"
    assert 0.0 <= result.threshold_probability <= 1.0
    assert set(result.parameter_means) == {"media_retorno", "desviacion_retorno", "nu"}
    assert result.parameter_means["desviacion_retorno"] > 0
    # The floor on the tail index keeps the variance finite.
    assert result.parameter_means["nu"] > MIN_DEGREES_OF_FREEDOM

    # The histogram must be a real, decodable PNG.
    assert result.histogram_base64.startswith(PNG_BASE64_PREFIX)
    assert base64.b64decode(result.histogram_base64).startswith(b"\x89PNG\r\n\x1a\n")

    # Default behaviour: the heavy arrays are deliberately not materialized.
    assert result.losses_samples == []
    assert result.raw_trace == {}


def test_reported_metrics_match_the_simulated_samples() -> None:
    """The analytic measures must agree with the simulated loss distribution."""
    from Analisis_Riesgo_PyMC import run_risk_analysis

    confidence = 0.9
    threshold = 20_000.0

    result = run_risk_analysis(
        RETURNS,
        investment_amount=500_000.0,
        var_confidence=confidence,
        loss_threshold=threshold,
        include_full_samples=True,
        **SAMPLING,
    )

    losses = np.asarray(result.losses_samples)
    assert losses.size > 0

    # The reported measures come from closed-form per-draw formulas rather than
    # from the simulation, so these are cross-checks between two independent
    # estimators of the same quantity, not equalities.
    empirical_var = float(np.percentile(losses, confidence * 100.0))
    assert result.var_value == pytest.approx(empirical_var, rel=0.15)

    empirical_threshold_probability = float(np.mean(losses > threshold))
    assert result.threshold_probability == pytest.approx(
        empirical_threshold_probability, abs=0.002
    )

    # Expected shortfall is the mean loss beyond the VaR, so it is always the
    # larger of the two, and the credible interval must bracket the estimate.
    assert result.expected_shortfall > result.var_value > 0
    assert result.var_value_lower < result.var_value < result.var_value_upper

    # Opt-in sampling exposes both posterior parameters.
    assert set(result.raw_trace) == {"media_retorno", "desviacion_retorno"}

    # One predictive return is drawn per posterior sample, so the loss array is
    # exactly as long as the posterior: no padding from repeating the historical
    # observations.
    posterior_size = len(result.raw_trace["media_retorno"])
    assert losses.size == posterior_size
