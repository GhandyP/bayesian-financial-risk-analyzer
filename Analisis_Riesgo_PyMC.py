"""Reusable PyMC model to analyse financial loss risk."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm


# Bound the input before allocating model and posterior predictive work.
MAX_RETURNS = 2000


@dataclass
class RiskAnalysisResult:
    var_value: float
    threshold_probability: float
    investment_amount: float
    var_confidence: float
    loss_threshold: float
    losses_samples: list[float]
    parameter_means: dict[str, float]
    histogram_base64: str
    raw_trace: dict


def run_risk_analysis(
    returns: Sequence[float] | pd.Series | Iterable[float] | Mapping[str, float],
    *,
    investment_amount: float = 1_000_000.0,
    var_confidence: float = 0.95,
    loss_threshold: float = 50_000.0,
    draws: int = 2000,
    tune: int = 1000,
    target_accept: float = 0.9,
) -> RiskAnalysisResult:
    """Estimate Value at Risk (VaR) and tail probabilities from historical returns."""

    if investment_amount <= 0:
        raise ValueError("investment_amount debe ser positivo.")
    if not 0.8 <= var_confidence < 1.0:
        raise ValueError("var_confidence debe estar entre 0.8 y 1.0.")
    if loss_threshold < 0:
        raise ValueError("loss_threshold debe ser no negativo.")

    returns_array = _coerce_returns(returns)
    if not np.isfinite(returns_array).all():
        raise ValueError("Los retornos no pueden contener NaN o infinito.")
    if returns_array.size < 10:
        raise ValueError("Se requieren al menos 10 retornos historicos.")
    if returns_array.size > MAX_RETURNS:
        raise ValueError(f"El numero maximo de retornos es {MAX_RETURNS}.")

    with pm.Model() as model:
        media_retorno = pm.Normal(
            "media_retorno", mu=float(returns_array.mean()), sigma=max(float(returns_array.std()), 0.01)
        )
        desviacion_retorno = pm.HalfNormal(
            "desviacion_retorno", sigma=max(float(returns_array.std()), 0.02)
        )

        pm.Normal("retornos", mu=media_retorno, sigma=desviacion_retorno, observed=returns_array)

        trace = pm.sample(
            draws=draws,
            tune=tune,
            target_accept=target_accept,
            progressbar=False,
            return_inferencedata=False,
        )

        predictive = pm.sample_posterior_predictive(trace, samples=5_000, progressbar=False)

    simulated_returns = predictive["retornos"].ravel()
    simulated_losses = -simulated_returns * investment_amount

    var_percentile = var_confidence * 100.0
    var_value = float(np.percentile(simulated_losses, var_percentile))
    threshold_probability = float(np.mean(simulated_losses > loss_threshold))

    histogram_base64 = _encode_histogram(
        simulated_losses,
        var_value=var_value,
        threshold=loss_threshold,
        var_confidence=var_confidence,
    )

    parameter_means = {
        "media_retorno": float(trace["media_retorno"].mean()),
        "desviacion_retorno": float(trace["desviacion_retorno"].mean()),
    }

    raw_trace = {
        "media_retorno": trace["media_retorno"].tolist(),
        "desviacion_retorno": trace["desviacion_retorno"].tolist(),
    }

    return RiskAnalysisResult(
        var_value=var_value,
        threshold_probability=threshold_probability,
        investment_amount=float(investment_amount),
        var_confidence=float(var_confidence),
        loss_threshold=float(loss_threshold),
        losses_samples=simulated_losses.tolist(),
        parameter_means=parameter_means,
        histogram_base64=histogram_base64,
        raw_trace=raw_trace,
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
