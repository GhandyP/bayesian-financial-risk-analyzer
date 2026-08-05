# Analisis de Riesgo Financiero - PyMC + Flutter

Aplicacion pequena compuesta por un helper PyMC, una API FastAPI y una app Flutter. Estima el Valor en Riesgo (VaR), la probabilidad de superar un umbral de perdida y una visualizacion del resultado.

## Quick path

Desde la raíz del proyecto:

1. Instala las dependencias Python:

   ```bash
   python -m pip install --requirement backend/requirements.txt
   ```

2. Ejecuta los tests del backend:

   ```bash
   python -m pytest backend/test_main.py -v
   ```

3. Inicia la API:

   ```bash
   python -m backend.main
   ```

4. En otra terminal, instala y verifica Flutter:

   ```bash
   cd flutter_app
   flutter pub get
   flutter analyze
   flutter test
   ```

## Architecture

```text
Flutter (lib/main.dart)
  -> ApiService.analyse()
FastAPI (backend/main.py)
  -> run_risk_analysis()
PyMC (Analisis_Riesgo_PyMC.py)
  -> RiskResponse-compatible summary and Base64 PNG histogram
```

## Backend configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Host where the service listens | `127.0.0.1` |
| `API_PORT` | Service port | `8000` |
| `API_CORS_ORIGINS` | Comma-separated allowed origins | Localhost ports `3000` and `5173` |

Example:

```bash
export API_HOST=127.0.0.1
export API_PORT=8000
export API_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
python -m backend.main
```

## API contract

`POST /analyse` accepts historical returns as proportions, for example `-0.012` means `-1.2%`.

Request fields:

| Field | Type | Default | Constraints |
|-------|------|---------|-------------|
| `returns` | `number[]` | Required | 10 to 2000 finite values |
| `investment_amount` | `number` | `1000000` | Greater than zero |
| `var_confidence` | `number` | `0.95` | `0.8 <= value < 1.0` |
| `loss_threshold` | `number` | `50000` | Non-negative |
| `draws` | `integer` | `2000` | `500..10000` |
| `tune` | `integer` | `1000` | `200..10000` |
| `target_accept` | `number` | `0.9` | `0.5..0.99` |

The response contains `var_value`, `threshold_probability`, the echoed risk parameters, `parameter_means` and `histogram_base64`. Full posterior samples are intentionally not returned by the API.

Example:

```bash
curl -X POST http://127.0.0.1:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"returns":[-0.012,0.008,-0.004,0.01,-0.006,0.007,-0.003,0.005,-0.002,0.004]}'
```

## Flutter configuration

The API endpoint is configured with `String.fromEnvironment` in `lib/config/api_config.dart`.

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
flutter build apk --dart-define=API_BASE_URL=https://api.example.com
```

The default is `http://127.0.0.1:8000`. Android emulators generally need `10.0.2.2` to reach a backend running on the host machine.

## Verification

```bash
python -m pytest backend/test_main.py -v
cd flutter_app && flutter analyze
cd flutter_app && flutter test
```

The backend tests mock the expensive PyMC and Matplotlib integrations for API contract checks, and cover the 400 (model error) and 504 (timeout) branches. The model still performs defensive validation before sampling, including finite values and the 2000-return upper bound. Flutter tests cover parsing, the input/result widgets and the API service with a mocked HTTP client.

## Troubleshooting

- **CORS**: Add the exact frontend origin, including its port, to `API_CORS_ORIGINS`.
- **Connection from Android emulator**: Use `http://10.0.2.2:8000` through `--dart-define=API_BASE_URL=...`.
- **Memory or latency**: Reduce `draws` and `tune` within their accepted ranges.
- **Histogram errors**: Verify that the pinned Matplotlib dependency is installed correctly.
