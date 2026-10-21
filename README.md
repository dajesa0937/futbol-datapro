# Fútbol DataPro

PWA de analítica del fútbol colombiano (Liga BetPlay Dimayor): informe de los últimos 20 partidos de cada equipo y una
estimación probabilística del próximo encuentro, siempre con la fuente, la cobertura y las limitaciones a la vista.

> **Estado: base funcional.** Por defecto corre con **datos demostrativos sintéticos** (clubes ficticios). El adaptador de datos reales
> (API-Football) está escrito y probado con respuestas simuladas, **pero no se ha ejecutado contra la API real**. Sin cuentas, pagos ni informe PDF. Ver `docs/01-arquitectura.md` (estado por fase).

## Qué funciona hoy (probado)
- API FastAPI: equipos, próximos partidos, análisis completo, validación del modelo, historial.
- Motor Dixon-Coles con decaimiento temporal, mercados (1X2, goles esperados, marcadores, más/menos, ambos anotan), Monte Carlo y validación walk-forward (Brier, log loss, calibración).
- Importación de CSV/Excel con validación (duplicados, alias de nombres, filas inválidas registradas).
- Dashboard: Inicio, Analizar (Resumen, Últimos 20, Goles, Tarjetas, Jugadores, Contexto, Probabilidades, Datos y método), Historial, Fuentes y calidad. PWA instalable.
- Seguridad base (cabeceras, CORS, límite de solicitudes, validación). Ver `docs/04-seguridad.md` para lo que **falta**.
- 38 pruebas automáticas del backend (`python -m pytest -q`).
- Interfaz alineada al mockup: barra lateral, panel del partido con 7 recuadros, tema claro/oscuro, navegación móvil, selección de temporada.

## Ejecutar en Windows 11
Requisitos: **Python 3.11+** (python.org, marcar «Add python.exe to PATH») y **Node.js 20+ LTS** (nodejs.org). Usa PowerShell.

### 1. Backend
```powershell
cd futbol-datapro\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # si falla: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
copy .env.example .env                 # opcional; sin .env usa datos demo
python -m pytest -q                    # deben pasar las pruebas
python -m uvicorn app.main:app --port 8000
```
Comprueba: http://localhost:8000/api/health → `{"status":"ok"}` (y http://localhost:8000/docs en desarrollo).

### 2. Frontend (otra ventana de PowerShell)
```powershell
cd futbol-datapro\frontend
copy .env.example .env.local
npm install
npm run dev                            # http://localhost:3000
```
Para probar la versión de producción (y la instalación como PWA): `npm run build` y luego `npm start`.

### 3. Probar paso a paso
1. Abre http://localhost:3000 → verás el aviso **DATOS DEMOSTRATIVOS** y 10 partidos.
2. Pulsa **Analizar** en un partido → recorre las 8 pestañas.
3. **Guardar en historial** → ve a **Historial** y ábrelo.
4. **Fuentes y calidad** → métricas de validación (sobre datos sintéticos, con su advertencia).

## Usar tus propios datos (CSV/Excel)
1. Copia `backend/data/ejemplo_partidos.csv` (o un `.xlsx` con las mismas columnas) y complétalo.
   Obligatorias: `date, competition, season, home, away, home_goals, away_goals`. Filas sin goles y con fecha futura = próximos partidos.
2. En `backend/.env`: `DATA_PROVIDER=csv` y `CSV_MATCHES_PATH=data/mis_partidos.csv`; reinicia el backend.
3. **Fuentes y calidad** muestra cuántas filas se rechazaron y por qué. Con pocos partidos el sistema responde «estimación no fiable» en lugar de inventar probabilidades.

## Datos reales (API-Football) — en tu PC
1. Crea tu cuenta en api-football.com (el plan gratuito permite 100 consultas/día; **verifica precios y condiciones tú mismo**) y copia tu clave.
2. En `backend/.env`: `API_FOOTBALL_KEY=tu_clave` (este archivo NO se sube a Git).
3. **Comprueba la cobertura antes de nada** (usa ~1 consulta): `python -m scripts.api_football_cobertura`. Muestra las ligas de Colombia, sus IDs y qué trae cada temporada (eventos, estadísticas, alineaciones). Si los IDs difieren de `239`/`241`, ajústalos en `API_FOOTBALL_LEAGUES`.
4. Descarga datos con presupuesto: `python -m scripts.api_football_sync --seasons 2025,2026 --details none --max-requests 20` (solo marcadores) y luego `--details recent` para minutos de gol y tarjetas (2 consultas por partido; es reanudable).
5. En `.env`: `DATA_PROVIDER=api_football`, reinicia la API. **Fuentes y calidad** mostrará la cobertura real.
6. Las respuestas crudas se guardan en `backend/data/cache/` (ignorado por Git: respeta la licencia del proveedor).
Si algo no coincide con el formato esperado, el sistema descarta ese detalle y lo registra en lugar de inventarlo.

## Subir a GitHub
```powershell
git remote add origin https://github.com/TU_USUARIO/futbol-datapro.git   # repositorio PRIVADO recomendado
git branch -M main
git push -u origin main
```
Abre la carpeta con VS Code (`futbol-datapro.code-workspace`), instala las extensiones recomendadas y usa **Terminal → Ejecutar tarea → «Todo: API + web»**.

## Documentación
`docs/00-investigacion.md` (proveedores, pagos, hosting, legal) · `01-arquitectura.md` · `02-prediccion-y-validacion.md` · `03-negocio-costos-riesgos.md` · `04-seguridad.md`.

## Despliegue (resumen; aún no realizado)
Frontend en Vercel/Netlify con `NEXT_PUBLIC_API_URL=https://tu-api`. Backend en Render/Railway con `APP_ENV=production`,
`DATABASE_URL` de PostgreSQL gestionado, `CORS_ORIGINS=https://tu-frontend`, `TRUST_PROXY=true` si hay proxy. **No publicar con datos
reales hasta tener autenticación** (FASE 6).
