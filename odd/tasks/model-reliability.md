# Feature: model-reliability

**Branch**: `feat/model-reliability` (encadenada sobre `feat/portfolio-hardening`)
**Owner**: parent session (el Gentleman)
**Depende de**: `portfolio-hardening` (necesita el venv y el smoke test del camino real)

## Objetivo

Cerrar el entregable (c): que "herramienta de riesgo confiable" sea una afirmación respaldada y
no una etiqueta. El problema no es la aplicación, es la estadística.

Evidencia del estado actual:

| Hecho | Archivo | Consecuencia |
|---|---|---|
| Likelihood `Normal` | `Analisis_Riesgo_PyMC.py:78` | Colas livianas por construcción: el VaR subestima riesgo de cola |
| Prior `Normal(mu=mean(returns))` | `Analisis_Riesgo_PyMC.py:71-72` | Los datos entran por el prior **y** por el likelihood |
| Sin `rhat`/`ess`/`divergences` en ningún lado | todo el archivo | Si el sampler no converge, se devuelve un número igual |
| Solo se reporta el VaR puntual | `Analisis_Riesgo_PyMC.py:97-98` | Sin incertidumbre ni medida de cola (ES) |

## Decisiones metodológicas (tomadas con el usuario)

- **t-Student** como likelihood, para colas gruesas. Reemplaza la Normal.
- **Priors débiles independientes de los datos**: se elimina el doble uso.
- **Diagnósticos de convergencia visibles**: si no converge, no se devuelve un número en silencio.
- **ES (expected shortfall)** e **intervalo de incertidumbre del VaR** en el contrato de respuesta.
- **Backtest de cobertura** sobre datos sintéticos con colas conocidas (sin dependencias externas ni red).

## Fuera de alcance (decidido explícitamente)

- GARCH / volatilidad condicional: el salto de tamaño no está justificado en esta fase.
- Datos de mercado reales: requeriría una dependencia de descarga y acceso a red.

## Tasks

| # | Task | Commit | Estado | Evidencia |
|---|---|---|---|---|
| 1 | Diagnósticos de convergencia (rhat, ESS, divergencias) visibles | `feat(model): ...` | pending | valores impresos en una corrida real |
| 2 | Likelihood t-Student con `nu` estimado | `feat(model): ...` | pending | VaR de cola crece frente a la Normal bajo el mismo input |
| 3 | Priors independientes de los datos | `refactor(model): ...` | pending | sin `returns.mean()` en los priors |
| 4 | ES + intervalo de incertidumbre del VaR en el contrato (API + Dart + UI) | `feat(api): ...` | pending | campos nuevos en response y renderizados |
| 5 | Backtest de cobertura sobre datos sintéticos con colas conocidas | `test(model): ...` | pending | tabla cobertura esperada vs observada |
| 6 | Docs: supuestos estadísticos y qué NO modela la herramienta | `docs: ...` | pending | sección de límites en README |

## Restricciones

- Cada task conserva los tests existentes verdes.
- Los campos nuevos del contrato (task 4) tocan Python **y** Dart: usar el test de drift de `portfolio-hardening` como red.
- Flutter sin verificación local: el render de campos nuevos se inspecciona y se valida en CI.
- El backtest debe ser determinista (semilla fija) para no producir fallos intermitentes.

## Notas de recuperación

`mem_search` por `model-reliability`, leer este archivo, seguir desde la primera task en `pending`.
