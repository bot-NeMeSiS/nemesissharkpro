# V329 UPDATE PACK · Instalación desde iPhone con Working Copy

Este paquete es seguro porque NO incluye `app.py`.

## Qué añade
- Navegación móvil inferior.
- Acceso rápido visible a SHARK COMBI 1X2.
- CSS/JS premium móvil.
- Bloque HTML opcional para pegar en dashboard cliente.

## Cómo subirlo desde iPhone

1. Descarga este ZIP en Archivos.
2. Descomprímelo.
3. Abre Working Copy.
4. Entra en tu repo.
5. Copia estas carpetas encima:
   - `static/css/`
   - `static/js/`
   - `templates/client/`
   - `docs/`
6. Commit: `V329 mobile combi quick access`
7. Push.
8. Redeploy en Render.

## Para hacerlo visible en el dashboard cliente

Busca el template principal del panel cliente y pega:

```jinja2
{% include 'client/v329_combi_quick_access_block.html' %}
```

Si no encuentras el template, manda captura de la carpeta `templates/` y te digo dónde va.
