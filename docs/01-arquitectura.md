# 01 · Arquitectura y estructura de carpetas

## Decisiones
| Componente | Decisión | Alternativa evaluada | Motivo |
|---|---|---|---|
| Frontend | Next.js 16 + TypeScript + Tailwind 3 + Recharts | Vite+React | Next da PWA, rutas y despliegue sencillos; Recharts cubre barras/líneas/circulares; mapas de calor con tabla HTML accesible |
| Backend | FastAPI (Python) | Node/Express | Motor estadístico en Python (NumPy/SciPy), tipado con Pydantic |
| BD | SQLAlchemy: SQLite (desarrollo) / PostgreSQL (producción) | Solo PostgreSQL | Arranque sin instalar nada en Windows; misma capa para producción |
| Proveedores | Interfaz `DataProvider` (demo, CSV/Excel, API-Football pendiente) | Acoplar a un proveedor | Cambiar de proveedor = registrar otro adaptador |
| Caché/cola | **No** se añaden aún (Redis, Celery) | Redis + workers | Sin carga real todavía; se añadirán cuando la ingesta programada lo exija |

## Estructura
```
futbol-datapro/
├─ README.md
├─ docs/                    decisiones (este directorio)
├─ backend/
│  ├─ app/
│  │  ├─ main.py            API (FastAPI), CORS, rutas
│  │  ├─ config.py          variables de entorno
│  │  ├─ schemas.py         modelos de dominio (Match, Fixture…)
│  │  ├─ security.py        cabeceras, límite de solicitudes, tamaño de cuerpo
│  │  ├─ db.py              historial de análisis (SQLAlchemy)
│  │  ├─ providers/         base.py · demo.py · csv_file.py · api_football.py (pendiente)
│  │  ├─ engine/            dixon_coles.py · markets.py · cards.py · validation.py
│  │  └─ analytics/         team_report.py · analysis.py (orquestación)
│  ├─ tests/                31 pruebas (motor, proveedores, API, seguridad)
│  ├─ data/ejemplo_partidos.csv
│  └─ requirements.txt · .env.example · pytest.ini
└─ frontend/
   ├─ app/                  páginas: Inicio, Analizar, Historial, Fuentes
   ├─ components/           AnalysisView, MatchPicker, Shell, charts/
   ├─ lib/                  api.ts (cliente + tipos), format.ts
   └─ public/               manifest, iconos, sw.js
```

## Flujo
`Proveedor → partidos normalizados → (corte por fecha) → informe por equipo + Dixon-Coles → mercados + Monte Carlo → API → dashboard`.
Cada análisis guardado (`POST /api/history`) es una versión inmutable con hora, fuente y modelo.

## Estado por fase
| Fase | Estado |
|---|---|
| 1 Investigación | Hecha; pendiente prueba de cobertura con clave real |
| 2 Diseño/prototipo | Dashboard funcional basado en el mockup |
| 3 Frontend | Inicio, Analizar (8 pestañas), Historial, Fuentes. **No hechas**: calendario mensual, panel de usuario, suscripción |
| 4 Backend/ingesta | Proveedores demo y CSV/Excel. **Pendiente**: ingesta real programada, alineaciones, clima |
| 5 Motor/validación | Dixon-Coles + validación walk-forward implementados; **sin datos reales** aún |
| 6 Usuarios/planes | Pendiente |
| 7 Pagos/seguridad | Seguridad base hecha; pagos pendientes |
| 8 Despliegue | Pendiente |
| Informe PDF | Pendiente (botón deshabilitado y rotulado) |
