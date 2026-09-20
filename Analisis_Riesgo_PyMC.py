"""Reusable PyMC model to analyse financial loss risk."""

from __future__ import annotations

import base64
import io
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import arviz as az
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
import scipy.stats as st

from risk_limits import MAX_RETURNS, MIN_RETURNS

# Weakly informative, data-independent priors.
#
# Returns are proportions (``-0.012`` is ``-1.2%``), so these values stay
# defensible for anything from daily to monthly periods while letting the
# likelihood determine the answer. They deliberately do NOT read
# ``returns.mean()``/``returns.std()``: centring the prior on the sample would
# let the data enter the model twice, once through the prior and once through
# the likelihood, and would understate the posterior uncertainty.
PRIOR_MEAN_LOCATION = 0.0
PRIOR_MEAN_SCALE = 0.05

# Volatility prior: log-normal, i.e. a normal prior on ``log(sigma)``.
# A half-normal with a wide scale looks "weak" but has most of its mass far
# above typical period volatilities, and with short samples it biases the
# estimate upward: measured on the sample payload it put the posterior 57%
# above the maximum-likelihood value. A prior on the log keeps the scale
# invariant, so 0.007 and 0.07 are equidistant in relative terms.
#
# PRIOR_SIGMA_MEDIAN is the median of the implied prior on sigma. Returns are
# proportions and the client's examples are single-digit-percent moves, so the
# centre sits at 1% per period. With short samples the prior is a real input to
# the answer, which is why the response reports a credible interval.
PRIOR_SIGMA_MEDIAN = 0.01
PRIOR_SIGMA_LOG_SCALE = 1.0

# Degrees of freedom of the Student-t likelihood, modelled as
# ``MIN_DEGREES_OF_FREEDOM + Exponential(rate)``. The floor keeps the variance
# finite and the expected shortfall defined; the exponential prior keeps mass on
# genuinely fat tails while allowing the Normal limit when the data call for it.
MIN_DEGREES_OF_FREEDOM = 2.0
PRIOR_NU_RATE = 0.1

# Convergence thresholds for the fitted posterior, following the usual
# recommendations: rhat close to 1, a few hundred effective samples, and no
# divergent transitions.
#
# A posterior that fails these does not produce a smaller number, it produces a
# wrong one, so the analysis raises instead of returning a value the caller
# cannot distinguish from a trustworthy one.
CHAIN_COUNT = 4
MAX_RHAT = 1.01
MIN_EFFECTIVE_SAMPLE_SIZE = 400.0
MAX_DIVERGENCES = 0

# Fixed so a given request is reproducible: the simulated losses drive the
# reported VaR, and an unseeded run would make every response a different
# number for the same input.
SAMPLING_SEED = 20260101

# Percentiles of the posterior distribution of the VaR reported as its credible
# interval. The VaR is a function of the parameters, so it has a posterior of its
# own: this is parameter uncertainty, not Monte Carlo noise.
VAR_CREDIBLE_INTERVAL_PERCENTILES = (5.0, 95.0)


class ConvergenceError(RuntimeError):
    """Raised when the posterior did not converge well enough to be reported."""


@dataclass
class RiskAnalysisResult:
    var_value: float
    var_value_lower: float
    var_value_upper: float
    expected_shortfall: float
    threshold_probability: float
    investment_amount: float
    var_confidence: float
    loss_threshold: float
    losses_samples: list[float]
    parameter_means: dict[str, float]
    histogram_base64: str
    raw_trace: dict
    diagnostics: dict[str, float | int | bool]


