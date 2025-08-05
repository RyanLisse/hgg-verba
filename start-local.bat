@echo off
REM Verba Local Deployment Startup Script for Windows
REM This script sets up and starts Verba with local Weaviate Docker deployment

setlocal enabledelayedexpansion

echo =====================================
echo    Verba Local Deployment Startup    
echo =====================================
echo.

REM Check prerequisites
echo Checking prerequisites...

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://docs.docker.com/desktop/windows/install/
    pause
    exit /b 1
)

REM Check Docker Compose
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker Compose is not available
    echo Please ensure Docker Desktop is installed with Compose
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop
    pause
    exit /b 1
)

echo [OK] Docker and Docker Compose are installed and running
echo.

REM Check for .env file
echo Checking environment configuration...

if not exist .env (
    if exist .env.local (
        echo Creating .env from .env.local template...
        copy .env.local .env >nul
        echo [OK] Created .env file
    ) else if exist .env.example (
        echo Creating .env from .env.example template...
        copy .env.example .env >nul
        echo [OK] Created .env file
    ) else (
        echo Warning: No .env file found
        echo Creating minimal .env for local deployment...
        (
            echo # Verba Local Deployment Configuration
            echo WEAVIATE_URL_VERBA=http://localhost:8080
            echo WEAVIATE_API_KEY_VERBA=
            echo.
            echo # Add your API keys here
            echo OPENAI_API_KEY=
            echo ANTHROPIC_API_KEY=
            echo GOOGLE_API_KEY=
            echo COHERE_API_KEY=
        ) > .env
        echo [OK] Created minimal .env file
    )
)

REM Check if services are already running
docker compose ps 2>nul | findstr "running" >nul
if %errorlevel% equ 0 (
    echo Services are already running. Restarting...
    docker compose down
    timeout /t 2 /nobreak >nul
)

REM Start services
echo.
echo Starting Weaviate and Verba...
docker compose up -d

if %errorlevel% neq 0 (
    echo Error: Failed to start services
    echo Check Docker Desktop and try again
    pause
    exit /b 1
)

REM Wait for services to be ready
echo.
echo Waiting for services to start...
echo This may take up to 30 seconds...

REM Wait for Weaviate
set WEAVIATE_READY=0
for /l %%i in (1,1,30) do (
    curl -s http://localhost:8080/v1/.well-known/ready >nul 2>&1
    if !errorlevel! equ 0 (
        set WEAVIATE_READY=1
        goto :weaviate_check_done
    )
    echo | set /p=.
    timeout /t 2 /nobreak >nul
)
:weaviate_check_done
echo.

if !WEAVIATE_READY! equ 1 (
    echo [OK] Weaviate is ready
) else (
    echo [ERROR] Weaviate failed to start
    echo Check logs with: docker compose logs weaviate
    pause
    exit /b 1
)

REM Wait for Verba
set VERBA_READY=0
for /l %%i in (1,1,30) do (
    curl -s http://localhost:8000 >nul 2>&1
    if !errorlevel! equ 0 (
        set VERBA_READY=1
        goto :verba_check_done
    )
    echo | set /p=.
    timeout /t 2 /nobreak >nul
)
:verba_check_done
echo.

if !VERBA_READY! equ 1 (
    echo [OK] Verba is ready
) else (
    echo [ERROR] Verba failed to start
    echo Check logs with: docker compose logs verba
    pause
    exit /b 1
)

REM Success message
echo.
echo =====================================
echo   Local Deployment Started Successfully!
echo =====================================
echo.
echo Access points:
echo   - Verba UI:      http://localhost:8000
echo   - Weaviate API:  http://localhost:8080
echo   - Weaviate gRPC: localhost:50051
echo.
echo Useful commands:
echo   - View logs:      docker compose logs -f
echo   - Stop services:  docker compose down
echo   - Reset data:     docker compose down -v
echo   - View status:    docker compose ps
echo.

REM Open browser
echo Opening Verba in your browser...
start http://localhost:8000

echo.
echo Press any key to view logs, or close this window to run in background...
pause >nul

docker compose logs -f