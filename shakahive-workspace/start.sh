#!/bin/bash

# NOVARAai Startup Script
# Starts all microservices

echo "Starting NOVARAai Services..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Start services using Docker Compose
echo "Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."
curl -s http://localhost:8000/health | python -m json.tool
curl -s http://localhost:8001/health | python -m json.tool
curl -s http://localhost:8002/health | python -m json.tool
curl -s http://localhost:8003/health | python -m json.tool
curl -s http://localhost:8004/health | python -m json.tool
curl -s http://localhost:8005/health | python -m json.tool

echo "All services started successfully!"
echo "API Gateway: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
