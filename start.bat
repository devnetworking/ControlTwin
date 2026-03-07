@echo off
setlocal EnableDelayedExpansion

REM ControlTwin — Complete Stack Startup Script (Windows cmd)

set "ESC="
for /F "delims=" %%e in ('echo prompt $E ^| cmd') do set "ESC=%%e"

set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "BOLD=%ESC%[1m"
set "NC=%ESC%[0m"

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

set "BACKEND_DIR=%ROOT_DIR%\controltwin-backend"
set "FRONTEND_DIR=%ROOT_DIR%\controltwin-frontend"
set "AI_DIR=%ROOT_DIR%\controltwin-ai"
set "FRONTEND_LOG=%FRONTEND_DIR%\frontend.log"
set "FRONTEND_PID_FILE=%FRONTEND_DIR%\.frontend.pid"

if "%~1"=="" set "CMD=start"
if not "%~1"=="" set "CMD=%~1"

if /I "%CMD%"=="start" goto :start_full
if /I "%CMD%"=="backend" goto :start_backend_only
if /I "%CMD%"=="frontend" goto :start_frontend_only
if /I "%CMD%"=="ai" goto :start_ai_only
if /I "%CMD%"=="stop" goto :stop_all
if /I "%CMD%"=="status" goto :show_status
if /I "%CMD%"=="logs" goto :logs_dispatch
if /I "%CMD%"=="reset" goto :reset_all
if /I "%CMD%"=="restart" goto :restart_dispatch
if /I "%CMD%"=="help" goto :usage
if /I "%CMD%"=="-h" goto :usage
if /I "%CMD%"=="--help" goto :usage

echo %RED%Unknown command: %CMD%%NC%
goto :usage

:print_info
echo %CYAN%%~1%NC%
exit /b 0

:print_ok
echo %GREEN%%~1%NC%
exit /b 0

:print_warn
echo %YELLOW%%~1%NC%
exit /b 0

:print_err
echo %RED%%~1%NC%
exit /b 0

:check_env_file
set "TARGET_DIR=%~1"
if not exist "%TARGET_DIR%\.env" (
  if exist "%TARGET_DIR%\.env.example" (
    copy /Y "%TARGET_DIR%\.env.example" "%TARGET_DIR%\.env" >nul
    call :print_warn "Created missing .env in %TARGET_DIR%"
  ) else (
    call :print_warn "No .env.example in %TARGET_DIR%"
  )
)
exit /b 0

:check_port
set "PORT=%~1"
netstat -an | findstr /R /C:":%PORT% .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
  exit /b 1
) else (
  exit /b 0
)

:wait_http
set "WAIT_URL=%~1"
set "WAIT_TIMEOUT=%~2"
set "WAIT_NAME=%~3"
set /a ELAPSED=0

:wait_http_loop
curl -fsS "%WAIT_URL%" >nul 2>&1
if %errorlevel%==0 (
  call :print_ok "✅ %WAIT_NAME% is ready (%WAIT_URL%)"
  exit /b 0
)

if %ELAPSED% GEQ %WAIT_TIMEOUT% (
  call :print_err "❌ Timeout waiting for %WAIT_NAME% (%WAIT_URL%)"
  exit /b 1
)

timeout /t 2 >nul
set /a ELAPSED+=2
goto :wait_http_loop

:wait_container
set "CNAME=%~1"
set "CTIMEOUT=%~2"
set "CFRIEND=%~3"
set /a CELAPSED=0

:wait_container_loop
for /f "delims=" %%s in ('docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" "%CNAME%" 2^>nul') do set "CSTATUS=%%s"
if /I "!CSTATUS!"=="healthy" (
  call :print_ok "✅ %CFRIEND% is ready (container: %CNAME%)"
  exit /b 0
)
if /I "!CSTATUS!"=="running" (
  call :print_ok "✅ %CFRIEND% is ready (container: %CNAME%)"
  exit /b 0
)

if %CELAPSED% GEQ %CTIMEOUT% (
  call :print_err "❌ Timeout waiting for %CFRIEND% (container: %CNAME%)"
  exit /b 1
)

timeout /t 2 >nul
set /a CELAPSED+=2
goto :wait_container_loop

