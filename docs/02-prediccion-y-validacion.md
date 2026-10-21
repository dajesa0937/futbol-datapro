# 02 · Estrategia de predicción y validación

## Modelo base: Dixon-Coles con decaimiento temporal
- Goles local/visitante ~ Poisson con `λ_local = exp(μ + ventaja_local + ataque_local − defensa_visitante)` y `λ_visit = exp(μ + ataque_visit − defensa_local)`.
- Corrección `τ(ρ)` para 0-0, 1-0, 0-1, 1-1. Peso de cada partido `exp(−ξ·días)` (ξ=0,0019/día ≈ vida media 1 año).
- Penalización ridge (0,6) sobre ataque/defensa: con ≈20 partidos por equipo evita estimaciones extremas.
- Se ajusta solo con partidos **estrictamente anteriores** a la fecha del encuentro (hay una prueba automática que lo comprueba).
- Se entrena con Liga + Copa + internacionales; **amistosos excluidos** (intensidad y plantillas no comparables).
- Salidas: 1X2, goles esperados, matriz de marcadores, más/menos 0,5–4,5, ambos anotan, rango 80 % de goles, simulación Monte Carlo (20.000, semilla fija) que confirma el cálculo analítico.

## Módulos secundarios (etiquetados "estimación simple, sin validar")
- Tarjetas: tasa por equipo con contracción hacia la media de liga (≥ 8 partidos con datos), Poisson para líneas. Árbitro: aún no se aplica porque la fuente no informa al árbitro designado.
- Goles por tramo: reparto de los goles esperados con la distribución del equipo mezclada con la de la liga (solo con ≥ 60 % de partidos con minuto).
- Goleadores: participación en goles del equipo × goles esperados; requiere ≥ 8 goles con autor; asume que el jugador juega.

## Qué NO se hace todavía y por qué
- Poisson bivariado, regresión/ML con más variables, xG, descanso/viajes en el modelo, alineaciones: **sin datos reales no se puede demostrar que mejoren** el modelo base. Solo se incorporarán si superan al Dixon-Coles en validación fuera de muestra.
- No se muestran porcentajes de "acierto". Cuando los datos son insuficientes (<10 partidos previos de un equipo) la API **no emite probabilidades** y la interfaz lo dice.

## Validación retrospectiva (`app/engine/validation.py`)
Walk-forward semanal: para cada semana se reajusta con partidos previos y se predice esa semana. Métricas: Brier multiclase, log loss, error en goles totales, tabla de calibración, desempeño por temporada. Referencias: frecuencias históricas y Poisson de liga sin fuerza de equipos.

### Resultado actual y su significado
Sobre los **datos sintéticos** (373 partidos evaluados): Brier 0,6414 (modelo) vs 0,6498 (frecuencias) y 0,6477 (Poisson de liga), mejora ≈ 1 %. El modelo recupera la fuerza real simulada (correlación ≈ 0,72 con ataque y defensa verdaderos).
**Esto valida que el código funciona y que no hay fuga de información. NO dice nada sobre el rendimiento en la Liga BetPlay real.** La validación real requiere cargar ≥ 2–3 temporadas reales.

## Hoja de ruta de modelado (con datos reales)
1. Validar Dixon-Coles y ajustar ξ y ridge por validación cruzada temporal.
2. Probar Poisson bivariado y binomial negativa; mantener solo lo que mejore Brier/log loss de forma consistente.
3. Registrar cada predicción antes del partido y comparar con el resultado (el historial ya guarda versión y hora).
4. Reportes periódicos y alerta de degradación (Brier móvil frente a referencia).
