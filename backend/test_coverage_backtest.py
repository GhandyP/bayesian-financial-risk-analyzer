"""Out-of-sample coverage of the reported VaR on synthetic fat-tailed data.

A window of a known data-generating process is used to fit the model, and the
model is then asked to cover the returns that follow that window. This is the
only check here that answers the question a risk number exists to answer: is a
95% VaR actually exceeded about 5% of the time?

Each window is one posterior fit scored against every following out-of-sample
return, so the coverage estimate does not cost a fit per observation.

Slow: every window fits a full posterior, so this file carries the `slow`
marker and, like `test_model_smoke.py`, must run in its own pytest process.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

pytestmark = pytest.mark.slow

# Data-generating process: a Student-t with genuinely fat tails, which is the
# case the Normal likelihood used to get wrong. TRUE_SCALE is the t scale, so the
# standard deviation of these returns is about 0.0099.
TRUE_NU = 4.0
TRUE_SCALE = 0.007
DATA_SEED = 424242

TRAIN_SIZE = 150
TEST_SIZE = 150
WINDOW_COUNT = 3

CONFIDENCE = 0.95

# The API defaults, not the API minimum. At draws=500 and tune=200 this
# posterior does not converge: measured rhat 1.0260 and ESS 258 against the
# thresholds in the model, with PyMC warning that the effective sample size per
# chain is below 100. At the defaults the same window gives rhat 1.0017, ESS 1791
# and recovers the true tail index (nu 4.04 against a true 4.0).
SAMPLING = {"draws": 2000, "tune": 1000}

# Under correct coverage the exceedance count over 450 out-of-sample points is
# Binomial(450, 0.05): mean 22.5, standard deviation 4.6. The band is wide enough
# to absorb estimation error and narrow enough to reject gross miscalibration.
MINIMUM_EXCEEDANCE_RATE = 0.02
MAXIMUM_EXCEEDANCE_RATE = 0.09


@pytest.fixture(autouse=True)
def _require_real_pymc() -> None:
    """Fail loudly when pymc is a stub rather than silently passing against it."""
    import pymc as pm

    if not isinstance(pm.sample, types.FunctionType):
        pytest.fail(
            "pymc is not the real package (a stub is installed in sys.modules). "
            "Run this file on its own: pytest backend/test_coverage_backtest.py -m slow"
        )


def _synthetic_returns(size: int) -> np.ndarray:
    rng = np.random.default_rng(DATA_SEED)
    return TRUE_SCALE * rng.standard_t(TRUE_NU, size=size)


def test_var_is_exceeded_at_roughly_the_nominal_rate_out_of_sample() -> None:
    from Analisis_Riesgo_PyMC import run_risk_analysis

    series = _synthetic_returns(WINDOW_COUNT * (TRAIN_SIZE + TEST_SIZE))

    exceedances = 0
    tested = 0
    rows: list[str] = []

    for window in range(WINDOW_COUNT):
        start = window * TEST_SIZE
        train = series[start : start + TRAIN_SIZE]
        test = series[start + TRAIN_SIZE : start + TRAIN_SIZE + TEST_SIZE]

        result = run_risk_analysis(
            train,
            investment_amount=1.0,
            var_confidence=CONFIDENCE,
            loss_threshold=0.05,
            **SAMPLING,
        )

        # investment_amount=1.0 keeps the VaR in return units, so it is directly
        # comparable with the negated out-of-sample return.
        window_exceedances = int(np.sum(-test > result.var_value))
        exceedances += window_exceedances
        tested += int(test.size)
        rows.append(
            f"window {window}: VaR {result.var_value:.5f} "
            f"(nu {result.parameter_means['nu']:.1f}) "
            f"-> {window_exceedances}/{test.size} exceedances"
        )

    rate = exceedances / tested
    message = "\n".join(
        [
            "",
            *rows,
            f"out-of-sample exceedances: {exceedances}/{tested} = {rate:.2%} "
            f"(nominal {1 - CONFIDENCE:.0%})",
        ]
    )
    print(message)

    assert MINIMUM_EXCEEDANCE_RATE <= rate <= MAXIMUM_EXCEEDANCE_RATE, message
