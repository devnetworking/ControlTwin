#!/bin/bash
# ControlTwin — Complete Stack Startup Script

set -u

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/controltwin-backend"
FRONTEND_DIR="$ROOT_DIR/controltwin-frontend"
AI_DIR="$ROOT_DIR/controltwin-ai"
FRONTEND_LOG="$ROOT_DIR/controltwin-frontend/frontend.log"
FRONTEND_PID_FILE="$ROOT_DIR/controltwin-frontend/.frontend.pid"

PORTS=(8000 8001 5432 8086 9092 6379 8010 11434 5173)

print_info() { echo -e "${CYAN}${1}${NC}"; }
print_ok() { echo -e "${GREEN}${1}${NC}"; }
print_warn() { echo -e "${YELLOW}${1}${NC}"; }
print_err() { echo -e "${RED}${1}${NC}"; }

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_env_file() {
  local dir="$1"
  if [ ! -f "$dir/.env" ]; then
    if [ -f "$dir/.env.example" ]; then
      cp "$dir/.env.example" "$dir/.env"
      print_warn "Created missing .env from .env.example in $(basename "$dir")"
    else
      print_warn "No .env or .env.example found in $(basename "$dir")"
    fi
  fi
}

check_port_available() {
  local port="$1"
  if command_exists lsof; then
    if lsof -i :"$port" -sTCP:LISTEN -Pn >/dev/null 2>&1; then
      return 1
    fi
  elif command_exists ss; then
    if ss -ltn | awk '{print $4}' | grep -E "[:.]$port$" >/dev/null 2>&1; then
      return 1
    fi
  elif command_exists netstat; then
    if netstat -an 2>/dev/null | grep -E "LISTEN|LISTENING" | grep -E "[:.]$port[[:space:]]" >/dev/null 2>&1; then
      return 1
    fi
  fi
  return 0
}

wait_for_http() {
  local url="$1"
  local timeout="$2"
  local name="$3"
  local elapsed=0
  while [ $elapsed -lt $timeout ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      print_ok "✅ $name is ready ($url)"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  print_err "❌ Timeout waiting for $name ($url)"
  return 1
}

wait_for_container_health() {
  local container="$1"
  local timeout="$2"
  local name="$3"
  local elapsed=0
  while [ $elapsed -lt $timeout ]; do
    local status
    status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || true)"
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
      print_ok "✅ $name is ready (container: $container)"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  print_err "❌ Timeout waiting for $name (container: $container)"
  return 1
}

check_ram() {
  local ram_gb=0
  if [ "$(uname -s)" = "Darwin" ]; then
    local bytes
    bytes="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
    ram_gb=$((bytes / 1024 / 1024 / 1024))
  else
    local kb
    kb="$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo 0)"
    ram_gb=$((kb / 1024 / 1024))
  fi

  if [ "$ram_gb" -lt 8 ]; then
    print_warn "⚠️  RAM detected: ${ram_gb}GB (< 8GB). Ollama mistral:7b may be unstable."
  else
    print_ok "RAM detected: ${ram_gb}GB"
  fi
}

preflight_checks() {
  print_info "${BOLD}Step 1 — Pre-flight checks${NC}"

  if ! command_exists docker; then
    print_err "Docker is not installed."
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    print_err "Docker is not running. Start Docker Desktop/Daemon and retry."
    exit 1
  fi
  print_ok "Docker is running."

  if docker compose version >/dev/null 2>&1; then
    print_ok "$(docker compose version)"
  else
    print_err "Docker Compose plugin is unavailable."
    exit 1
  fi

  print_info "Checking ports: ${PORTS[*]}"
  for p in "${PORTS[@]}"; do
    if check_port_available "$p"; then
      print_ok "Port $p is available."
    else
      if [ "$p" = "9092" ]; then
        print_warn "Port 9092 is in use. Note: current backend compose exposes Kafka on host 29092."
      else
        print_warn "Port $p is already in use."
      fi
    fi
  done

  ensure_env_file "$BACKEND_DIR"
  ensure_env_file "$AI_DIR"
  ensure_env_file "$FRONTEND_DIR"

  check_ram
}

start_backend() {
  print_info "${BOLD}Step 2 — Start backend infrastructure${NC}"
  (
    cd "$BACKEND_DIR" || exit 1
    docker compose up -d postgres influxdb zookeeper kafka
    wait_for_container_health "controltwin_postgres" 60 "PostgreSQL" || exit 1
    wait_for_container_health "controltwin_influxdb" 30 "InfluxDB" || exit 1
    docker compose run --rm api alembic upgrade head
    docker compose up -d api
  ) || {
    print_err "Backend startup failed."
    exit 1
  }

  wait_for_http "http://localhost:8000/api/v1/health" 30 "Backend API" || exit 1
}

