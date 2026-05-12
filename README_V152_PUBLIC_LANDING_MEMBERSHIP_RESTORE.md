# NeMeSiS SHARK PRO V152.0

Release: `V152_PUBLIC_LANDING_MEMBERSHIP_RESTORE`

## Objetivo
Recuperar y mejorar la página principal pública comercial sin romper V151.

## Cambios principales
- `/` y `/inicio` vuelven a ser landing pública premium.
- `/dashboard` redirige según sesión:
  - cliente -> `/cliente/pro`
  - admin -> `/admin`
  - sin sesión -> `/`
- `/planes`, `/membresias` y `/pricing` muestran la landing enfocada en planes.
- Cards comerciales FREE / PRO / ELITE con colores:
  - FREE azul
  - PRO verde/turquesa
  - ELITE dorado
- Botones claros:
  - Entrar / iniciar sesión
  - Ver planes
  - Acceder al panel cliente si hay sesión
  - Salir de cuenta si hay sesión
  - Instalar app PWA
- Landing limpia, sin textos admin/debug.
- Mantiene rutas V151:
  - `/cliente/pro`
  - `/cliente/premium`
  - `/cliente/dashboard-pro`
  - `/api/v151/client/identity`

## Archivos añadidos
- `templates/public_landing_v152.html`
- `static/css/v152_public_landing.css`
- `static/js/v152_public_landing.js`

## Validación
- `python -m py_compile app.py` OK.
- Limpieza de ZIP: sin `__pycache__`, sin logs, sin zips internos.