def run_risk_analysis(
    returns: Sequence[float] | pd.Series | Iterable[float] | Mapping[str, float],
    *,
    investment_amount: float = 1_000_000.0,
    var_confidence: float = 0.95,
    loss_threshold: float = 50_000.0,
    draws: int = 2000,
    tune: int = 1000,
    target_accept: float = 0.9,
    include_full_samples: bool = False,
) -> RiskAnalysisResult:
    """Estimate Value at Risk (VaR) and tail probabilities from historical returns.

    Returns are modelled with a Student-t likelihood so that fat tails are
    estimated rather than assumed away: ``nu`` is fitted from the data, and the
    Normal model is recovered as ``nu`` grows large.

    By default the heavy posterior samples (``losses_samples`` and ``raw_trace``)
    are NOT materialized, because most consumers only need the summary metrics,
    the parameter means and the histogram. Passing ``include_full_samples=True``
    opt-in recovers the full simulation arrays when a caller really needs them.
    """

    if investment_amount <= 0:
        raise ValueError("investment_amount debe ser positivo.")
    if not 0.8 <= var_confidence < 1.0:
        raise ValueError("var_confidence debe estar entre 0.8 y 1.0.")
    if loss_threshold < 0:
        raise ValueError("loss_threshold debe ser no negativo.")

    returns_array = _coerce_returns(returns)
    if not np.isfinite(returns_array).all():
        raise ValueError("Los retornos no pueden contener NaN o infinito.")
    if returns_array.size < MIN_RETURNS:
        raise ValueError(f"Se requieren al menos {MIN_RETURNS} retornos historicos.")
    if returns_array.size > MAX_RETURNS:
        raise ValueError(f"El numero maximo de retornos es {MAX_RETURNS}.")

    with pm.Model():
        media_retorno = pm.Normal(
            "media_retorno", mu=PRIOR_MEAN_LOCATION, sigma=PRIOR_MEAN_SCALE
        )
        # Sampled in log space: the prior is scale-invariant and the sampler
        # explores an unconstrained parameter, which converges better than a
        # half-normal bounded at zero.
        desviacion_retorno = pm.Deterministic(
            "desviacion_retorno",
            pm.math.exp(
                pm.Normal(
                    "log_desviacion",
                    mu=float(np.log(PRIOR_SIGMA_MEDIAN)),
                    sigma=PRIOR_SIGMA_LOG_SCALE,
                )
            ),
        )
        nu = pm.Deterministic(
            "nu",
            MIN_DEGREES_OF_FREEDOM + pm.Exponential("nu_excess", lam=PRIOR_NU_RATE),
        )
        # Student-t takes a scale, not a standard deviation, and the two differ
        # by sqrt(nu/(nu-2)). The conversion below keeps ``desviacion_retorno``
        # interpretable as volatility, which is what the response reports.
        escala_retorno = desviacion_retorno * pm.math.sqrt(
            (nu - MIN_DEGREES_OF_FREEDOM) / nu
        )

        pm.StudentT(
            "retornos",
            nu=nu,
            mu=media_retorno,
            sigma=escala_retorno,
            observed=returns_array,
        )

        trace = pm.sample(
            draws=draws,
            tune=tune,
            target_accept=target_accept,
            # Four chains is the minimum for rhat to mean anything: PyMC warns
            # that two are not enough to compute convergence diagnostics.
            chains=CHAIN_COUNT,
            cores=CHAIN_COUNT,
            random_seed=SAMPLING_SEED,
            progressbar=False,
        )

    diagnostics = _convergence_diagnostics(trace)
    _require_convergence(diagnostics)

    # One predictive return per posterior sample, drawn from the fitted
    # Student-t. Sampling the observed variable instead returns one draw per
    # (posterior sample, historical observation) pair, which pads the sample count
    # with copies of the same points and understates the Monte Carlo error.
    simulated_returns = _simulate_returns(trace, np.random.default_rng(SAMPLING_SEED))
    simulated_losses = -simulated_returns * investment_amount

    # The reported measures are analytic functions of each posterior draw rather
    # than percentiles of the simulated losses: the tail statistics of a
    # Student-t have closed forms, so the 95% VaR no longer rests on the 5% of the
    # simulated draws that happen to fall beyond it.
    var_draws, shortfall_draws = _var_and_shortfall(
        trace, var_confidence, investment_amount
    )
    var_value = float(np.mean(var_draws))
    var_value_lower = float(
        np.percentile(var_draws, VAR_CREDIBLE_INTERVAL_PERCENTILES[0])
    )
    var_value_upper = float(
        np.percentile(var_draws, VAR_CREDIBLE_INTERVAL_PERCENTILES[1])
    )
    expected_shortfall = float(np.mean(shortfall_draws))
    threshold_probability = _threshold_probability(
        trace, loss_threshold / investment_amount
    )

    histogram_base64 = _encode_histogram(
        simulated_losses,
        var_value=var_value,
        threshold=loss_threshold,
        var_confidence=var_confidence,
    )

    parameter_means = {
        "media_retorno": float(trace.posterior["media_retorno"].mean()),
        "desviacion_retorno": float(trace.posterior["desviacion_retorno"].mean()),
        "nu": float(trace.posterior["nu"].mean()),
    }

    losses_samples: list[float]
    raw_trace: dict
    if include_full_samples:
        losses_samples = simulated_losses.tolist()
        raw_trace = {
            "media_retorno": trace.posterior["media_retorno"].to_numpy().ravel().tolist(),
            "desviacion_retorno": trace.posterior["desviacion_retorno"]
            .to_numpy()
            .ravel()
            .tolist(),
        }
    else:
        losses_samples = []
        raw_trace = {}

    return RiskAnalysisResult(
        var_value=var_value,
        var_value_lower=var_value_lower,
        var_value_upper=var_value_upper,
        expected_shortfall=expected_shortfall,
        threshold_probability=threshold_probability,
        investment_amount=float(investment_amount),
        var_confidence=float(var_confidence),
        loss_threshold=float(loss_threshold),
        losses_samples=losses_samples,
        parameter_means=parameter_means,
        histogram_base64=histogram_base64,
        raw_trace=raw_trace,
        diagnostics=diagnostics,
    )


