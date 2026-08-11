# Finder Docker Documentation

This document explains how to build, run, and manage the **Finder** application using Docker and Docker Compose for local development and production deployment (such as AWS EC2).

---

## 🏗 System Architecture

The Finder stack consists of 3 primary services:

1. **Frontend**: React + Vite + TypeScript single-page app.
   - **Local Dev**: Runs Vite development server on port `5173` with hot-module replacement (HMR).
   - **Production**: Multi-stage build served via Nginx on port `80` acting as static server + reverse proxy.
2. **Backend**: FastAPI (Python 3.11) with Uvicorn.
   - Exposes REST API on port `8000`.
   - Includes Playwright (Chromium) for web page extraction.
   - Runs non-destructive database migrations (`alembic upgrade head`) automatically on startup.
3. **Database**: PostgreSQL 16.
   - **Local Dev**: Bound to host port `5433:5432`.
   - **Production**: Internal container network only (`5432`).

---

## 🚀 Local Development Setup

### Prerequisites
- Docker (Desktop / Engine) version 20+ installed
- Docker Compose v2+ (`docker compose`)

### 1. Start the Local Stack

From the project root directory, run:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

### 2. Verify Service Status

```bash
docker compose -f docker/docker-compose.yml ps
```

All 3 containers (`finder-db`, `finder-backend`, `finder-frontend`) should be in the `running` / `healthy` state.

### 3. Accessing Services

- **Frontend App**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Endpoint**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **PostgreSQL**: `localhost:5433` (User: `finder`, DB: `finder_db`)

### 4. Viewing Logs

```bash
# View logs for all services
docker compose -f docker/docker-compose.yml logs -f

# View logs for backend only
docker compose -f docker/docker-compose.yml logs -f backend
```

### 5. Stopping the Stack

```bash
docker compose -f docker/docker-compose.yml down
```

---

## 🌐 Production Setup (AWS EC2 / Server Deployment)

For production environments, use the production compose file:

```bash
# Set production secrets in environment or .env file
export SECRET_KEY="your-strong-production-jwt-secret"
export OPENAI_API_KEY="your-openai-api-key"

# Build and launch production stack
docker compose -f docker/docker-compose.prod.yml up -d --build
```

In production:
- Nginx listens on port `80` (or `443` with SSL).
- Browser requests to `/api/v1/*` are transparently proxied to the backend container.
- PostgreSQL is bound to loopback `127.0.0.1:5433` (not exposed publicly) and accessible via pgAdmin container on port `5050`.

---

## 🐘 Connecting pgAdmin to Production DB

There are two ways to connect pgAdmin to the production database:

### Option A: Built-in pgAdmin Web Interface (Port 5050)
The production stack includes a pgAdmin service accessible on port `5050`.

1. Open `http://<your-server-ip>:5050` in your web browser.
2. Log in using the credentials defined in `.env` (defaults: `admin@finder.com` / `admin_secret`).
3. Click **Add New Server**:
   - **Host name/address**: `db` (or container IP)
   - **Port**: `5432`
   - **Maintenance database**: `finder_db` (or `$POSTGRES_DB`)
   - **Username**: `finder` (or `$POSTGRES_USER`)
   - **Password**: `<your-POSTGRES_PASSWORD>`

### Option B: Desktop pgAdmin via SSH Tunnel
If you prefer using pgAdmin on your local machine:

1. Open local **pgAdmin** > **Add New Server**.
2. **Connection Tab**:
   - **Host**: `127.0.0.1`
   - **Port**: `5433`
   - **Database**: `finder_db` (or `$POSTGRES_DB`)
   - **Username**: `finder` (or `$POSTGRES_USER`)
   - **Password**: `<your-POSTGRES_PASSWORD>`
3. **SSH Tunnel Tab**:
   - **Use SSH tunneling**: `Yes`
   - **Tunnel Host**: `<your-server-ip>`
   - **Username**: `ubuntu` / `ec2-user`
   - **Identity File**: Upload your server's `.pem` SSH key file.

---

## 🔄 Database Migrations & Volume Persistence

- **Database Storage**: PostgreSQL data is stored in the Docker volume `finder_postgres_data` (or `finder_postgres_prod_data` in production).
- **Upload Storage**: Resume uploads are stored in the Docker volume `finder_backend_uploads` (or `finder_backend_prod_uploads`).
- **Migrations**: Alembic migrations run automatically on container startup using `alembic upgrade head` via `docker-entrypoint.sh`. Existing data is never deleted or dropped.

---

## 🛠 Troubleshooting

- **Check Container Health**:
  ```bash
  docker compose -f docker/docker-compose.yml ps
  ```
- **Rebuild Containers After Requirements/Dependencies Change**:
  ```bash
  docker compose -f docker/docker-compose.yml up -d --build --force-recreate
  ```
- **Run Alembic Migrations Manually**:
  ```bash
  docker exec -it finder-backend alembic upgrade head
  ```
- **Interactive Shell in Backend**:
  ```bash
  docker exec -it finder-backend /bin/sh
  ```
