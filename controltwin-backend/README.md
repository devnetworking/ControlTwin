# ControlTwin

Production-ready FastAPI backend for **ControlTwin**, a Digital Twin platform for **ICS/SCADA** workloads in the energy sector (electricity, oil & gas).

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

API base URL: `http://localhost:8000/api/v1`

Health endpoint: `GET /api/v1/health`

## Technology Stack

- Python 3.11
- FastAPI 0.115 + Uvicorn
- PostgreSQL 16 + SQLAlchemy 2.0 async (`asyncpg`)
- InfluxDB 2.7
- Kafka (aiokafka)
- MQTT (HiveMQ CE)
- JWT (PyJWT) + bcrypt
- Pydantic v2 + pydantic-settings
- Docker / Docker Compose
- pymodbus 3.8 (read-only collector)
- asyncua 1.1 (subscription collector)

## Project Structure

| Path | Description |
|---|---|
| `app/main.py` | FastAPI app and lifespan startup/shutdown |
| `app/core/config.py` | Environment-backed settings |
| `app/core/security.py` | Password hashing + JWT functions |
| `app/core/logging.py` | Logging setup |
| `app/models/models.py` | SQLAlchemy ORM models |
| `app/schemas/schemas.py` | Pydantic request/response schemas |
| `app/auth/dependencies.py` | Current user dependency |
| `app/auth/rbac.py` | Roles, permissions, RBAC guards |
| `app/db/postgres.py` | Async SQLAlchemy engine/session/init/health |
| `app/db/influxdb.py` | Influx repository (write/query/latest/health) |
| `app/services/*.py` | Business services |
| `app/collectors/*.py` | Modbus and OPC-UA collectors |
| `app/api/v1/router.py` | API router aggregator |
| `app/api/v1/endpoints/*.py` | Endpoint modules |
| `tests/test_backend.py` | Unit tests |
| `docker/Dockerfile` | Multi-stage runtime image |
| `docker-compose.yml` | Full local stack |
| `docker/postgres/init.sql` | PostgreSQL extension init |

## API Endpoints

All endpoints under `/api/v1`.

| Domain | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh` |
| Users | `GET /users/me`, `POST /users` |
| Sites | `GET /sites`, `GET /sites/{id}`, `POST /sites` |
| Assets | `GET /assets`, `GET /assets/{id}`, `POST /assets`, `PATCH /assets/{id}`, `DELETE /assets/{id}` (soft delete) |
| DataPoints | `GET /datapoints`, `POST /datapoints`, `POST /datapoints/query`, `GET /datapoints/{id}/latest` |
| Alerts | `GET /alerts`, `GET /alerts/{id}`, `POST /alerts`, `POST /alerts/{id}/acknowledge`, `POST /alerts/{id}/resolve` |
| Collectors | `GET /collectors`, `GET /collectors/{id}`, `POST /collectors` |
| Health | `GET /health` |

## RBAC Matrix

| Role | Permissions |
|---|---|
| `readonly` | `asset:read`, `datapoint:read` |
| `viewer` | readonly + `alert:read`, `report:read` |
| `ot_operator` | viewer + `alert:acknowledge`, `collector:read` |
| `ot_analyst` | operator + `asset:create`, `asset:update`, `datapoint:write`, `alert:manage`, `collector:manage`, `report:generate`, `audit:read` |
| `admin` | analyst + `asset:delete`, `user:read`, `user:manage` |
| `super_admin` | all permissions |

## Security Notes

- JWT access tokens (30 minutes) + refresh tokens (7 days)
- Lockout after 5 failed logins for 15 minutes
- Bcrypt hashing (12 rounds)
- Asset deletion is soft-delete only
- Modbus collector is strictly **read-only** (FC01/02/03/04 only)

## Testing

Run tests:

```bash
pytest -q
```

Covers auth/security, RBAC rules, schema validation, asset service edge cases, and Modbus read-only security check.
