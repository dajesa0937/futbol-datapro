# 00 · Investigación técnica y comercial (FASE 1)

Fecha de la investigación: 20 oct 2026. Todo lo marcado **[NO VERIFICADO]** no pudo comprobarse con las fuentes
consultadas y debe confirmarse antes de decidir. No se contrató ningún servicio ni se realizó ningún pago.

## 1. Proveedores de datos deportivos

| Criterio | API-Football (api-sports.io) | Sportmonks Football API v3 | Hudl Statsbomb / Wyscout |
|---|---|---|---|
| Precio | Gratis (100 consultas/día); Pro US$19/mes (7.500/día); Ultra US$29 (75.000/día); Mega US$39 (150.000/día) | Starter €29/mes (5 ligas a elección, 2.000 llamadas/entidad/hora); Growth €99 (30 ligas); Pro €249 (120 ligas). −20 % en plan anual. Prueba de 14 días | Orientado a clubes y profesionales; precio **[NO VERIFICADO]** |
| Funciones por plan | Todos los endpoints en todos los planes; el gratuito limita temporadas disponibles | Todas las funciones en todos los planes; cambia el nº de ligas y la capacidad | Datos avanzados (eventos, xG) |
| Cobertura Liga BetPlay | **[NO VERIFICADO]**: afirma >1.200 ligas, pero no se confirmó Colombia con minuto a minuto, tarjetas, árbitro ni alineaciones | **[NO VERIFICADO]**: afirma >2.200 ligas; confirmar que Primera A está en el catálogo y qué temporadas incluye | Win Sports anunció (19 feb 2026) acuerdo con Hudl y que Primera A y B se incorporan a Statsbomb |
| Histórico | Depende del plan y la liga | Solo las últimas 3 temporadas; más histórico = compra única aparte | Alto |
| Licencia comercial | Revisar términos para uso en producto de pago **[NO VERIFICADO]** | Idem **[NO VERIFICADO]** | Probablemente restrictiva (uso profesional) |

Otros hallazgos:
- **football-data.org**: gratuita, pero su lista de 12 competiciones no incluye Colombia.
- **Sports Game Odds** ofrece Primera A, pero es un proveedor de *cuotas de apuestas*, no de estadísticas de análisis; se descarta.
- Los derechos de los datos del fútbol colombiano están concentrados (Win Sports/Dimayor). **Riesgo**: que la licencia
  del proveedor no autorice redistribuir los datos en un producto de pago. Debe confirmarse por escrito con el proveedor elegido.

**Recomendación** (condicionada): empezar con API-Football en plan **gratuito** solo para ejecutar una *prueba de cobertura*
(ver abajo) y, si Colombia está completa, pasar a Pro (US$19/mes). Si falla, repetir la prueba con la prueba de 14 días de
Sportmonks. La elección definitiva depende de esa prueba y de la licencia, no del precio.

### Prueba de cobertura (pendiente, requiere clave del usuario)
Para cada candidato, con la Liga BetPlay 2025-II y 2026-I/II: (1) ¿existe la liga y cuántos partidos devuelve?; (2) ¿hay goles con
minuto y autor?; (3) ¿tarjetas por partido y por equipo?; (4) ¿árbitro?; (5) ¿alineaciones y lesiones antes del partido?; (6) ¿xG?;
(7) ¿latencia de actualización tras el pitazo final?; (8) ¿licencia comercial? Guardar respuestas reales y construir las pruebas del
adaptador sobre ellas.

## 2. Clima
- **Open-Meteo**: API gratuita **solo para uso no comercial** (<10.000 llamadas/día); el uso comercial exige suscripción de pago (datos CC BY 4.0, con atribución obligatoria). Precio exacto **[NO VERIFICADO]**.
- Alternativa: instancia propia de Open-Meteo (open source) o un proveedor comercial.
- Regla del proyecto: mostrar clima solo si hay pronóstico verificable para estadio y fecha. Hoy **no hay módulo de clima**; la interfaz lo declara como no disponible.

## 3. Pagos en Colombia
| | Wompi (Grupo Cibest/Bancolombia) | Mercado Pago Colombia |
|---|---|---|
| Medios | Tarjetas, PSE, Nequi, DaviPlata, Bancolombia, efectivo | Tarjetas, PSE, efectivo (Efecty) |
| Recurrente | Fuentes de pago y tokenización para cobros recurrentes; **la app debe programar cada cobro** | API de Suscripciones nativa: planes, frecuencia semanal/mensual/anual, reintentos automáticos, período de prueba |
| Comisiones | **[NO VERIFICADO]** | **[NO VERIFICADO]** |

Inclinación inicial: **Mercado Pago Suscripciones** por traer reintentos y gestión de ciclo; **Wompi** si se prioriza Nequi/PSE y el
ecosistema Bancolombia. Decisión en FASE 7 tras revisar comisiones, requisitos de alta de comercio y pruebas en sandbox.
Nunca se almacenarán datos de tarjeta: se usa tokenización/checkout del procesador y webhooks con firma verificada.

## 4. Hosting y base de datos
Hallazgos de comparativas fechadas entre ago y oct 2026 (verificar en las páginas oficiales antes de contratar):
- **Render**: plan gratuito que se duerme tras 15 min (arranque de 30–60 s) y Postgres gratuito que **expira a los 30 días**: no sirve para producción. Reestructuró precios el 1-ago-2026.
- **Railway**: sin nivel gratuito real (crédito de prueba), cobro por uso, Postgres como servicio del proyecto.
- **Fly.io**: máquinas desde ≈ US$1,94/mes; Postgres gestionado caro (≈ US$38/mes); muchos usan Neon/Supabase aparte.
- Frontend: Vercel/Netlify (Next.js).
**Propuesta**: frontend en Vercel o Netlify; backend FastAPI en Render o Railway (≈ US$7–20/mes); PostgreSQL gestionado de pago bajo
(Neon/Supabase/Render) con copias de seguridad. Evitar niveles gratuitos que expiran o se duermen en producción.

## 5. Bibliotecas estadísticas
SciPy/NumPy (implementado: Dixon-Coles propio con `scipy.optimize`). Candidatos a evaluar sin adoptarlos por moda: `statsmodels`
(GLM Poisson/binomial negativa para tarjetas), `scikit-learn`/`lightgbm` solo si superan al modelo base fuera de muestra.

## 6. Obligaciones legales en Colombia (revisar con abogado)
- **Ley 1581 de 2012 (Habeas Data)**: política de tratamiento de datos, autorización del titular y, si aplica, **inscripción de bases de datos en el RNBD** de la SIC (Decreto 090 de 2018 definió quiénes están obligados y plazos; las bases nuevas deben inscribirse dentro de los 2 meses siguientes a su creación). Confirmar si la empresa es sujeto obligado.
- **Protección al consumidor** (Ley 1480 de 2011): información clara de precios, renovación automática, cancelación y derecho de retracto en ventas a distancia **[verificar]**.
- **Apuestas**: el producto es analítica, **no** debe ofrecer cuotas, enlaces de casas de apuestas ni recomendaciones de apostar, y debe incluir aviso de juego responsable. Si en el futuro se monetiza con afiliados de apuestas, consultar normativa de Coljuegos.
- **Marcas y escudos**: no se usan; la interfaz muestra monogramas. Revisar permisos antes de incorporar escudos.
- Facturación/impuestos (IVA, facturación electrónica DIAN): consultar contador.
