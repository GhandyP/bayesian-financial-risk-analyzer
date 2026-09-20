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

The response contains `var_value`, `var_value_lower`, `var_value_upper`, `expected_shortfall`, `threshold_probability`, the echoed risk parameters, `parameter_means`, `histogram_base64` and a `diagnostics` object (`max_rhat`, `min_ess`, `divergences`, `converged`). Full posterior samples are intentionally not returned by the API.

Example:

```bash
curl -X POST http://127.0.0.1:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"returns":[-0.012,0.008,-0.004,0.01,-0.006,0.007,-0.003,0.005,-0.002,0.004]}'
```

## Supuestos del modelo estadistico

El modelo ajusta una unica serie de retornos con verosimilitud Student-t. Sus supuestos
y sus limites, explicitos:

- **Verosimilitud**: Student-t con `nu` estimado de los datos, con piso en 2 para que la
  varianza sea finita y el ES quede definido. `nu` grande equivale al modelo Normal.
- **Priors**: debiles e independientes de los datos. No se usan `mean()` ni `std()` de la
  muestra: eso haria entrar los datos dos veces, por el prior y por la verosimilitud.
- **Con muestras cortas el prior es un insumo real**: con 10 observaciones la volatilidad
  posterior queda alrededor de 30% por encima del valor de maxima verosimilitud. Por eso la
  respuesta informa un intervalo creible: con pocos datos, la incertidumbre es el resultado.
- **`desviacion_retorno` es la desviacion estandar**, no la escala de la Student-t.
- **VaR y ES** salen de la forma cerrada de la Student-t, evaluada en cada muestra posterior.
  El VaR viene con un intervalo creible 5-95%: es incertidumbre sobre los parametros, no
  ruido de Monte Carlo.

## Que NO modela

- **Volatilidad condicional**: no hay GARCH ni clustering; la volatilidad se supone constante.
- **Dependencia temporal**: los retornos se tratan como i.i.d. dentro de la ventana.
- **Multi-activo**: una sola serie, sin correlaciones.
- **Horizonte**: un periodo, el de los datos de entrada.
- **`nu` con series muy cortas**: con 10 observaciones el valor reportado refleja el prior,
  no evidencia.
- **El backtest de cobertura es sintetico**, no sobre datos de mercado: no es un backtest
  regulatorio.

## Convergencia

El muestreo corre 4 cadenas y la respuesta se emite solo si el posterior pasa los umbrales:
`rhat <= 1.01`, ESS >= 400 y divergencias <= 0.5% de las muestras. Si no los pasa, la API
responde 500 con el diagnostico en el mensaje, en lugar de devolver un numero que no se puede
distinguir de uno valido.

## Costo

Con los valores por defecto (`draws=2000`, `tune=1000`, 4 cadenas) un request tarda alrededor
de 45-75 segundos, y el timeout del backend es de 120 segundos. La API acepta `draws` desde 500,
pero **500 no converge con colas gruesas** (medido: rhat 1.026, ESS 258), asi que ese request
devuelve 500. Para uso real, `draws >= 2000`.

## Evidencia de verificacion

- **Cobertura out-of-sample**: 25 excedencias sobre 450 puntos, 5.56% contra un 5% nominal,
  sobre datos sinteticos con colas conocidas (`nu` verdadero 4).
- **Formas cerradas**: VaR y ES coinciden con una simulacion de 4 millones de muestras con
  0.17% de error.
- **Corrida real** sobre el payload de ejemplo: VaR 12.902, intervalo 6.598-21.674, ES 18.094,
  rhat 1.003, ESS 4290, 0 divergencias.

## Flutter configuration

The API endpoint is configured with `String.fromEnvironment` in `lib/config/api_config.dart`.

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
flutter build apk --dart-define=API_BASE_URL=https://api.example.com
```

The default is `http://127.0.0.1:8000`. Android emulators generally need `10.0.2.2` to reach a backend running on the host machine.

## Verification

```bash
# Fast suite: API, contract and lint checks
python -m pip install --requirement backend/requirements.txt
python -m ruff check .
python -m pytest -m "not slow" -v

# Real model runs: execute PyMC instead of stubbing it (~6 min total)
python -m pytest -m slow -v

cd flutter_app && flutter analyze
cd flutter_app && flutter test
```

The backend tests mock the expensive PyMC and Matplotlib integrations for API contract checks, and cover the 400 (model error) and 504 (timeout) branches. `backend/test_model_smoke.py` is the only suite that runs the real sampler, so it is excluded from the default run through the `slow` marker in `pytest.ini` and must be invoked on its own: `test_main.py` installs a `pymc` stub in `sys.modules`.

`backend/test_contract.py` links the two hand-written sides of the contract. It regenerates the response example that the Dart suite decodes and compares the Flutter limit constants (`lib/config/risk_limits.dart`) against the Pydantic constraints, so a renamed field or a one-sided bound change fails in CI instead of at runtime. After an intended schema change, regenerate the example:

```bash
python -m backend.test_contract
```

Flutter tests cover parsing, the input/result widgets and the API service with a mocked HTTP client.

## Troubleshooting

- **CORS**: Add the exact frontend origin, including its port, to `API_CORS_ORIGINS`.
- **Connection from Android emulator**: Use `http://10.0.2.2:8000` through `--dart-define=API_BASE_URL=...`.
- **Memory or latency**: Reduce `draws` and `tune` within their accepted ranges.
- **Histogram errors**: Verify that the pinned Matplotlib dependency is installed correctly.
