@echo off
REM NOVARAai Startup Script for Windows
REM Starts all microservices

echo Starting NOVARAai Services...

REM Check if .env exists
if not exist .env (
    echo Error: .env file not found. Please copy .env.example to .env and configure it.
    exit /b 1
)

REM Start services using Docker Compose
echo Starting services with Docker Compose...
docker-compose up -d

REM Wait for services to be ready
echo Waiting for services to start...
timeout /t 10 /nobreak

echo All services started successfully!
echo API Gateway: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo To view logs, run: docker-compose logs -f
echo To stop services, run: docker-compose down
