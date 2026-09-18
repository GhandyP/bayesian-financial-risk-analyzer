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
| 4 | `MAX_RETURNS` con fuente única de verdad | `refactor(contract): ...` | pending | un solo literal; tests del backend verdes |
| 5 | 422 legible en el cliente Flutter | `fix(api): ...` | pending | test Dart con `detail` como lista |
| 6 | Espejar límites del backend en validadores Flutter | `fix(ui): ...` | pending | casos límite cubiertos por test |
| 7 | Test de drift de contrato | `test(contract): ...` | pending | rename simulado rompe CI |
| 8 | CI: ruff pinneado, nombre del job, pin de Flutter | `chore(ci): ...` | pending | lint corre y falla a propósito |
| 9 | Docs: README/AGENTS al día | `docs: ...` | pending | comandos verificados |

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

## Riesgos

- **Flutter sin verificación local**: cualquier error de sintaxis o API en Dart se descubre en CI. Mitigación: cambios mínimos, patrones ya presentes en el archivo.
- El fix del modelo puede ser más grande de lo previsto si el pin exige cambios de API (`return_inferencedata=False` está deprecado en PyMC 5). Si supera un work unit, se documenta y se parte en dos commits.
- El test de contrato debe ser chico y no traer infraestructura nueva (nada de generadores de clientes).

## Notas de recuperación

Si la sesión se corta: `mem_search` por `portfolio-hardening`, leer este archivo, y seguir desde
la primera task en `pending`.
