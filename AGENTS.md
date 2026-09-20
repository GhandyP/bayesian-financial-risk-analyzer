# PROJECT KNOWLEDGE BASE

## OVERVIEW
Risk analysis project: Bayesian PyMC model + FastAPI API + Flutter UI. Small repo, direct integration, minimal layering.

## STRUCTURE
```text
./
├── Analisis_Riesgo_PyMC.py
├── risk_limits.py
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── test_main.py
│   ├── test_contract.py
│   ├── test_model_smoke.py
│   └── contract/
├── flutter_app/
│   ├── lib/
│   ├── test/
│   └── pubspec.yaml
├── pytest.ini
├── ruff.toml
└── .github/workflows/ci.yml
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Bayesian model logic | `Analisis_Riesgo_PyMC.py` | Core VaR + posterior predictive sampling |
| API contracts/validation | `backend/models.py` | Pydantic request/response models |
| API routes/config | `backend/main.py` | FastAPI routes, CORS, runtime settings |
| Backend tests | `backend/test_main.py` | Uses `TestClient`; model call patched |
| Real model smoke tests | `backend/test_model_smoke.py` | `slow`-marked; runs PyMC for real, own pytest process |
| Coverage backtest | `backend/test_coverage_backtest.py` | `slow`-marked; out-of-sample VaR coverage on synthetic fat tails |
| Cross-language contract | `backend/test_contract.py` | Response example freshness + Dart limits vs Pydantic bounds |
| Shared request limits | `risk_limits.py` | Single source for `MIN_RETURNS`/`MAX_RETURNS`, Pydantic-safe (no PyMC import) |
| Flutter page flow | `flutter_app/lib/main.dart` | Entry widget + submission state |
| Flutter parsing | `flutter_app/lib/utils/parsing_logic.dart` | Shared return parser |
| Flutter widgets | `flutter_app/lib/widgets/` | Input/result/histogram blocks |
| CI checks | `.github/workflows/ci.yml` | Python + Flutter jobs |

## CODE MAP
| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|
| `run_risk_analysis` | function | `Analisis_Riesgo_PyMC.py` | high | Main statistical compute path |
| `RiskRequest` | class | `backend/models.py` | medium | API request schema/validation |
| `RiskResponse` | class | `backend/models.py` | medium | API response contract |
| `analyse` | route fn | `backend/main.py` | high | Bridges API input to model output |
| `ApiService.analyse` | method | `flutter_app/lib/services/api_service.dart` | high | HTTP adapter for UI submit |
| `parseReturns` | function | `flutter_app/lib/utils/parsing_logic.dart` | medium | Input normalization + validation |

## CONVENTIONS
- Spanish UI strings and doc prose; keep user-facing text consistent.
- Backend runtime config from env vars: `API_HOST`, `API_PORT`, `API_CORS_ORIGINS`.
- Python deps pinned in `backend/requirements.txt`; update pins intentionally.
- Flutter lint baseline is `flutter_lints`; keep analyzer clean.

## ANTI-PATTERNS (THIS PROJECT)
- Reintroducing wildcard CORS in backend.
- Adding unpinned Python dependencies.
- Embedding heavy parsing/business logic directly in Flutter widget trees.
- Coupling tests to live PyMC execution for basic API contract tests.

## UNIQUE STYLES
- API route returns flattened risk summary plus histogram base64 payload.
- Backend imports model helper from repo root (path mutation pattern exists).
- CI is intentionally simple: backend tests + Flutter analyze/test only.

## COMMANDS
```bash
python -m pip install --requirement backend/requirements.txt
python -m ruff check .
python -m pytest -m "not slow" -v
python -m pytest -m slow -v
python -m backend.main

cd flutter_app && flutter pub get
cd flutter_app && flutter analyze
cd flutter_app && flutter test
cd flutter_app && flutter run
```

## NOTES
- Avoid scanning `.venv`, `.dart_tool`, `.pytest_cache`, `.sisyphus/evidence` for architecture decisions.
- Model execution can be expensive; API tests should patch model call unless explicitly profiling.
- The model path has a real smoke test; it must run in its own pytest process because `test_main.py` stubs `pymc`.
- Request limits are mirrored in `flutter_app/lib/config/risk_limits.dart` and compared by `backend/test_contract.py`; change both sides together.
- The model fits a Student-t with `nu` estimated from the data, weak data-independent priors, analytic VaR/ES with a credible interval and a convergence gate that returns HTTP 500 rather than a number; README documents the assumptions and the explicit non-goals.
- `pytest -m slow` costs about six minutes: it fits real posteriors on four chains, and the API defaults (2000 draws) are the minimum that converges on fat-tailed data.