:check_ram
for /f "tokens=2 delims==" %%m in ('wmic computersystem get TotalPhysicalMemory /value ^| findstr TotalPhysicalMemory') do set "MEM_BYTES=%%m"
if not defined MEM_BYTES (
  call :print_warn "Unable to detect RAM"
  exit /b 0
)
set /a MEM_GB=%MEM_BYTES:~0,-9%
if %MEM_GB% LSS 8 (
  call :print_warn "⚠ RAM detected: %MEM_GB%GB (< 8GB). Ollama mistral:7b may be unstable."
) else (
  call :print_ok "RAM detected: %MEM_GB%GB"
)
exit /b 0

:preflight
call :print_info "Step 1 — Pre-flight checks"

where docker >nul 2>&1
if not %errorlevel%==0 (
  call :print_err "Docker is not installed."
  exit /b 1
)

docker info >nul 2>&1
if not %errorlevel%==0 (
  call :print_err "Docker is not running. Start Docker Desktop and retry."
  exit /b 1
)
call :print_ok "Docker is running."

docker compose version >nul 2>&1
if not %errorlevel%==0 (
  call :print_err "Docker Compose plugin is unavailable."
  exit /b 1
)

for %%p in (8000 8001 5432 8086 9092 6379 8010 11434 5173) do (
  call :check_port %%p
  if !errorlevel! EQU 0 (
    call :print_ok "Port %%p is available."
  ) else (
    if "%%p"=="9092" (
      call :print_warn "Port 9092 is in use. Note: compose maps Kafka to 29092 on host."
    ) else (
      call :print_warn "Port %%p is already in use."
    )
  )
)

call :check_env_file "%BACKEND_DIR%"
call :check_env_file "%AI_DIR%"
call :check_env_file "%FRONTEND_DIR%"

call :check_ram
exit /b 0

:start_backend
call :print_info "Step 2 — Start backend infrastructure"
pushd "%BACKEND_DIR%"
docker compose up -d postgres influxdb zookeeper kafka
if not %errorlevel%==0 (popd & exit /b 1)

call :wait_container "controltwin_postgres" 60 "PostgreSQL"
if not %errorlevel%==0 (popd & exit /b 1)

call :wait_container "controltwin_influxdb" 30 "InfluxDB"
if not %errorlevel%==0 (popd & exit /b 1)

docker compose run --rm api alembic upgrade head
if not %errorlevel%==0 (popd & exit /b 1)

docker compose up -d api
if not %errorlevel%==0 (popd & exit /b 1)
popd

call :wait_http "http://localhost:8000/api/v1/health" 30 "Backend API"
if not %errorlevel%==0 exit /b 1
exit /b 0

:start_ai
call :print_info "Step 3 — Start AI service"
pushd "%AI_DIR%"
docker compose -f docker-compose.ai.yml up -d redis chromadb ollama mlflow
if not %errorlevel%==0 (popd & exit /b 1)
popd

call :wait_container "controltwin-ollama" 120 "Ollama"
if not %errorlevel%==0 exit /b 1

pushd "%AI_DIR%"
docker compose -f docker-compose.ai.yml up -d controltwin-ai celery-worker
if not %errorlevel%==0 (popd & exit /b 1)
popd

call :wait_http "http://localhost:8001/api/v1/ai/status" 30 "AI API"
if not %errorlevel%==0 exit /b 1
exit /b 0

:start_frontend
call :print_info "Step 4 — Start frontend"
if not exist "%FRONTEND_DIR%\node_modules" (
  pushd "%FRONTEND_DIR%"
  call npm install
  if not %errorlevel%==0 (popd & exit /b 1)
  popd
)

if exist "%FRONTEND_PID_FILE%" del /q "%FRONTEND_PID_FILE%" >nul 2>&1

pushd "%FRONTEND_DIR%"
start "controltwin-frontend-dev" /min cmd /c "npm run dev > ""%FRONTEND_LOG%"" 2>&1"
popd

call :wait_http "http://localhost:5173" 30 "Frontend"
if not %errorlevel%==0 exit /b 1
exit /b 0

