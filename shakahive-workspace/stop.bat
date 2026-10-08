@echo off
REM NOVARAai Stop Script for Windows
REM Stops all microservices

echo Stopping NOVARAai Services...

docker-compose down

echo All services stopped successfully.
