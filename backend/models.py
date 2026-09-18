"""Pydantic models for the risk analysis API contract."""

from __future__ import annotations

import math
from typing import List

from pydantic import BaseModel, Field, field_validator

from risk_limits import MAX_RETURNS, MIN_RETURNS


class RiskRequest(BaseModel):
    returns: List[float]
    investment_amount: float = Field(1_000_000.0, gt=0)
    var_confidence: float = Field(0.95, ge=0.8, lt=1.0)
    loss_threshold: float = Field(50_000.0, ge=0)
    draws: int = Field(2000, ge=500, le=10000)
    tune: int = Field(1000, ge=200, le=10000)
    target_accept: float = Field(0.9, ge=0.5, le=0.99)

    @field_validator("returns")
    @classmethod
    def _validate_returns(cls, value: List[float]) -> List[float]:
        if len(value) < MIN_RETURNS:
            raise ValueError(f"Debe proporcionar al menos {MIN_RETURNS} retornos historicos.")
        if len(value) > MAX_RETURNS:
            raise ValueError(f"El numero maximo de retornos es {MAX_RETURNS}.")
        if any(not math.isfinite(item) for item in value):
            raise ValueError("Los retornos no pueden contener NaN o infinito.")
        return value


class ParameterMeans(BaseModel):
    media_retorno: float
    desviacion_retorno: float


class RiskResponse(BaseModel):
    var_value: float
    threshold_probability: float
    investment_amount: float
    var_confidence: float
    loss_threshold: float
    parameter_means: ParameterMeans
    histogram_base64: str