def _coerce_returns(
    returns: Sequence[float] | pd.Series | Iterable[float] | Mapping[str, float]
) -> np.ndarray:
    if isinstance(returns, pd.Series):
        array = returns.to_numpy(dtype=float)
    elif isinstance(returns, Mapping):
        array = np.asarray(list(returns.values()), dtype=float)
    else:
        array = np.asarray(list(returns), dtype=float)

    if array.ndim != 1:
        raise ValueError("Los retornos deben ser una secuencia unidimensional.")

    return array


def _posterior_parameters(
    trace: az.InferenceData,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Flat posterior draws of (mean, standard deviation, tail index)."""
    posterior = trace.posterior
    return (
        posterior["media_retorno"].to_numpy().ravel(),
        posterior["desviacion_retorno"].to_numpy().ravel(),
        posterior["nu"].to_numpy().ravel(),
    )


def _t_scale(desviacion: np.ndarray, nu: np.ndarray) -> np.ndarray:
    """Student-t scale for which ``desviacion`` is the standard deviation."""
    return desviacion * np.sqrt((nu - MIN_DEGREES_OF_FREEDOM) / nu)


def _simulate_returns(
    trace: az.InferenceData, rng: np.random.Generator
) -> np.ndarray:
    """Draw one new return per posterior sample from the fitted Student-t."""
    media, desviacion, nu = _posterior_parameters(trace)
    return media + _t_scale(desviacion, nu) * rng.standard_t(nu)


def _var_and_shortfall(
    trace: az.InferenceData, confidence: float, investment_amount: float
) -> tuple[np.ndarray, np.ndarray]:
    """Analytic VaR and expected shortfall, in currency, for every draw.

    Both are computed per posterior sample and returned as arrays so the caller
    can report the VaR posterior itself. ``nu > 2`` keeps the variance finite and
    the tail mean below finite, so neither quantity can blow up.
    """
    media, desviacion, nu = _posterior_parameters(trace)
    scale = _t_scale(desviacion, nu)
    alpha = 1.0 - confidence
    quantile = st.t.ppf(alpha, nu)
    density = st.t.pdf(quantile, nu)
    # E[T | T <= q] for a standard Student-t at its alpha quantile q.
    tail_mean = -density * (nu + quantile**2) / ((nu - 1.0) * alpha)
    var_loss = -(media + scale * quantile) * investment_amount
    shortfall_loss = -(media + scale * tail_mean) * investment_amount
    return var_loss, shortfall_loss


def _threshold_probability(trace: az.InferenceData, threshold_return: float) -> float:
    """Posterior mean of P(loss > threshold), evaluated analytically per draw."""
    media, desviacion, nu = _posterior_parameters(trace)
    scale = _t_scale(desviacion, nu)
    per_draw = st.t.cdf((-threshold_return - media) / scale, nu)
    return float(np.mean(per_draw))


def _convergence_diagnostics(trace: az.InferenceData) -> dict[str, float | int | bool]:
    """MCMC health indicators for the fitted posterior, computed with ArviZ.

    ``max_rhat`` and ``min_ess`` are taken over every posterior variable, so a
    single badly mixing parameter cannot hide behind the others.
    """
    rhat = az.rhat(trace)
    ess = az.ess(trace)
    max_rhat = max(float(rhat[name].max()) for name in rhat.data_vars)
    min_ess = min(float(ess[name].min()) for name in ess.data_vars)
    divergences = int(trace.sample_stats["diverging"].sum())
    return {
        "max_rhat": max_rhat,
        "min_ess": min_ess,
        "divergences": divergences,
        "converged": (
            max_rhat <= MAX_RHAT
            and min_ess >= MIN_EFFECTIVE_SAMPLE_SIZE
            and divergences <= MAX_DIVERGENCES
        ),
    }


def _require_convergence(diagnostics: dict[str, float | int | bool]) -> None:
    """Refuse to report a number from a posterior that did not converge."""
    if diagnostics["converged"]:
        return
    raise ConvergenceError(
        "El muestreo no convergio: "
        f"rhat maximo {diagnostics['max_rhat']:.4f} (limite {MAX_RHAT}), "
        f"ESS minimo {diagnostics['min_ess']:.0f} "
        f"(minimo {MIN_EFFECTIVE_SAMPLE_SIZE:.0f}), "
        f"divergencias {diagnostics['divergences']} (maximo {MAX_DIVERGENCES})."
    )


def _encode_histogram(
    losses: np.ndarray,
    *,
    var_value: float,
    threshold: float,
    var_confidence: float,
) -> str:
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(losses, bins=50, density=True, alpha=0.7, color="crimson")
    ax.axvline(var_value, color="black", linestyle="dashed", label=f"VaR {var_confidence:.0%} = {var_value:,.0f}")
    ax.axvline(threshold, color="royalblue", linestyle="dashed", label=f"Umbral = {threshold:,.0f}")
    ax.set_title("Distribucion simulada de perdidas")
    ax.set_xlabel("Perdida (moneda)")
    ax.set_ylabel("Densidad")
    ax.legend()

    buffer = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    sample_returns = rng.normal(loc=-0.001, scale=0.02, size=1000)
    result = run_risk_analysis(sample_returns)
    print("VaR 95%:", result.var_value)
