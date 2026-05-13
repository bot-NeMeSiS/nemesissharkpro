# NeMeSiS SHARK PRO V84.1 — Render Fixed

Corrige el error de Render:

`Could not open requirements file: requirements.txt`

## Cómo usar

1. Descomprime este ZIP.
2. Copia TODO el contenido dentro de tu carpeta del repo:
   `C:\NeMeSiS SHARK PRO`
3. En GitHub Desktop:
   - Summary: `fix render requirements`
   - Commit to main
   - Push origin
4. En Render:
   - Manual Deploy
   - Deploy latest commit

## Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```