start_ai() {
  print_info "${BOLD}Step 3 — Start AI service${NC}"
  (
    cd "$AI_DIR" || exit 1
    docker compose -f docker-compose.ai.yml up -d redis chromadb ollama mlflow
  ) || {
    print_err "AI infrastructure startup failed."
    exit 1
  }

  wait_for_container_health "controltwin-ollama" 120 "Ollama" || exit 1

  (
    cd "$AI_DIR" || exit 1
    docker compose -f docker-compose.ai.yml up -d controltwin-ai celery-worker
  ) || {
    print_err "AI app startup failed."
    exit 1
  }

  wait_for_http "http://localhost:8001/api/v1/ai/status" 30 "AI API" || exit 1
}

start_frontend() {
  print_info "${BOLD}Step 4 — Start frontend${NC}"
  (
    cd "$FRONTEND_DIR" || exit 1
    if [ ! -d node_modules ]; then
      print_info "node_modules not found. Running npm install..."
      npm install
    fi
  ) || {
    print_err "Frontend dependency installation failed."
    exit 1
  }

  if [ -f "$FRONTEND_PID_FILE" ]; then
    old_pid="$(cat "$FRONTEND_PID_FILE" 2>/dev/null || true)"
    if [ -n "${old_pid:-}" ] && ps -p "$old_pid" >/dev/null 2>&1; then
      print_warn "Frontend appears already running (PID $old_pid)."
    else
      rm -f "$FRONTEND_PID_FILE"
    fi
  fi

  if [ ! -f "$FRONTEND_PID_FILE" ]; then
    (
      cd "$FRONTEND_DIR" || exit 1
      nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
      echo $! > "$FRONTEND_PID_FILE"
    )
    print_ok "Frontend dev server started in background."
  fi

  wait_for_http "http://localhost:5173" 30 "Frontend" || exit 1
}

print_success_banner() {
  echo -e "${GREEN}"
  cat <<'EOF'
╔══════════════════════════════════════════════╗
║     ControlTwin AI — Stack Ready 🚀          ║
╠══════════════════════════════════════════════╣
║  Backend API  → http://localhost:8000        ║
║  API Docs     → http://localhost:8000/docs   ║
║  AI Service   → http://localhost:8001        ║
║  Frontend     → http://localhost:5173        ║
║  InfluxDB     → http://localhost:8086        ║
║  Ollama       → http://localhost:11434       ║
║  MLflow       → http://localhost:5000        ║
╠══════════════════════════════════════════════╣
║  Default login: admin / ControlTwin2025!     ║
╚══════════════════════════════════════════════╝
EOF
  echo -e "${NC}"
}

stop_frontend() {
  if [ -f "$FRONTEND_PID_FILE" ]; then
    pid="$(cat "$FRONTEND_PID_FILE" 2>/dev/null || true)"
    if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      print_ok "Stopped frontend process PID $pid."
    fi
    rm -f "$FRONTEND_PID_FILE"
  fi

  pkill -f "vite" >/dev/null 2>&1 || true
  pkill -f "npm run dev" >/dev/null 2>&1 || true
}

stop_all() {
  print_info "${BOLD}Stopping all services...${NC}"
  stop_frontend
  (cd "$AI_DIR" && docker compose -f docker-compose.ai.yml down) || true
  (cd "$BACKEND_DIR" && docker compose down) || true
  print_ok "All services stopped."
}

status_line() {
  local name="$1"
  local ok="$2"
  local url="$3"
  if [ "$ok" -eq 0 ]; then
    printf "%-15s | ${GREEN}✅ UP  ${NC} | %s\n" "$name" "$url"
  else
    printf "%-15s | ${RED}❌ DOWN${NC} | %s\n" "$name" "$url"
  fi
}

check_http() {
  curl -fsS "$1" >/dev/null 2>&1
}

check_container_running() {
  docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q true
}

show_status() {
  echo "Service         | Status  | URL"
  echo "----------------|---------|---------------------------"

  check_container_running "controltwin_postgres"; status_line "PostgreSQL" $? "localhost:5432"
  check_http "http://localhost:8086"; status_line "InfluxDB" $? "http://localhost:8086"
  check_container_running "controltwin_kafka"; status_line "Kafka" $? "localhost:9092"
  check_http "http://localhost:8000/api/v1/health"; status_line "Backend API" $? "http://localhost:8000"
  check_http "http://localhost:11434/api/tags"; status_line "Ollama" $? "http://localhost:11434"
  check_http "http://localhost:8010/api/v1/heartbeat"; status_line "ChromaDB" $? "http://localhost:8010"
  check_container_running "controltwin-redis"; status_line "Redis" $? "localhost:6379"
  check_http "http://localhost:8001/api/v1/ai/status"; status_line "AI Service" $? "http://localhost:8001"
  check_http "http://localhost:5173"; status_line "Frontend" $? "http://localhost:5173"
}

