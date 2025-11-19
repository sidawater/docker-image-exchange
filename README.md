# doc-upload

Minimal document upload service (FastAPI + SQLAlchemy)

Quick start

1. Create and activate a virtualenv (example):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install the package and dev extras:

```bash
pip install -e .[dev]
```

3. Run the app with Uvicorn (adjust the module path if needed):

```bash
uvicorn run:app --reload
```

Notes

- Database configuration and other environment variables are expected to be provided via `.env` or the environment.
- Alembic is included for migrations (`alembic` command).
- Code style tools configured: `black`, `isort`, `ruff`, `mypy`.
