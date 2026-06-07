# Deployment — Datra Analytics

This directory is the **single source of truth** for how the Datra Analytics
site is deployed. The full stack (backend + static frontend) runs as a
`docker-compose` project on a single EC2 instance.

## Server layout

```
/home/ubuntu/datra-analytics-final/
├── backend/            <- contents of the Website-be repo (this repo)
├── website/            <- contents of the Website-fe repo
├── docker-compose.yml  <- copy of deploy/docker-compose.yml (kept in sync by CI)
└── .env                <- DB credentials (NOT in git; see .env.example)
```

| Item            | Value                                              |
|-----------------|----------------------------------------------------|
| Instance        | `i-0491dd2f55c1f641f` (`datra-analytics`)           |
| Region          | `ap-south-1`                                        |
| Host            | `13.205.180.185`                                    |
| SSH user        | `ubuntu`                                            |
| App dir         | `/home/ubuntu/datra-analytics-final`                |
| Compose         | `docker-compose` **v1** (use the hyphenated command)|
| Frontend ports  | `80`, `443`                                         |
| Backend port    | `8000` (also proxied by the frontend nginx at `/api`)|

## CI/CD (GitHub Actions)

Two workflows, one per repo, both triggered on **push to `main`** only:

- **Website-be** → `.github/workflows/deploy.yml`
  rsyncs this repo into `backend/`, pushes this `docker-compose.yml` to the
  server, then `docker-compose up -d --build backend`, then health-checks
  `http://localhost:8000/api/dashboard/filters`.
- **Website-fe** → `.github/workflows/deploy.yml`
  rsyncs that repo into `website/`, then `docker-compose up -d --build
  frontend`, then health-checks `http://localhost/health`.

### Required GitHub Actions secrets (set per repo)

| Secret            | Value                                |
|-------------------|--------------------------------------|
| `SSH_HOST`        | `13.205.180.185`                     |
| `SSH_USER`        | `ubuntu`                             |
| `SSH_PRIVATE_KEY` | contents of the `developer.pem` key  |

The rsync step excludes `.env`, so the server's database credentials are
never overwritten by a deploy.

## Manual deploy (fallback)

From the server (`/home/ubuntu/datra-analytics-final`):

```bash
docker-compose up -d --build          # rebuild & restart everything
docker-compose up -d --build backend  # backend only
docker-compose up -d --build frontend # frontend only
docker-compose logs -f                # tail logs
```
