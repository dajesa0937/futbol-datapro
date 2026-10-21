# 04 · Seguridad (estado real)

## Implementado y probado (pruebas automáticas)
- Validación de entrada con Pydantic/FastAPI (longitudes, tipos, rangos de fecha). Consultas SQL solo con ORM parametrizado (una prueba envía un texto tipo inyección SQL y se trata como equipo desconocido).
- Cabeceras de seguridad en API (`nosniff`, `X-Frame-Options: DENY`, CSP restrictiva, `no-store`) y en el frontend (CSP, HSTS en producción, `Referrer-Policy`, `Permissions-Policy`).
- CORS restringido a orígenes configurados (sin credenciales). Probado que un origen no listado no recibe cabecera.
- Límite de solicitudes por IP (lecturas y escrituras por separado, `Retry-After`), y tope de 10 KB por cuerpo.
- `/docs` y `/openapi.json` deshabilitados con `APP_ENV=production`.
- Secretos solo por variables de entorno; `.env` fuera del control de versiones; la clave de API no se imprime.
- Historial limitado a 1.000 filas para evitar abuso del almacenamiento.
- Dependencias: `pip-audit` sin vulnerabilidades conocidas; `npm audit --omit=dev` con 0 (se subió a Next 16 para corregir avisos de PostCSS).

## Limitaciones conocidas (honestas)
1. **No hay autenticación ni permisos todavía** (FASE 6). `POST /api/history` está abierto, solo limitado. No exponer públicamente con datos reales sin cuentas.
2. El limitador es en memoria y por proceso; en producción añadir límite en el proxy/CDN o Redis. Si hay proxy, `TRUST_PROXY=true` solo detrás de un proxy confiable.
3. La CSP del frontend usa `'unsafe-inline'` para scripts (requisito de hidratación de Next); mejora futura: nonces.
4. Sin registro de auditoría, copias de seguridad automáticas, monitoreo ni WAF: pendientes del despliegue (FASE 8).
5. Pagos, webhooks firmados y protección antifraude: no implementados.
6. Esto **no es una auditoría de seguridad ni una garantía de que no pueda ser vulnerado**; antes del lanzamiento conviene una prueba de penetración independiente.

## Lista previa al lanzamiento
HTTPS obligatorio · autenticación con contraseñas con hash (argon2/bcrypt) y verificación de correo · roles (usuario/administrador) · control de planes en backend · webhooks con verificación de firma e idempotencia · rotación de claves · copias de seguridad cifradas y prueba de restauración · política de privacidad y términos · inscripción RNBD si aplica.