:banner
echo %GREEN%
echo ╔══════════════════════════════════════════════╗
echo ║     ControlTwin AI — Stack Ready 🚀          ║
echo ╠══════════════════════════════════════════════╣
echo ║  Backend API  → http://localhost:8000        ║
echo ║  API Docs     → http://localhost:8000/docs   ║
echo ║  AI Service   → http://localhost:8001        ║
echo ║  Frontend     → http://localhost:5173        ║
echo ║  InfluxDB     → http://localhost:8086        ║
echo ║  Ollama       → http://localhost:11434       ║
echo ║  MLflow       → http://localhost:5000        ║
echo ╠══════════════════════════════════════════════╣
echo ║  Default login: admin / ControlTwin2025!     ║
echo ╚══════════════════════════════════════════════╝
echo %NC%
exit /b 0

:start_full
call :preflight
if not %errorlevel%==0 exit /b 1
call :start_backend
if not %errorlevel%==0 exit /b 1
call :start_ai
if not %errorlevel%==0 exit /b 1
call :start_frontend
if not %errorlevel%==0 exit /b 1
call :banner
exit /b 0

:start_backend_only
call :preflight
if not %errorlevel%==0 exit /b 1
call :start_backend
if not %errorlevel%==0 exit /b 1
call :print_ok "Backend started."
exit /b 0

:start_ai_only
call :preflight
if not %errorlevel%==0 exit /b 1
call :start_ai
if not %errorlevel%==0 exit /b 1
call :print_ok "AI service started."
exit /b 0

:start_frontend_only
call :preflight
if not %errorlevel%==0 exit /b 1
call :start_frontend
if not %errorlevel%==0 exit /b 1
call :print_ok "Frontend started."
exit /b 0

:stop_frontend
taskkill /FI "WINDOWTITLE eq controltwin-frontend-dev*" /F >nul 2>&1
taskkill /IM node.exe /F >nul 2>&1
exit /b 0

:stop_all
call :print_info "Stopping all services..."
call :stop_frontend
pushd "%AI_DIR%"
docker compose -f docker-compose.ai.yml down
popd
pushd "%BACKEND_DIR%"
docker compose down
popd
call :print_ok "All services stopped."
exit /b 0

:status_line
set "SVC=%~1"
set "STATE=%~2"
set "URL=%~3"
if /I "%STATE%"=="UP" (
  echo %SVC% ^| %GREEN%✅ UP%NC% ^| %URL%
) else (
  echo %SVC% ^| %RED%❌ DOWN%NC% ^| %URL%
)
exit /b 0

:show_status
echo Service         ^| Status  ^| URL
echo ----------------^|---------^|---------------------------
curl -fsS "http://localhost:8000/api/v1/health" >nul 2>&1 && (call :status_line "Backend API     " "UP" "http://localhost:8000") || (call :status_line "Backend API     " "DOWN" "http://localhost:8000")
curl -fsS "http://localhost:8001/api/v1/ai/status" >nul 2>&1 && (call :status_line "AI Service      " "UP" "http://localhost:8001") || (call :status_line "AI Service      " "DOWN" "http://localhost:8001")
curl -fsS "http://localhost:5173" >nul 2>&1 && (call :status_line "Frontend        " "UP" "http://localhost:5173") || (call :status_line "Frontend        " "DOWN" "http://localhost:5173")
curl -fsS "http://localhost:8086" >nul 2>&1 && (call :status_line "InfluxDB        " "UP" "http://localhost:8086") || (call :status_line "InfluxDB        " "DOWN" "http://localhost:8086")
curl -fsS "http://localhost:11434/api/tags" >nul 2>&1 && (call :status_line "Ollama          " "UP" "http://localhost:11434") || (call :status_line "Ollama          " "DOWN" "http://localhost:11434")
curl -fsS "http://localhost:8010/api/v1/heartbeat" >nul 2>&1 && (call :status_line "ChromaDB        " "UP" "http://localhost:8010") || (call :status_line "ChromaDB        " "DOWN" "http://localhost:8010")
docker inspect -f "{{.State.Running}}" controltwin_postgres 2>nul | findstr /I "true" >nul && (call :status_line "PostgreSQL      " "UP" "localhost:5432") || (call :status_line "PostgreSQL      " "DOWN" "localhost:5432")
docker inspect -f "{{.State.Running}}" controltwin_kafka 2>nul | findstr /I "true" >nul && (call :status_line "Kafka           " "UP" "localhost:9092") || (call :status_line "Kafka           " "DOWN" "localhost:9092")
docker inspect -f "{{.State.Running}}" controltwin-redis 2>nul | findstr /I "true" >nul && (call :status_line "Redis           " "UP" "localhost:6379") || (call :status_line "Redis           " "DOWN" "localhost:6379")
exit /b 0

