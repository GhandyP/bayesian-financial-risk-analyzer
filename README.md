# Bayesian Financial Risk Analyzer

A FastAPI service, Bayesian PyMC model, and Flutter app for estimating Value at Risk (VaR), expected shortfall (ES), and the posterior probability of exceeding a loss threshold from one return series.

## Contents

- [Overview and features](#en-overview-and-features)
- [Requirements and tested versions](#en-requirements-and-tested-versions)
- [Quick start](#en-quick-start)
- [Architecture and project layout](#en-architecture-and-project-layout)
- [Configuration](#en-configuration)
- [API request and response](#en-api-request-and-response)
- [HTTP errors](#en-http-errors)
- [Model interpretation and assumptions](#en-model-interpretation-and-assumptions)
- [Convergence, limitations, and non-goals](#en-convergence-limitations-and-non-goals)
- [Validation and CI](#en-validation-and-ci)
- [Troubleshooting](#en-troubleshooting)

<a id="en-overview-and-features"></a>
## Overview and features

- `POST /analyse` analyzes 10–2000 finite returns expressed as proportions.
- Returns VaR, ES, posterior probability of exceeding a loss threshold, VaR uncertainty bounds, convergence diagnostics, and a Base64-encoded PNG histogram.
- A Flutter app submits inputs and presents results.

<a id="en-requirements-and-tested-versions"></a>
## Requirements and tested versions

| Component | Declared or CI-tested fact |
|---|---|
| Python | CI uses Python 3.11. No independent minimum Python version is declared. |
| Flutter | CI uses Flutter 3.47.0. This is not a minimum-version claim. |
| Dart | Declared SDK constraint: `>=3.0.0 <4.0.0`. |

<a id="en-quick-start"></a>
## Quick start

### API

From the repository root, install dependencies and start the service:

```bash
python -m pip install --requirement backend/requirements.txt
python -m backend.main
```

By default, the API listens at `http://127.0.0.1:8000`.

### Flutter

In another terminal:

```bash
cd flutter_app
flutter pub get
flutter run
```

The app defaults to `http://127.0.0.1:8000`. Android emulators often need `http://10.0.2.2:8000`; see [Configuration](#en-configuration).

<a id="en-architecture-and-project-layout"></a>
## Architecture and project layout

```text
Flutter (flutter_app/lib/main.dart)
  -> ApiService.analyse()
FastAPI (backend/main.py)
  -> run_risk_analysis()
PyMC model (Analisis_Riesgo_PyMC.py)
```

| Path | Responsibility |
|---|---|
| `Analisis_Riesgo_PyMC.py` | Model fitting and risk measure calculation. |
| `risk_limits.py` | Shared backend input limits. |
| `backend/main.py` | API configuration and routes. |
| `backend/models.py` | Request and response schemas and validation. |
| `backend/` | API, contract, and model tests. |
| `flutter_app/lib/` | App, HTTP service, configuration, and widgets. |
| `flutter_app/test/` | Flutter tests. |

<a id="en-configuration"></a>
## Configuration

### Backend

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `127.0.0.1` | Interface on which the service listens. |
| `API_PORT` | `8000` | Service port. |
| `API_CORS_ORIGINS` | `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:5173`, `http://127.0.0.1:5173` | Comma-separated allowed origins. CORS credentials are disabled. |

Example:

```bash
export API_HOST=127.0.0.1
export API_PORT=8000
export API_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
python -m backend.main
```

### Flutter

`flutter_app/lib/config/api_config.dart` reads `API_BASE_URL` through `String.fromEnvironment`. Its default is `http://127.0.0.1:8000`; the app posts to `/analyse`.

```bash
cd flutter_app
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

<a id="en-api-request-and-response"></a>
## API request and response

`POST /analyse` accepts finite returns expressed as proportions; for example, `-0.012` represents `-1.2%`.

### Request

| Field | Type | Default | Constraint |
|---|---|---:|---|
| `returns` | `number[]` | Required | 10–2000 finite values. |
| `investment_amount` | `number` | `1000000` | Greater than zero. |
| `var_confidence` | `number` | `0.95` | `0.8 <= value < 1`. |
| `loss_threshold` | `number` | `50000` | Greater than or equal to zero. |
| `draws` | `integer` | `2000` | 500–10000. |
| `tune` | `integer` | `1000` | 200–10000. |
| `target_accept` | `number` | `0.9` | 0.5–0.99. |

Example using defaults:

```bash
curl -X POST http://127.0.0.1:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"returns":[-0.012,0.008,-0.004,0.01,-0.006,0.007,-0.003,0.005,-0.002,0.004]}'
```

### Response

Monetary loss values use the caller-selected unit of `investment_amount`; the API specifies no currency. `threshold_probability` is between 0 and 1, not a percentage.

| Field | Type | Meaning |
|---|---|---|
| `var_value` | `float` | Mean VaR across posterior draws, describing a loss quantile at `var_confidence`. The posterior mean itself is not asserted to have an exact exceedance frequency. |
| `var_value_lower`, `var_value_upper` | `float` | 5th and 95th posterior percentiles of VaR, representing parameter uncertainty—not a loss range or Monte Carlo error. |
| `expected_shortfall` | `float` | Expected loss conditional on being in the tail defined by the confidence level. |
| `threshold_probability` | `float` | Posterior probability that loss exceeds `loss_threshold`. |
| `investment_amount`, `var_confidence`, `loss_threshold` | `float` | Risk inputs echoed in the response. |
| `parameter_means` | `object` | Posterior means of `media_retorno`, `desviacion_retorno`, and `nu`. |
| `histogram_base64` | `string` | PNG histogram encoded as Base64. |
| `diagnostics` | `object` | `max_rhat`, `min_ess`, `divergences`, and `converged`. |

Full posterior samples are not returned.

<a id="en-http-errors"></a>
## HTTP errors

| Status | Meaning |
|---:|---|
| `422` | Invalid request; includes a `detail` list of validation errors. |
| `400` | The model raised `ValueError`. |
| `500` | Convergence gate failed; response detail includes diagnostics. |
| `504` | Inference exceeded the 120-second timeout. |

<a id="en-model-interpretation-and-assumptions"></a>
## Model interpretation and assumptions

- Fits one return series with a Student-t likelihood; `nu` is estimated with a floor of 2.
- Uses weak, data-independent priors.
- Assumes constant volatility and returns that are independent and identically distributed within the input window.
- Computes VaR and ES analytically for each posterior draw.
- The analysis horizon is one period, corresponding to the supplied returns.

<a id="en-convergence-limitations-and-non-goals"></a>
## Convergence, limitations, and non-goals

Sampling uses four chains. Results are returned only when all gates pass:

| Diagnostic | Gate |
|---|---:|
| Maximum R-hat | `<= 1.01` |
| Minimum ESS | `>= 400` |
| Divergences | `<= 0.5%` |

There is no automatic retry. A failed gate produces HTTP `500` with diagnostic information. The model does not include GARCH or other time-varying volatility, temporal dependence, or multi-asset analysis. It is not a multi-period model. No empirical performance or coverage figures are asserted here.

<a id="en-validation-and-ci"></a>
## Validation and CI

CI runs Ruff, fast and slow Python tests, and Flutter analysis and tests. From the repository root:

```bash
python -m ruff check .
python -m pytest -m "not slow" -v
python -m pytest -m slow --ignore=backend/test_main.py -v
```

The slow-test command excludes `backend/test_main.py` because it stubs `pymc`; the slow tests need the real package. Flutter commands:

```bash
cd flutter_app
flutter pub get
flutter analyze
flutter test
```

<a id="en-troubleshooting"></a>
## Troubleshooting

| Symptom | Check |
|---|---|
| Android app cannot connect to the API | Set `API_BASE_URL=http://10.0.2.2:8000` using `--dart-define`. |
| Frontend gets a CORS error | Add the exact origin, including port, to `API_CORS_ORIGINS`. |
| HTTP `500` with diagnostics | Review convergence metrics; the API does not retry automatically. |
| HTTP `504` | Inference exceeded the 120-second timeout. |

---

# Analizador de riesgo financiero bayesiano

Servicio FastAPI, modelo bayesiano PyMC y aplicación Flutter para estimar Value at Risk (VaR), expected shortfall (ES) y la probabilidad posterior de superar un umbral de pérdida a partir de una serie de retornos.

## Contenido

- [Resumen y funcionalidades](#es-resumen-y-funcionalidades)
- [Requisitos y versiones verificadas](#es-requisitos-y-versiones-verificadas)
- [Inicio rápido](#es-inicio-rápido)
- [Arquitectura y estructura del proyecto](#es-arquitectura-y-estructura-del-proyecto)
- [Configuración](#es-configuración)
- [Solicitud y respuesta de la API](#es-solicitud-y-respuesta-de-la-api)
- [Errores HTTP](#es-errores-http)
- [Interpretación y supuestos del modelo](#es-interpretación-y-supuestos-del-modelo)
- [Convergencia, límites y objetivos excluidos](#es-convergencia-límites-y-objetivos-excluidos)
- [Validación y CI](#es-validación-y-ci)
- [Solución de problemas](#es-solución-de-problemas)

<a id="es-resumen-y-funcionalidades"></a>
## Resumen y funcionalidades

- `POST /analyse` analiza entre 10 y 2000 retornos finitos expresados como proporciones.
- Devuelve VaR, ES, probabilidad posterior de superar un umbral de pérdida, límites de incertidumbre del VaR, diagnósticos de convergencia e histograma PNG codificado en Base64.
- Una aplicación Flutter envía las entradas y presenta los resultados.

<a id="es-requisitos-y-versiones-verificadas"></a>
## Requisitos y versiones verificadas

| Componente | Hecho declarado o comprobado en CI |
|---|---|
| Python | CI usa Python 3.11. No se declara una versión mínima independiente de Python. |
| Flutter | CI usa Flutter 3.47.0. Esto no implica que sea una versión mínima. |
| Dart | Restricción declarada del SDK: `>=3.0.0 <4.0.0`. |

<a id="es-inicio-rápido"></a>
## Inicio rápido

### API

Desde la raíz del repositorio, instala las dependencias e inicia el servicio:

```bash
python -m pip install --requirement backend/requirements.txt
python -m backend.main
```

De forma predeterminada, la API escucha en `http://127.0.0.1:8000`.

### Flutter

En otra terminal:

```bash
cd flutter_app
flutter pub get
flutter run
```

La aplicación usa `http://127.0.0.1:8000` de forma predeterminada. Los emuladores Android suelen necesitar `http://10.0.2.2:8000`; consulta [Configuración](#es-configuración).

<a id="es-arquitectura-y-estructura-del-proyecto"></a>
## Arquitectura y estructura del proyecto

```text
Flutter (flutter_app/lib/main.dart)
  -> ApiService.analyse()
FastAPI (backend/main.py)
  -> run_risk_analysis()
Modelo PyMC (Analisis_Riesgo_PyMC.py)
```

| Ruta | Responsabilidad |
|---|---|
| `Analisis_Riesgo_PyMC.py` | Ajuste del modelo y cálculo de medidas de riesgo. |
| `risk_limits.py` | Límites compartidos de entrada del backend. |
| `backend/main.py` | Configuración y rutas de la API. |
| `backend/models.py` | Esquemas y validación de solicitudes y respuestas. |
| `backend/` | Pruebas de API, contrato y modelo. |
| `flutter_app/lib/` | Aplicación, servicio HTTP, configuración y widgets. |
| `flutter_app/test/` | Pruebas de Flutter. |

<a id="es-configuración"></a>
## Configuración

### Backend

| Variable | Valor predeterminado | Descripción |
|---|---|---|
| `API_HOST` | `127.0.0.1` | Interfaz en la que escucha el servicio. |
| `API_PORT` | `8000` | Puerto del servicio. |
| `API_CORS_ORIGINS` | `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:5173`, `http://127.0.0.1:5173` | Orígenes permitidos separados por comas. Las credenciales CORS están desactivadas. |

Ejemplo:

```bash
export API_HOST=127.0.0.1
export API_PORT=8000
export API_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
python -m backend.main
```

### Flutter

`flutter_app/lib/config/api_config.dart` lee `API_BASE_URL` mediante `String.fromEnvironment`. Su valor predeterminado es `http://127.0.0.1:8000`; la aplicación envía solicitudes a `/analyse`.

```bash
cd flutter_app
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

<a id="es-solicitud-y-respuesta-de-la-api"></a>
## Solicitud y respuesta de la API

`POST /analyse` acepta retornos finitos expresados como proporciones; por ejemplo, `-0.012` representa `-1.2%`.

### Solicitud

| Campo | Tipo | Predeterminado | Restricción |
|---|---|---:|---|
| `returns` | `number[]` | Obligatorio | 10–2000 valores finitos. |
| `investment_amount` | `number` | `1000000` | Mayor que cero. |
| `var_confidence` | `number` | `0.95` | `0.8 <= valor < 1`. |
| `loss_threshold` | `number` | `50000` | Mayor o igual a cero. |
| `draws` | `integer` | `2000` | 500–10000. |
| `tune` | `integer` | `1000` | 200–10000. |
| `target_accept` | `number` | `0.9` | 0.5–0.99. |

Ejemplo con los valores predeterminados:

```bash
curl -X POST http://127.0.0.1:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{"returns":[-0.012,0.008,-0.004,0.01,-0.006,0.007,-0.003,0.005,-0.002,0.004]}'
```

### Respuesta

Los montos de pérdida usan la unidad elegida por quien llama para `investment_amount`; la API no fija una moneda. `threshold_probability` está entre 0 y 1, no es un porcentaje.

| Campo | Tipo | Significado |
|---|---|---|
| `var_value` | `float` | VaR medio entre las muestras posteriores, que describe un cuantil de pérdida al nivel `var_confidence`. No se afirma que la propia media posterior tenga una frecuencia exacta de excedencia. |
| `var_value_lower`, `var_value_upper` | `float` | Percentiles 5 y 95 posteriores del VaR: representan incertidumbre de los parámetros, no un rango de pérdidas ni error Monte Carlo. |
| `expected_shortfall` | `float` | Pérdida esperada condicionada a estar en la cola definida por el nivel de confianza. |
| `threshold_probability` | `float` | Probabilidad posterior de que la pérdida supere `loss_threshold`. |
| `investment_amount`, `var_confidence`, `loss_threshold` | `float` | Parámetros de riesgo recibidos y devueltos. |
| `parameter_means` | `object` | Medias posteriores de `media_retorno`, `desviacion_retorno` y `nu`. |
| `histogram_base64` | `string` | Histograma PNG codificado en Base64. |
| `diagnostics` | `object` | `max_rhat`, `min_ess`, `divergences` y `converged`. |

No se devuelven las muestras posteriores completas.

<a id="es-errores-http"></a>
## Errores HTTP

| Estado | Significado |
|---:|---|
| `422` | Solicitud inválida; incluye una lista `detail` con errores de validación. |
| `400` | El modelo generó `ValueError`. |
| `500` | Falló el control de convergencia; el detalle incluye diagnósticos. |
| `504` | La inferencia superó el tiempo límite de 120 segundos. |

<a id="es-interpretación-y-supuestos-del-modelo"></a>
## Interpretación y supuestos del modelo

- Ajusta una serie de retornos con una verosimilitud Student-t; `nu` se estima con un piso de 2.
- Usa priors débiles e independientes de los datos.
- Supone volatilidad constante y retornos independientes e idénticamente distribuidos dentro de la ventana de entrada.
- Calcula VaR y ES analíticamente para cada muestra posterior.
- El horizonte del análisis es un periodo, correspondiente a los retornos proporcionados.

<a id="es-convergencia-límites-y-objetivos-excluidos"></a>
## Convergencia, límites y objetivos excluidos

El muestreo usa cuatro cadenas. Solo se devuelven resultados si se superan todos estos controles:

| Diagnóstico | Control |
|---|---:|
| R-hat máximo | `<= 1.01` |
| ESS mínimo | `>= 400` |
| Divergencias | `<= 0.5%` |

No hay reintento automático. Si falla un control, la API responde `500` con información diagnóstica. El modelo no incluye GARCH ni otra volatilidad variable en el tiempo, dependencia temporal ni análisis multi-activo. No es un modelo de varios periodos. Aquí no se afirman cifras empíricas de rendimiento ni cobertura.

<a id="es-validación-y-ci"></a>
## Validación y CI

CI ejecuta Ruff, las pruebas Python rápidas y lentas, y el análisis y las pruebas de Flutter. Desde la raíz del repositorio:

```bash
python -m ruff check .
python -m pytest -m "not slow" -v
python -m pytest -m slow --ignore=backend/test_main.py -v
```

El comando de pruebas lentas excluye `backend/test_main.py` porque crea un stub de `pymc`; las pruebas lentas necesitan el paquete real. Comandos de Flutter:

```bash
cd flutter_app
flutter pub get
flutter analyze
flutter test
```

<a id="es-solución-de-problemas"></a>
## Solución de problemas

| Síntoma | Comprobación |
|---|---|
| La aplicación Android no conecta con la API | Define `API_BASE_URL=http://10.0.2.2:8000` mediante `--dart-define`. |
| El frontend recibe un error CORS | Añade el origen exacto, incluido el puerto, a `API_CORS_ORIGINS`. |
| HTTP `500` con diagnósticos | Revisa las métricas de convergencia; la API no reintenta automáticamente. |
| HTTP `504` | La inferencia superó el tiempo límite de 120 segundos. |
