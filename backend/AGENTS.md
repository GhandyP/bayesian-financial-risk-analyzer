# BACKEND KNOWLEDGE BASE

## OVERVIEW
FastAPI boundary layer around `run_risk_analysis`; request validation, config loading, response shaping.

## STRUCTURE
```text
backend/
├── main.py
├── models.py
├── test_main.py
├── test_contract.py
├── test_model_smoke.py
├── contract/
└── requirements.txt
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Runtime config | `main.py` (`RuntimeSettings`) | Reads `API_HOST`, `API_PORT`, `API_CORS_ORIGINS` |
| CORS behavior | `main.py` middleware setup | Allowlist parsed from comma-separated env value |
| Request validation | `models.py` `RiskRequest` | Pydantic v2 field bounds + minimum 10 returns validator |
| API contract | `models.py` `RiskResponse` | Response schema; flattened payload, no posterior samples |
| API routes | `main.py` `analyse` route | Bridges request to model; 400 on ValueError, 504 on timeout |
| Endpoint tests | `test_main.py` | Uses `TestClient`, patches `run_risk_analysis` |
| Real model tests | `test_model_smoke.py` | `slow`-marked; real PyMC run, own pytest process |
| Coverage backtest | `test_coverage_backtest.py` | `slow`-marked; one fit per window scored on later returns |
| Contract tests | `test_contract.py` | Regenerates the Dart fixture; checks Dart limits against Pydantic |
| Response example | `contract/risk_response.example.json` | Generated; decoded by the Dart suite |
| Dependency policy | `requirements.txt` | Versions pinned; keep deterministic |

## CONVENTIONS
- API surface stays minimal: `/` health + `/analyse` compute route.
- Validation errors should be HTTP 422 from schema bounds; model `ValueError` mapped to 400.
- Keep `run_risk_analysis` import path stable unless doing broader packaging refactor.

## ANTI-PATTERNS
- Restoring `allow_origins=["*"]`.
- Adding unbounded PyMC run parameters beyond current validated ranges.
- Writing tests that require live PyMC dependency for basic route behavior.
- Widening the convergence thresholds so a request passes, or reporting a number when the posterior failed the gate.
- Returning `losses_samples` or `raw_trace` from API route (payload bloat risk).

## COMMANDS
```bash
python -m pip install --requirement backend/requirements.txt
python -m ruff check .
python -m pytest -m "not slow" -v
python -m pytest -m slow -v
python -m backend.test_contract
python -m backend.main
```

## NOTES
- `test_main.py` stubs `pymc`/`matplotlib` modules before importing app; keep this for lightweight CI.
- Because of that stub, `test_model_smoke.py` must never run in the same pytest process: it guards against a mocked `pymc` and fails loudly.
- `run_risk_analysis` stops materializing full posterior samples by default; pass `include_full_samples=True` only when a caller needs the raw arrays.
- Request bounds live in `risk_limits.py`, not in `models.py`, so the Pydantic layer stays free of the PyMC import.
- The route maps `ConvergenceError` to HTTP 500: a posterior that fails the gate (`rhat <= 1.01`, ESS >= 400, divergences <= 0.5% of draws) must not reach the client as a result. Divergences are judged as a rate because the count varies between environments for the same seed.
- Sampling with the API defaults takes roughly 45-75 seconds per request, against a 120-second timeout. `draws=500` is accepted by validation but does not converge on fat-tailed data.