show_logs() {
  local svc="${1:-all}"
  case "$svc" in
    all)
      print_info "Streaming backend + ai docker logs (Ctrl+C to stop)..."
      (
        cd "$BACKEND_DIR" || exit 1
        docker compose logs -f &
        p1=$!
        cd "$AI_DIR" || exit 1
        docker compose -f docker-compose.ai.yml logs -f &
        p2=$!
        wait $p1 $p2
      )
      ;;
    backend)
      (cd "$BACKEND_DIR" && docker compose logs -f api)
      ;;
    ai)
      (cd "$AI_DIR" && docker compose -f docker-compose.ai.yml logs -f)
      ;;
    frontend)
      if [ -f "$FRONTEND_LOG" ]; then
        tail -f "$FRONTEND_LOG"
      else
        print_warn "No frontend log file found at $FRONTEND_LOG"
      fi
      ;;
    kafka)
      (cd "$BACKEND_DIR" && docker compose logs -f kafka)
      ;;
    ollama)
      (cd "$AI_DIR" && docker compose -f docker-compose.ai.yml logs -f ollama)
      ;;
    *)
      print_err "Unknown logs target: $svc"
      echo "Usage: ./start.sh logs [backend|ai|frontend|kafka|ollama]"
      exit 1
      ;;
  esac
}

reset_all() {
  read -r -p "This will DELETE all data. Type 'yes' to confirm: " answer
  if [ "$answer" != "yes" ]; then
    print_warn "Reset cancelled."
    exit 0
  fi

  stop_all

  (cd "$BACKEND_DIR" && docker compose down -v) || true
  (cd "$AI_DIR" && docker compose -f docker-compose.ai.yml down -v) || true

  read -r -p "Also remove ollama_models/, chroma_data/, mlflow_data/? Type 'yes' to confirm: " wipe_data
  if [ "$wipe_data" = "yes" ]; then
    rm -rf "$AI_DIR/ollama_models" "$AI_DIR/chroma_data" "$AI_DIR/mlflow_data"
    print_ok "Removed AI local data directories."
  fi

  start_full
}

start_full() {
  preflight_checks
  start_backend
  start_ai
  start_frontend
  print_success_banner
}

start_backend_only() {
  preflight_checks
  start_backend
  print_ok "Backend started."
}

start_ai_only() {
  preflight_checks
  start_ai
  print_ok "AI service started."
}

start_frontend_only() {
  preflight_checks
  start_frontend
  print_ok "Frontend started."
}

restart_target() {
  local target="${1:-all}"
  case "$target" in
    all)
      stop_all
      start_full
      ;;
    backend)
      (cd "$BACKEND_DIR" && docker compose down) || true
      start_backend_only
      ;;
    frontend)
      stop_frontend
      start_frontend_only
      ;;
    ai)
      (cd "$AI_DIR" && docker compose -f docker-compose.ai.yml down) || true
      start_ai_only
      ;;
    *)
      print_err "Unknown restart target: $target"
      echo "Usage: ./start.sh restart [backend|frontend|ai]"
      exit 1
      ;;
  esac
}

usage() {
  cat <<EOF
Usage:
  ./start.sh              Start full stack
  ./start.sh backend      Start only backend
  ./start.sh frontend     Start only frontend
  ./start.sh ai           Start only AI service
  ./start.sh stop         Stop everything
  ./start.sh restart      Stop + start (full stack)
  ./start.sh restart svc  Restart only one service (backend|frontend|ai)
  ./start.sh status       Show status of all services
  ./start.sh logs [svc]   Tail logs (all or specific service)
  ./start.sh reset        Full reset (stop + remove volumes + restart)
EOF
}

main() {
  local cmd="${1:-start}"
  case "$cmd" in
    start)
      start_full
      ;;
    backend)
      start_backend_only
      ;;
    frontend)
      start_frontend_only
      ;;
    ai)
      start_ai_only
      ;;
    stop)
      stop_all
      ;;
    restart)
      restart_target "${2:-all}"
      ;;
    status)
      show_status
      ;;
    logs)
      show_logs "${2:-all}"
      ;;
    reset)
      reset_all
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      print_err "Unknown command: $cmd"
      usage
      exit 1
      ;;
  esac
}

main "$@"
