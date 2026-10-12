# Resultados del Backtest de Señales (Corregido)

**Fecha de ejecución:** 2026-10-12 01:59:06 UTC

## Configuración

- **Años de historia:** 5
- **Comisión acciones:** 0.10%
- **Comisión crypto:** 0.20%
- **Horizonte:** 10 sesiones
- **División de datos:** 60% in-sample, 40% out-of-sample
- **Simulación de portafolio:** 10% por posición, máximo 10 posiciones

## Definiciones de Métricas

- **Tasa de acierto (target):** Porcentaje de señales que alcanzaron el precio objetivo (no stop ni expiró)
- **Tasa de retornos positivos:** Porcentaje de señales con rendimiento neto > 0 (incluye expiradas positivas)
- **Tasa que supera SPY:** Porcentaje de señales con mejor rendimiento que SPY en la misma ventana temporal
- **Pérdida máxima por operación:** La peor pérdida individual registrada
- **Drawdown de portafolio:** Simulado con posición fija del 10% y máximo 10 posiciones simultáneas

## Resumen Ejecutivo

### In-Sample (Entrenamiento)

- **Total de señales:** 6302
- **Tasa de acierto (target):** 12.91%
- **Tasa de retornos positivos:** 51.58%
- **Tasa que supera SPY:** 45.53%
- **Rendimiento neto promedio:** +0.59%
- **SPY promedio (misma ventana):** +0.61%
- **BTC promedio (misma ventana):** +2.14%
- **Pérdida máxima por operación:** -20.91%
- **Drawdown de portafolio (10% posición, máx 10):** -47.88%
- **Objetivos alcanzados:** 811
- **Stops activados:** 1790
- **Expiradas:** 3680
- **Ganancia promedio (ganadoras):** +3.89%
- **Pérdida promedio (perdedoras):** -2.92%
- **Ratio ganancia/pérdida:** 1.33

### Out-of-Sample (Validación)

- **Total de señales:** 2469
- **Tasa de acierto (target):** 12.95%
- **Tasa de retornos positivos:** 45.89%
- **Tasa que supera SPY:** 42.02%
- **Rendimiento neto promedio:** +0.26%
- **SPY promedio (misma ventana):** +0.30%
- **BTC promedio (misma ventana):** -0.65%
- **Pérdida máxima por operación:** -21.35%
- **Drawdown de portafolio (10% posición, máx 10):** -35.90%
- **Objetivos alcanzados:** 318
- **Stops activados:** 770
- **Expiradas:** 1368
- **Ganancia promedio (ganadoras):** +4.47%
- **Pérdida promedio (perdedoras):** -3.31%
- **Ratio ganancia/pérdida:** 1.35

## Desempeño por Tipo de Señal

### In-Sample

#### Impulso

- **Señales:** 4386
- **Tasa de acierto (target):** 6.14%
- **Tasa de retornos positivos:** 55.24%
- **Tasa que supera SPY:** 47.18%
- **Rendimiento neto promedio:** +0.74%
- **Objetivos:** 268 | **Stops:** 814 | **Expiradas:** 3286

#### Retroceso

- **Señales:** 1916
- **Tasa de acierto (target):** 28.38%
- **Tasa de retornos positivos:** 43.23%
- **Tasa que supera SPY:** 41.77%
- **Rendimiento neto promedio:** +0.26%
- **Objetivos:** 543 | **Stops:** 976 | **Expiradas:** 394

### Out-of-Sample

#### Impulso

- **Señales:** 1455
- **Tasa de acierto (target):** 2.90%
- **Tasa de retornos positivos:** 49.72%
- **Tasa que supera SPY:** 44.69%
- **Rendimiento neto promedio:** +0.39%
- **Objetivos:** 42 | **Stops:** 266 | **Expiradas:** 1142

#### Retroceso

- **Señales:** 1014
- **Tasa de acierto (target):** 27.44%
- **Tasa de retornos positivos:** 40.36%
- **Tasa que supera SPY:** 38.17%
- **Rendimiento neto promedio:** +0.07%
- **Objetivos:** 276 | **Stops:** 504 | **Expiradas:** 226

## Interpretación y Conclusiones

### Validez del Modelo

El modelo es válido si:

1. **Consistencia:** Las métricas out-of-sample son similares a las in-sample
2. **Superioridad vs SPY:** La tasa que supera SPY es > 50% en out-of-sample
3. **Retornos positivos:** El rendimiento neto promedio es positivo y supera a SPY

### Recomendaciones

⚠️ **ALERTA:** La tasa que supera SPY es ≤ 50% en out-of-sample. El sistema NO agrega valor sobre buy-and-hold.

⚠️ **REVISAR:** El rendimiento promedio es inferior a SPY en out-of-sample.

### Por Tipo de Señal

❌ **Retroceso:** Solo supera a SPY en 38.2% de los casos (≤50%). DESACTIVAR.

❌ **Impulso:** Solo supera a SPY en 44.7% de los casos (≤50%). DESACTIVAR.

## Limitaciones

1. **Slippage:** No se modela el deslizamiento de precio en la ejecución
2. **Liquidez:** Asume que siempre se puede entrar/salir al precio deseado
3. **Costos de oportunidad:** No considera el costo de tener capital inmovilizado
4. **Survivorship bias:** Solo incluye activos que existen actualmente

## Notas Metodológicas

- Las señales se generan usando solo información disponible hasta ese momento (sin look-ahead)
- La entrada es al día siguiente del cierre que generó la señal
- Si stop y objetivo se tocan el mismo día, se registra el stop (conservador)
- Las comisiones se descuentan del rendimiento bruto
- Los rendimientos de SPY/BTC se calculan para el mismo periodo de cada señal
- El drawdown de portafolio simula posiciones del 10% con máximo 10 simultáneas
- Precios ajustados por splits y dividendos (yfinance)