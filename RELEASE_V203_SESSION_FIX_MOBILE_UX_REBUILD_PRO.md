# V203 · SESSION FIX + MOBILE UX REBUILD PRO

Base: V202 Smart Product Control Center Pro.

## Incluye
- Corrección de identidad de cliente: elimina fallback hardcodeado `Damian` y toma nombre/plan desde `session['user']`.
- Fallback seguro `Cliente` cuando no hay sesión válida.
- Dashboard cliente móvil más compacto y limpio.
- Navbar móvil única para cliente: Inicio, Picks, Live, Favoritos, Cuenta.
- Botón flotante SHARK AI.
- Oculta navegación móvil duplicada heredada mediante CSS responsive.
- Limpieza de textos técnicos visibles al cliente.
- Panel grande “Lo que falta instalar / revisar”.
- API `/api/v203/session/identity`.
- Rutas `/cliente/setup-pendiente` y `/admin/setup-pendiente`.

## Política
- Sin partidos fake.
- Sin picks fake.
- Sin scores fake.
- Sin datos de otro usuario visibles.
- Todo en español.
