# V58 — Plan de arquitectura modular

## Objetivo

La app ya funciona, por eso V58 no rompe el `app.py` de producción de golpe. Añade una capa modular segura para empezar a mover lógica paso a paso sin arriesgar Render.

## Estructura nueva

```text
app_core/
  config.py
  services/
    telegram_quality.py
    memberships.py
    spanish_copy.py
  routes/
    __init__.py

tests/
  test_services.py
  test_smoke_routes.py

scripts/
  run_tests.py
  check_architecture.py
```

## Qué mover primero en futuras versiones

1. Telegram y filtros de calidad.
2. Membresías y caducidad.
3. Copys en español y traducción de mercados.
4. ROI y resultados.
5. Rutas admin.
6. Rutas cliente.

## Regla importante

Nada se mueve si no hay test básico antes. Así evitamos romper login, Telegram, picks, Render o membresías.
