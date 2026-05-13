# NeMeSiS SHARK PRO V81 — GitHub Clean Build

Esta build está limpiada para subir directamente a GitHub.

## Qué se ha eliminado del ZIP

- zips anteriores
- cachés Python
- `__pycache__`
- logs
- backups
- archivos temporales
- `.git`
- WAL/SHM de SQLite
- basura de sistema/IDE

## Cómo subir

1. Descomprime este ZIP.
2. Copia el contenido en tu repo local.
3. Mantén tu carpeta `.git` si ya existe.
4. Ejecuta:

```bash
git add .
git commit -m "V81 clean GitHub build"
git push
```

## Importante

No mezcles builds antiguas.  
Esta V81 ya incluye todo lo anterior.
