# Instrucciones para GitHub Copilot — Fútbol DataPro

Lee primero `docs/INSTRUCCIONES_PROYECTO.md` (reglas inquebrantables: no inventar datos, demo siempre etiquetado, sin pagos ni contratos sin autorización, no declarar terminado sin probar).

## Comandos
- Backend: `cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python -m pytest -q && python -m uvicorn app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm install && npm run dev` (tipos: `npx tsc --noEmit`; producción: `npm run build`)
- Datos reales: `cd backend && python -m scripts.api_football_cobertura` y `python -m scripts.api_football_sync --seasons 2026 --details none`

## Estructura
`backend/app/providers` (fuentes intercambiables), `engine` (modelo), `analytics` (informes), `security.py`, `db.py`; `frontend/components/Dashboard.tsx` (panel del mockup); `docs/`.

## Convenciones
- Español de Colombia en la interfaz; números con coma decimal (`lib/format.ts`).
- Colores solo vía variables CSS (`app/globals.css`); verde/rojo siempre con etiqueta de texto.
- Todo dato nuevo en la UI debe mostrar fuente, cobertura y muestra, o declarar «No disponible».
- El modelo solo usa partidos estrictamente anteriores a `as_of` (hay prueba de fuga de datos).
- La app web nunca llama a API-Football; solo los scripts de sincronización lo hacen.
- Nunca escribir claves en archivos versionados (`.env` está en `.gitignore`).
