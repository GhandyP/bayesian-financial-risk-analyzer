# Feature: portfolio-hardening

**Branch**: `feat/portfolio-hardening`
**Base**: `main` @ `a7ef7d2`
**Owner**: parent session (el Gentleman)

## Objetivo

Cerrar el entregable (a): que el repositorio no afirme más de lo que puede respaldar.

Hoy el camino real del producto (PyMC ejecutándose) **nunca se ejecutó**: todos los tests lo
mockean y CI tampoco lo corre. En paralelo, lo que la UI valida y lo que el backend acepta
divergen, y el único error que ese drift produce (422) es exactamente el que la UI no sabe
mostrar.

## Definición de terminado

1. `run_risk_analysis` corre de verdad con los pins de `backend/requirements.txt` en Python 3.11 y devuelve un VaR.
2. Existe un test que ejecuta el modelo real y está marcado `slow` (el camino del producto deja de estar sin cobertura).
3. Un 422 del backend se muestra legible en la UI, no como JSON crudo.
4. Ningún límite del backend queda sin espejo en Flutter.
5. Un rename de un campo del response rompe CI.
6. CI: lint Python real y pinneado, nombre del job veraz, SDK de Flutter pinneado.
7. README y AGENTS.md describen el estado nuevo (verificación y comandos).

**Estado: cerrado.** Los 9 work units están commiteados en `feat/portfolio-hardening` y la
suite queda en 18 tests rápidos + 2 smoke reales, más `ruff check .` limpio.

Queda pendiente fuera del código: **nada de esto pasó por CI todavía** (no hubo push) y los
cambios de Dart solo están verificados por inspección local, porque Flutter no está instalado
en la máquina de trabajo. Los tests de contrato cubren parte de ese hueco verificando las
constantes Dart contra Pydantic, pero no la sintaxis ni el render.

## Restricciones del entorno

- **Flutter no está instalado** en la máquina de trabajo: los cambios en Dart se verifican por inspección + CI. Declararlo en el reporte final.
- Python 3.11.15 disponible vía `uv`; el global (3.13) **no** reproduce los pins.
- Commits atómicos: uno por task, conventional commits. Sin push ni PR (decisión del usuario).

## Tasks

| # | Task | Commit | Estado | Evidencia |
|---|---|---|---|---|
| 1 | venv 3.11 reproducible + instalar pins | sin commit (`.venv/` está ignorado) | **DONE** | `.venv` con pymc 5.27.1, numpy 2.2.2, pandas 2.2.3, matplotlib 3.10.0, fastapi 0.115.8 |
| 2 | Correr el modelo real y arreglar incompatibilidades | `910f5e1` `fix(model)` | **DONE** | `TypeError: sample_posterior_predictive() got an unexpected keyword argument 'samples'`; tras el fix, POST /analyse devuelve 200 en 14.6s con PNG válido |
| 3 | Smoke test del camino real, marcado `slow` | `ed13167` `test(model)` | **DONE** | `pytest backend/test_model_smoke.py -m slow` → 2 passed en 25.6s; suite rápida 16 passed, 2 deselected |
| 4 | `MAX_RETURNS` con fuente única de verdad | `3eb1eb1` `refactor(contract)` | **DONE** | `risk_limits.py`; identidad `is` verificada y la capa Pydantic no importa PyMC |
| 5 | 422 legible en el cliente Flutter | `9ba6dc8` `fix(api)` | **DONE** | `detail` como lista formateado a `campo: mensaje`; fixture capturado del backend real, no inventado |
| 6 | Espejar límites del backend en validadores Flutter | `6d2213f` `fix(ui)` | **DONE** | `risk_limits.dart` + rechazo de no finitos; verificado contra Pydantic por el test de contrato |
| 7 | Test de drift de contrato | `1977463` `test(contract)` | **DONE** | 2 pruebas negativas simuladas: cambiar un límite en Dart y renombrar un campo del response hacen fallar la suite; restaurado, pasa |
| 8 | CI: ruff pinneado, nombre del job, pin de Flutter | `c3cae51` `chore(ci)` | **DONE** | `ruff check .` → All checks passed; 11 hallazgos reales arreglados; Flutter pinneado a 3.47.0 |
| 9 | Docs: README/AGENTS al día | `07c0e8d` `docs` | **DONE** | Los 4 documentos actualizados; cada comando documentado fue ejecutado antes de escribirlo |

## Bitácora de hallazgos medidos (no inferidos)

1. **El camino real estaba roto al 100%.** Con `pymc==5.27.1`, `pm.sample_posterior_predictive` ya
   no acepta `samples=` y devuelve un `InferenceData` por defecto. `run_risk_analysis` lanzaba
   `TypeError` siempre, así que POST /analyse devolvía 500 para cualquier request. Los 16 tests
   pasaban porque `test_main.py` reemplaza `pymc` por un `MagicMock`.
2. **`return_inferencedata=False` en `pm.sample` NO rompe** en la versión pinneada: la sospecha
   quedó descartada con una corrida real. Sigue siendo API legada, pero no es un bug.
3. **Latencia real medida**: 13.6s con los defaults (`draws=2000, tune=1000`), 10.2s con el
   mínimo (`draws=500, tune=200`), 14.6s el request HTTP completo con 10 retornos. Muy por
   debajo del timeout de 120s del backend.
4. **El 422 confirmado como lista**: `detail = [{"loc": ["body", "draws"], "msg": "Input
   should be less than or equal to 10000", ...}]`. El cliente solo sabe formatear `detail`
   como `String` o `Map`, así que hoy muestra el JSON crudo (task 5).
5. **La predictiva se aplana sobre las observaciones**: 10000 valores = 1000 muestras
   posteriores x 10 observaciones. Documentado en `model-reliability` como insumo de la fase (c).
6. **CI no habría detectado ningún test nuevo**: el step apuntaba a `backend/test_main.py`
   explícitamente, así que cualquier archivo de test agregado habría quedado fuera sin aviso.
   Ahora corre `pytest -m "not slow" -v`, que colecta la suite rápida completa.
7. **Ruff encontró 11 problemas reales** en el código que ya estaba: imports de `typing`
   deprecados, un `with ... as model` sin uso, imports desordenados, `asyncio.TimeoutError`
   aliasado y un `raise` sin encadenar. Los 7 `E402` restantes son consecuencia del
   `sys.path.insert` antes de los imports: quedaron como deuda aceptada y documentada en
   `ruff.toml`, no como `# noqa` sueltos por línea.

## Riesgos

- **Flutter sin verificación local**: cualquier error de sintaxis o API en Dart se descubre en CI. Mitigación aplicada: cambios mínimos, patrones ya presentes en el archivo, y el test de contrato para los valores.
- El fix del modelo resultó ser de dos líneas, no un rediseño: la sospecha sobre `return_inferencedata` no se confirmó. Cerrado.
- El test de contrato quedó chico y sin infraestructura nueva: un JSON generado, un regex sobre las constantes Dart y dos asserts. Cerrado.
- **Riesgo abierto**: el pin de Flutter a `3.47.0` no se pudo validar localmente. Congela lo que el channel `stable` ya resolvía, pero si `flutter analyze` se queja con ese SDK, se ve recién en CI.

## Notas de recuperación

Si la sesión se corta: `mem_search` por `portfolio-hardening`, leer este archivo, y seguir desde
la primera task en `pending`.
