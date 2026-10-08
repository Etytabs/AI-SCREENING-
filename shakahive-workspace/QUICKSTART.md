# Quick Start Guide

Get NOVARAai up and running in minutes.

## Prerequisites

- Docker and Docker Compose installed
- NVIDIA GPU with CUDA support (optional but recommended)
- At least 8GB RAM available

## Installation Steps

### 1. Clone and Setup

```bash
# Navigate to project directory
cd NOVARAai

# Copy environment file
cp .env.example .env

# Edit .env if needed (optional for basic setup)
```

### 2. Start Services

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

Or manually:
```bash
docker-compose up -d
```

### 3. Verify Services

Check that all services are running:
```bash
docker-compose ps
```

Test the API Gateway:
```bash
curl http://localhost:8000/health
```

### 4. Submit a Test Application

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI-Powered Agriculture in Rwanda",
    "abstract": "This project develops machine learning solutions for crop disease detection using satellite imagery and IoT sensors.",
    "full_proposal": "Detailed proposal describing the methodology, expected outcomes, and implementation plan for AI-powered agricultural monitoring systems in Rwanda.",
    "author_name": "Dr. Jean Mugabo",
    "institution": "University of Rwanda",
    "email": "jean.mugabo@ur.ac.rw",
    "budget_amount": 750000,
    "research_area": "Agriculture Technology",
    "keywords": ["AI", "Agriculture", "IoT", "Machine Learning"],
    "grant_type": "research",
    "funding_program": "NCST Innovation Grant 2024",
    "project_duration_months": 24,
    "team_members": [
      {"name": "Dr. Jean Mugabo", "role": "Principal Investigator"},
      {"name": "Marie Claire Uwimana", "role": "Co-Investigator"}
    ],
    "expected_outcomes": [
      "Reduced crop disease detection time by 50%",
      "Improved yield prediction accuracy by 30%",
      "Deployment in 5 districts"
    ]
  }'
```

### 5. Start Screening

Replace `{application_id}` with the ID from step 4:

```bash
curl -X POST http://localhost:8000/screen/{application_id} \
  -H "Content-Type: application/json" \
  -d '{
    "skip_plagiarism": false,
    "skip_duplication": false,
    "skip_novelty": false,
    "priority": "normal"
  }'
```

### 6. Check Status

```bash
curl http://localhost:8000/status/{application_id}
```

### 7. Get Report

Once screening is complete:

```bash
curl http://localhost:8000/report/{application_id}
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Stopping Services

**Windows:**
```bash
stop.bat
```

**Linux/Mac:**
```bash
chmod +x stop.sh
./stop.sh
```

Or manually:
```bash
docker-compose down
```

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f plagiarism-service
```

## Troubleshooting

### Services won't start
```bash
# Check Docker
docker --version
docker-compose --version

# Check port availability
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac
```

### GPU not detected
```bash
# Check NVIDIA drivers
nvidia-smi

# Check CUDA
nvcc --version
```

### Database connection issues
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Out of memory
```bash
# Reduce Docker memory limits in docker-compose.yml
# Or increase system memory allocation to Docker
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture
- Configure custom eligibility criteria
- Integrate with your existing grant management system
- Set up monitoring and alerting

## Support

For issues or questions:
- Check the documentation
- Review service logs
- Contact the development team
