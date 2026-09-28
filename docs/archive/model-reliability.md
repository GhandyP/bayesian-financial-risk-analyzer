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
| 1 | Priors independientes de los datos | `2a48310` | **DONE** | sin `returns.mean()` en los priors |
| 2 | Likelihood t-Student con `nu` estimado | `fcd44e8` | **DONE** | `nu` recuperado 4.04 contra 4.0 real; VaR +7% y P(cola) 15x |
| 3 | Diagnósticos de convergencia (rhat, ESS, divergencias) | `b2cc4ce`, `b7b3e03` | **DONE** | rhat 1.003, ESS 4290, 0 divergencias; falla si no converge |
| 4 | VaR/ES analíticos + intervalo creíble | `699bc82` | **DONE** | fórmulas validadas con 0,17% de error contra 4M muestras |
| 5 | Exponer ES, intervalo y diagnósticos (API + contrato + Dart + UI) | `4c6ff18` | **DONE** | campos nuevos en el response y una tarjeta de diagnóstico en la UI |
| 6 | Backtest de cobertura sobre datos sintéticos | `e0d77ee` | **DONE** | 25/450 = 5,56% out-of-sample contra 5% nominal |
| 7 | Docs: supuestos estadísticos y límites | `0cc5098` | **DONE** | secciones nuevas en README |

## Restricciones

- Cada task conserva los tests existentes verdes.
- Los campos nuevos del contrato (task 4) tocan Python **y** Dart: usar el test de drift de `portfolio-hardening` como red.
- Flutter sin verificación local: el render de campos nuevos se inspecciona y se valida en CI.
- El backtest debe ser determinista (semilla fija) para no producir fallos intermitentes.

## Notas metodológicas descubiertas durante (a)

- **La posterior predictiva se aplana sobre las observaciones.** Con `draws=500` y 2 cadenas,
  `simulated_losses` tiene 10000 valores = 1000 muestras posteriores x 10 observaciones
  (`Analisis_Riesgo_PyMC.py:93`). Las 10 predicciones por muestra son iid del mismo Normal,
  así que el VaR es correcto, pero el conteo *independiente* de muestras es el tamaño de la
  posterior (1000), no 10000. Efecto: el error de Monte Carlo del VaR se subestima.
  En la task 2 conviene simular una muestra de retorno por muestra posterior (por ejemplo
  desde la posterior de `mu`/`sigma`) en lugar de predecir las observaciones observadas.
- **Documentado y verificado**: el tamaño de la predictiva ya no se puede fijar con un
  parámetro; escala con `draws` x cadenas x observaciones. El `draws` del request pasó a
  controlar el costo de la simulación, no solo el muestreo.

## Task 4: campos nuevos del contrato

- `expected_shortfall` (ES) e intervalo de incertidumbre del VaR (`var_value_lower`,
  `var_value_upper`).

## Estado final

Cerrado. Los 7 work units están commiteados y pusheados en `feat/model-reliability`, sobre los 9
de `feat/portfolio-hardening`.

### Hallazgos medidos

1. **Priors empíricos**: `returns.mean()`/`std()` dentro del prior hacían entrar los datos dos
   veces. Medido: con 10 observaciones el efecto sobre el VaR es chico (13.895 -> 13.846), así que
   la corrección es metodológica y hay que decir que numéricamente es menor en ese input.
2. **Mi primer prior de volatilidad inflaba sigma 57%** sobre el máximo de verosimilitud
   (0.01059 contra 0.00677). Aislado con tres variantes en un script fuera del repo (Normal,
   t con `nu` fijo, t con `nu` estimado): las tres quedaban 20-30% arriba, así que la culpa era el
   centro del prior, no la verosimilitud. Reemplazado por un prior log-normal, invariante de escala:
   0.00894. El resto de la brecha es el sesgo hacia arriba propio de estimar escala con N=10.
3. **Escala contra desviación**: la Student-t de PyMC toma escala, y sin convertir las pérdidas
   simuladas salían 22% más angostas. Verificado: desviación simulada 0.01988 contra 0.02000
   pedida, donde la escala cruda habría dado 0.01549.
4. **La predictiva se aplanaba sobre las observaciones**: 10000 valores = 1000 muestras
   posteriores x 10 observaciones. Corregido a un retorno por muestra posterior.
5. **`draws=500` no converge con colas gruesas** (rhat 1.0260, ESS 258, con aviso de PyMC de que
   el ESS por cadena está por debajo de 100). Con los defaults converge y recupera el índice de
   cola (nu 4.04 contra 4.0 real). Consecuencia abierta: la API acepta `draws` desde 500 y ese
   request devuelve 500; está documentado en el README.
6. **El conteo de divergencias no es portable**: la misma ventana y la misma semilla dieron 0
   divergencias sobre 8000 muestras en un intérprete y 3 en otro, por el orden de reducción en
   punto flotante. El umbral pasó de conteo cero a tasa (0,5% de las muestras) para que la barrera
   no se convierta en un fallo aleatorio.

### Resultado sobre el payload de ejemplo

| Medida | Antes | Después |
|---|---|---|
| VaR 95% | 13.478 | 12.902 |
| Intervalo creíble 5-95% | no existía | 6.598 - 21.674 |
| ES 95% | no existía | 18.094 |
| P(pérdida > 50k) | 0,00008 | 0,00057 |
| Diagnóstico | no existía | rhat 1.003, ESS 4290, 0 divergencias |

### Costo

4 cadenas son el mínimo para que `rhat` signifique algo, y eso lleva un request de 14s a 45-75s
con los defaults, contra un timeout de 120s. El backtest de cobertura cuesta ~3,5 minutos y el
step `slow` de CI pasó de ~1,5 a ~6 minutos.

## Notas de recuperación

`mem_search` por `model-reliability`, leer este archivo, seguir desde la primera task en `pending`.
