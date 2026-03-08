# controltwin-ai

AI service for ControlTwin ICS/SCADA platform (local-first, air-gap safe).

## Architecture

```
+---------------------------+       +---------------------------+
|   ControlTwin Backend     |<----->|      controltwin-ai       |
|   FastAPI :8000/api/v1    |  HTTP |   FastAPI :8001/api/v1/ai |
+---------------------------+       +---------------------------+
          ^          ^                        ^        ^
          |          |                        |        |
      PostgreSQL   InfluxDB               Kafka     Redis
       :5432        :8086                :9092      :6379
                                             |
                                          Celery
                                             |
                                           MLflow
                                             |
                                           Ollama
                                             |
                                          ChromaDB
```

## Features (5 AI Layers)

1. Twin State Intelligence  
2. Anomaly Detection (4-level pipeline)  
3. Predictive Maintenance (RUL + forecast)  
4. AI Remediation (RAG + local LLM)  
5. What-if Simulation (Monte Carlo + physical models)  

## Security & Safety

- No external API dependency for LLM (Ollama local only)
- No cloud requirement
- All AI outputs are **recommendations only**
- No automatic command execution on ICS equipment
- LLM calls include audit fields: prompt_hash, model, response_time_ms, tokens_used

## Requirements

- Python 3.11
- Docker + Docker Compose
- Running local ControlTwin backend
- Local services: PostgreSQL, InfluxDB, Kafka, Redis (or via compose stack)

## Setup

```bash
cd controltwin-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-ai.txt
```

Copy env:

```bash
copy .env.example .env
```

Run API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Run workers:

```bash
celery -A app.workers.celery_app worker --loglevel=info -Q default,ml_training
python -m app.workers.kafka_consumer
```

## Docker Stack

```bash
docker compose -f docker-compose.ai.yml up -d --build
```

## API Examples

### Twin state

```bash
curl http://localhost:8001/api/v1/ai/twin-state/asset-001
```

### Set desired state

```bash
curl -X POST http://localhost:8001/api/v1/ai/twin-state/desired-state/asset-001 ^
  -H "Content-Type: application/json" ^
  -d "{\"state\":{\"temp\":70},\"set_by_user_id\":\"u1\"}"
```

### Anomaly score

```bash
curl http://localhost:8001/api/v1/ai/anomaly/score/dp-001
```

### Predictive RUL

```bash
curl http://localhost:8001/api/v1/ai/predictive/rul/asset-001
```

### Remediation suggest

```bash
curl -X POST http://localhost:8001/api/v1/ai/remediation/suggest ^
  -H "Content-Type: application/json" ^
  -d "{\"alert_id\":\"a-1\",\"asset_id\":\"asset-001\"}"
```

### Simulation run

```bash
curl -X POST http://localhost:8001/api/v1/ai/simulation/run ^
  -H "Content-Type: application/json" ^
  -d "{\"asset_id\":\"asset-001\",\"scenario_description\":\"Increase inlet pressure by 20%\",\"parameters\":{},\"n_iterations\":200,\"duration_hours\":24}"
```

## Hardware Guidance

- CPU: 8+ cores recommended
- RAM: 16GB minimum, 32GB preferred
- GPU optional but recommended for local Ollama and PyTorch training
- Storage: 20GB+ for models/artifacts/chroma cache

## Notes

- `docker/ollama/init.sh` pulls `mistral:7b`, `nomic-embed-text`, `llama3.2:3b`
- ML model artifacts stored in local model directory
- MLflow tracks training runs/metrics/artifacts
