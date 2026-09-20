"""FastAPI backend exposing the risk analysis PyMC helper."""

from __future__ import annotations

import asyncio
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from backend.models import RiskRequest, RiskResponse

MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

from Analisis_Riesgo_PyMC import run_risk_analysis


@dataclass(frozen=True)
class RuntimeSettings:
    host: str
    port: int
    cors_origins: list[str]


def _parse_origins(raw_origins: str) -> list[str]:
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def _load_runtime_settings() -> RuntimeSettings:
    default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    cors_origins = _parse_origins(os.getenv("API_CORS_ORIGINS", default_origins))
    return RuntimeSettings(host=host, port=port, cors_origins=cors_origins)


SETTINGS = _load_runtime_settings()

app = FastAPI(
    title="Analisis de Riesgo Financiero",
    version="1.0.0",
    description="API que estima VaR y probabilidad de perdidas criticas usando PyMC.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _json_safe(value: object) -> object:
    """Recursively replace non-finite floats so error payloads stay JSON-serializable."""
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return 422 details whose raw input may contain NaN/inf values."""
    detail = jsonable_encoder(exc.errors())
    return JSONResponse(status_code=422, content={"detail": _json_safe(detail)})


@app.get("/", summary="Estado del servicio")
async def root() -> dict:
    return {"status": "ok"}


@app.post("/analyse", summary="Calcula VaR y probabilidad de perdida critica", response_model=RiskResponse)
async def analyse(request: RiskRequest) -> RiskResponse:
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(run_risk_analysis, request.returns, investment_amount=request.investment_amount, var_confidence=request.var_confidence, loss_threshold=request.loss_threshold, draws=request.draws, tune=request.tune, target_accept=request.target_accept),
            timeout=120.0
        )
    except TimeoutError:
        # The timeout is expected behaviour, not a programming error, so the
        # original exception is not chained into the response.
        raise HTTPException(status_code=504, detail="Inference timed out") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RiskResponse(
        var_value=result.var_value,
        threshold_probability=result.threshold_probability,
        investment_amount=result.investment_amount,
        var_confidence=result.var_confidence,
        loss_threshold=result.loss_threshold,
        parameter_means=result.parameter_means,
        histogram_base64=result.histogram_base64,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=SETTINGS.host, port=SETTINGS.port)
