# Datra Analytics — Backend (Website-be)

FastAPI service powering the Datra Analytics real-estate intelligence platform.
It exposes a read-only REST API over a MySQL database of aggregated property
transaction data, plus a write endpoint for demo-request form submissions.

> Frontend lives in a separate repo: **Website-fe**.

## Tech Stack

- **FastAPI** — web framework
- **SQLAlchemy 2.0** (async) + **aiomysql** — database access
- **Pydantic v2** — validation
- **Uvicorn** — ASGI server

## Project Structure

```
app/
├── main.py          # App entry point, CORS, router registration
├── config.py        # Settings loaded from .env (DB + API config)
├── database.py      # Async SQLAlchemy engine & session
├── models.py        # ORM models (base tables)
├── schemas.py       # Pydantic request/response models
└── routers/
    ├── dashboard.py # KPIs, filters, trends, summary, search
    ├── city.py      # City analytics & rankings
    ├── locality.py  # Locality analytics
    ├── developer.py # Developer analytics
    ├── project.py   # Project analytics
    ├── rental.py    # Rental analytics
    └── demo.py      # Demo-request form (read/write)
```

## Configuration

All config is loaded from a `.env` file (see [.env.example](.env.example)).
**Never commit `.env`** — it is git-ignored.

| Variable      | Description                  | Default     |
|---------------|------------------------------|-------------|
| `DB_HOST`     | MySQL host                   | —           |
| `DB_PORT`     | MySQL port                   | `3306`      |
| `DB_NAME`     | Database name                | —           |
| `DB_USER`     | Database user                | —           |
| `DB_PASSWORD` | Database password            | —           |
| `API_HOST`    | Bind host                    | `0.0.0.0`   |
| `API_PORT`    | Bind port                    | `8000`      |
| `DEBUG`       | Enable reload / SQL echo     | `False`     |

## Local Development

```bash
# 1. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env            # then edit .env with real credentials

# 4. Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API root: http://localhost:8000
- Interactive docs: http://localhost:8000/api/docs

## Docker

```bash
docker build -t datra-backend .
docker run -p 8000:8000 --env-file .env datra-backend
```

## API Overview

| Group     | Base path           |
|-----------|---------------------|
| Dashboard | `/api/dashboard`    |
| City      | `/api/city-analytics` |
| Locality  | `/api/locality`     |
| Developer | `/api/developers`   |
| Project   | `/api/projects`     |
| Rental    | `/api/rental`       |
| Demo      | `/api/demo`         |
| Health    | `/api/health`       |

See `/api/docs` for the full, live schema.

## Security Notes

- Credentials are provided only via `.env` / environment variables — never hard-coded.
- `.env`, `*.pem`, and `*.key` are git-ignored.
- The Docker image runs as a non-root user.
- Restrict `CORS allow_origins` in `app/main.py` to your real frontend origin before production (currently includes `*`).