:logs_dispatch
set "LOG_TARGET=%~2"
if "%LOG_TARGET%"=="" set "LOG_TARGET=all"

if /I "%LOG_TARGET%"=="all" (
  call :print_info "Backend logs stream:"
  pushd "%BACKEND_DIR%"
  start "controltwin-backend-logs" cmd /k "docker compose logs -f"
  popd
  call :print_info "AI logs stream:"
  pushd "%AI_DIR%"
  start "controltwin-ai-logs" cmd /k "docker compose -f docker-compose.ai.yml logs -f"
  popd
  exit /b 0
)

if /I "%LOG_TARGET%"=="backend" (
  pushd "%BACKEND_DIR%"
  docker compose logs -f api
  popd
  exit /b 0
)

if /I "%LOG_TARGET%"=="ai" (
  pushd "%AI_DIR%"
  docker compose -f docker-compose.ai.yml logs -f
  popd
  exit /b 0
)

if /I "%LOG_TARGET%"=="frontend" (
  if exist "%FRONTEND_LOG%" (
    powershell -NoProfile -Command "Get-Content -Path '%FRONTEND_LOG%' -Wait -Tail 100"
  ) else (
    call :print_warn "No frontend log file found at %FRONTEND_LOG%"
  )
  exit /b 0
)

if /I "%LOG_TARGET%"=="kafka" (
  pushd "%BACKEND_DIR%"
  docker compose logs -f kafka
  popd
  exit /b 0
)

if /I "%LOG_TARGET%"=="ollama" (
  pushd "%AI_DIR%"
  docker compose -f docker-compose.ai.yml logs -f ollama
  popd
  exit /b 0
)

call :print_err "Unknown logs target: %LOG_TARGET%"
exit /b 1

:reset_all
set /p CONFIRM=This will DELETE all data. Type 'yes' to confirm: 
if /I not "%CONFIRM%"=="yes" (
  call :print_warn "Reset cancelled."
  exit /b 0
)

call :stop_all

pushd "%BACKEND_DIR%"
docker compose down -v
popd

pushd "%AI_DIR%"
docker compose -f docker-compose.ai.yml down -v
popd

set /p CONFIRM2=Also remove ollama_models\, chroma_data\, mlflow_data\ ? Type 'yes' to confirm: 
if /I "%CONFIRM2%"=="yes" (
  rmdir /s /q "%AI_DIR%\ollama_models" 2>nul
  rmdir /s /q "%AI_DIR%\chroma_data" 2>nul
  rmdir /s /q "%AI_DIR%\mlflow_data" 2>nul
)

goto :start_full

:restart_dispatch
set "TARGET=%~2"
if "%TARGET%"=="" set "TARGET=all"

if /I "%TARGET%"=="all" (
  call :stop_all
  goto :start_full
)

if /I "%TARGET%"=="backend" (
  pushd "%BACKEND_DIR%"
  docker compose down
  popd
  goto :start_backend_only
)

if /I "%TARGET%"=="frontend" (
  call :stop_frontend
  goto :start_frontend_only
)

if /I "%TARGET%"=="ai" (
  pushd "%AI_DIR%"
  docker compose -f docker-compose.ai.yml down
  popd
  goto :start_ai_only
)

call :print_err "Unknown restart target: %TARGET%"
exit /b 1

:usage
echo Usage:
echo   start.bat              Start full stack
echo   start.bat backend      Start only backend
echo   start.bat frontend     Start only frontend
echo   start.bat ai           Start only AI service
echo   start.bat stop         Stop everything
echo   start.bat restart      Stop + start
echo   start.bat status       Show status of all services
echo   start.bat logs [svc]   Tail logs (all/backend/ai/frontend/kafka/ollama)
echo   start.bat reset        Full reset (stop + remove volumes + restart)
exit /b 0
