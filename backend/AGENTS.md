# BACKEND KNOWLEDGE BASE

## OVERVIEW
FastAPI boundary layer around `run_risk_analysis`; request validation, config loading, response shaping.

## STRUCTURE
```text
backend/
├── main.py
├── models.py
├── test_main.py
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
| Dependency policy | `requirements.txt` | Versions pinned; keep deterministic |

## CONVENTIONS
- API surface stays minimal: `/` health + `/analyse` compute route.
- Validation errors should be HTTP 422 from schema bounds; model `ValueError` mapped to 400.
- Keep `run_risk_analysis` import path stable unless doing broader packaging refactor.

## ANTI-PATTERNS
- Restoring `allow_origins=["*"]`.
- Adding unbounded PyMC run parameters beyond current validated ranges.
- Writing tests that require live PyMC dependency for basic route behavior.
- Returning `losses_samples` or `raw_trace` from API route (payload bloat risk).

## COMMANDS
```bash
python -m pip install --requirement backend/requirements.txt
python -m pytest backend/test_main.py -v
python -m backend.main
```

## NOTES
- `test_main.py` stubs `pymc`/`matplotlib` modules before importing app; keep this for lightweight CI.
- `run_risk_analysis` stops materializing full posterior samples by default; pass `include_full_samples=True` only when a caller needs the raw arrays.
