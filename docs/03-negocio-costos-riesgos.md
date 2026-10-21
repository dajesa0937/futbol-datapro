# 03 · Modelo de negocio, costos y riesgos

## Planes (propuesta; límites configurables desde el panel de administración, aún no construido)
| | Gratis | Pro | Premium |
|---|---|---|---|
| Calendario y estadísticas básicas | ✔ | ✔ | ✔ |
| Análisis avanzados | pocos/mes | más | mayor límite |
| Últimos 20 partidos completos, marcadores, tarjetas, jugadores | resumen | ✔ | ✔ |
| Historial e informes PDF | — | ✔ | ✔ |
| Actualización de predicciones con nueva información | — | ✔ | ✔ |
| Seguimiento de varios equipos, comparaciones avanzadas, histórico adicional | — | — | ✔ |
El control de acceso se aplicará **en el backend** (FASE 6); hoy no hay cuentas ni límites.

## Costos mensuales estimados (hipótesis a confirmar)
| Concepto | Estimado | Estado |
|---|---|---|
| Datos deportivos | US$19 (API-Football Pro) – €29 (Sportmonks Starter) | precios publicados; cobertura **no verificada** |
| Backend + BD gestionada | ≈ US$15–30 | rango de comparativas; verificar |
| Frontend (Vercel/Netlify) | US$0–20 | verificar |
| Clima comercial | **[NO VERIFICADO]** | |
| Comisión de pagos | **[NO VERIFICADO]** | |
| Dominio, correo, monitoreo | ≈ US$5–15 | estimación |
Total de referencia ≈ **US$45–85/mes** (≈ COP 180.000–340.000 con una TRM supuesta de 4.000; **verificar la TRM**).

## Precios de lanzamiento (propuesta, sin validar con clientes)
Pro **COP 19.900/mes** y Premium **COP 39.900/mes**, con plan anual con descuento. Punto de equilibrio aproximado = costo fijo ÷ (precio − comisión):
con costo fijo COP 250.000 y comisión supuesta del 5 % → ≈ 14 suscriptores Pro. Son cifras de partida para discutir, no definitivas.

## Riesgos principales
| Riesgo | Impacto | Mitigación |
|---|---|---|
| La API elegida no cubre bien la Liga BetPlay | Alto | Prueba de cobertura antes de pagar; segundo candidato; importación CSV como plan B |
| Licencia de datos no permite redistribución comercial | Alto | Confirmar por escrito; asesoría legal |
| Modelo sin ventaja real frente a referencias | Medio | Validación pública y honesta; no prometer aciertos |
| Percepción de "tips de apuestas" | Medio/Legal | Sin cuotas ni enlaces de apuestas; aviso de juego responsable |
| Datos personales (Ley 1581) | Medio | Política, autorización, RNBD si aplica |
| Costo de datos > ingresos al inicio | Medio | Empezar con plan de datos mínimo; límites por plan |
| Seguridad de pagos | Alto | Tokenización del procesador, webhooks firmados, sin datos de tarjeta |
