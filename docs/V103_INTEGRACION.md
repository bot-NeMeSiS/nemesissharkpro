# V103 — MOBILE EXPERIENCE PRO / PWA MODULE

## Instalación

Extrae este ZIP encima de tu app completa estable actual.

## Archivos añadidos

- public/manifest.webmanifest
- public/sw.js
- frontend/pwa/registerServiceWorker.js
- frontend/pwa/mobile-pro.css
- frontend/components/PWAInstallCard.jsx
- frontend/components/MobileBottomNav.jsx
- frontend/components/MobileProShell.jsx
- frontend/pages/MobileExperiencePro.jsx

## Activar PWA en React

En tu entrada principal de frontend, normalmente main.jsx o App.jsx, añade:

```javascript
import { registerServiceWorker } from "./pwa/registerServiceWorker";

registerServiceWorker();
```

## Añadir manifest al HTML

En public/index.html o plantilla principal:

```html
<link rel="manifest" href="/manifest.webmanifest" />
<meta name="theme-color" content="#00d084" />
```

## Nueva ruta recomendada

/mobile-pro -> MobileExperiencePro

## Importante

Esto no toca Stripe.
Esto no inventa datos.
Solo mejora experiencia móvil, instalación tipo app y base push-ready.
