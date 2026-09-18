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
| 1 | venv 3.11 reproducible + instalar pins | `chore(env): ...` | pending | versión PyMC instalada, `.venv/` ignorado |
| 2 | Correr el modelo real y arreglar incompatibilidades (PyMC 5.27 / `return_inferencedata`) | `fix(model): ...` | pending | VaR real impreso, error original documentado |
| 3 | Smoke test del camino real, marcado `slow` | `test(model): ...` | pending | test pasa local, excluido del default |
| 4 | `MAX_RETURNS` con fuente única de verdad | `refactor(contract): ...` | pending | un solo literal; tests del backend verdes |
| 5 | 422 legible en el cliente Flutter | `fix(api): ...` | pending | test Dart con `detail` como lista |
| 6 | Espejar límites del backend en validadores Flutter | `fix(ui): ...` | pending | casos límite cubiertos por test |
| 7 | Test de drift de contrato | `test(contract): ...` | pending | rename simulado rompe CI |
| 8 | CI: ruff pinneado, nombre del job, pin de Flutter | `chore(ci): ...` | pending | lint corre y falla a propósito |
| 9 | Docs: README/AGENTS al día | `docs: ...` | pending | comandos verificados |

## Riesgos

- **Flutter sin verificación local**: cualquier error de sintaxis o API en Dart se descubre en CI. Mitigación: cambios mínimos, patrones ya presentes en el archivo.
- El fix del modelo puede ser más grande de lo previsto si el pin exige cambios de API (`return_inferencedata=False` está deprecado en PyMC 5). Si supera un work unit, se documenta y se parte en dos commits.
- El test de contrato debe ser chico y no traer infraestructura nueva (nada de generadores de clientes).

## Notas de recuperación

Si la sesión se corta: `mem_search` por `portfolio-hardening`, leer este archivo, y seguir desde
la primera task en `pending`.
