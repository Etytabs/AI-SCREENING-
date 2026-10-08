#!/bin/bash

# NOVARAai Stop Script
# Stops all microservices

echo "Stopping NOVARAai Services..."

docker-compose down

echo "All services stopped successfully."
