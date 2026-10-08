# NOVARAai - AI-Powered Research and Grant Screening Platform

An intelligent, GPU-accelerated microservices platform for automating the screening of grant applications, research proposals, and innovation submissions. Designed for research and innovation institutions like NCST Rwanda to reduce screening time from days to minutes.

## 🚀 Features

- **Automated Eligibility Verification**: Checks applications against grant-specific criteria
- **Plagiarism Detection**: GPU-accelerated text similarity analysis using transformer models
- **Duplication Detection**: Identifies similar or duplicate proposals from historical data
- **Novelty Assessment**: Evaluates innovation potential using multi-dimensional analysis
- **Comprehensive Reporting**: Generates structured screening reports in minutes
- **Microservices Architecture**: Scalable, independent services for optimal performance
- **GPU Acceleration**: Leverages CUDA for fast ML inference
- **RESTful API**: Easy integration with existing systems

## 🏗️ Architecture

The platform consists of six microservices:

1. **API Gateway** (Port 8000): Orchestrates screening workflows
2. **Eligibility Service** (Port 8001): Validates application eligibility
3. **Plagiarism Service** (Port 8002): GPU-accelerated plagiarism detection
4. **Duplication Service** (Port 8003): Checks for duplicate proposals
5. **Novelty Service** (Port 8004): Assesses innovation and novelty
6. **Report Service** (Port 8005): Generates screening reports

Supporting infrastructure:
- PostgreSQL: Application and report storage
- Redis: Caching and job queue
- Elasticsearch: Similarity search and indexing

## 📋 Requirements

### Hardware
- GPU with CUDA support (NVIDIA GPU recommended for optimal performance)
- Minimum 8GB RAM (16GB+ recommended)
- 50GB+ disk space

### Software
- Docker & Docker Compose
- Python 3.11+
- CUDA 11.8+ (for GPU acceleration)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd NOVARAai
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Services with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 5. Start Services Locally (Development)

```bash
# Start each service in separate terminals

# Terminal 1: API Gateway
cd services/api-gateway
python main.py

# Terminal 2: Eligibility Service
cd services/eligibility-service
python main.py

# Terminal 3: Plagiarism Service (GPU)
cd services/plagiarism-service
python main.py

# Terminal 4: Duplication Service
cd services/duplication-service
python main.py

# Terminal 5: Novelty Service (GPU)
cd services/novelty-service
python main.py

# Terminal 6: Report Service
cd services/report-service
python main.py
```

## 📖 Usage

### Submit an Application

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI-Powered Crop Disease Detection",
    "abstract": "This research aims to develop innovative solutions...",
    "full_proposal": "Detailed proposal content...",
    "author_name": "Dr. John Doe",
    "institution": "University of Rwanda",
    "email": "john.doe@university.rw",
    "budget_amount": 500000,
    "research_area": "Agriculture Technology",
    "keywords": ["AI", "Agriculture", "Machine Learning"],
    "grant_type": "research",
    "funding_program": "NCST Innovation Grant",
    "project_duration_months": 24
  }'
```

### Start Screening

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

### Check Screening Status

```bash
curl http://localhost:8000/status/{application_id}
```

### Get Screening Report

```bash
curl http://localhost:8000/report/{application_id}
```

## 🔌 API Endpoints

### API Gateway (Port 8000)

- `POST /applications` - Submit new application
- `POST /applications/upload` - Upload application file
- `POST /screen/{application_id}` - Start screening process
- `GET /status/{application_id}` - Get screening status
- `GET /report/{application_id}` - Get screening report
- `GET /applications` - List all applications
- `GET /applications/{application_id}` - Get application details
- `DELETE /applications/{application_id}` - Delete application
- `GET /health` - Health check

### Eligibility Service (Port 8001)

- `POST /check` - Check eligibility
- `POST /validate-criteria` - Validate eligibility criteria
- `GET /health` - Health check

### Plagiarism Service (Port 8002)

- `POST /detect` - Detect plagiarism
- `POST /batch-detect` - Batch plagiarism detection
- `GET /health` - Health check

### Duplication Service (Port 8003)

- `POST /check` - Check for duplicates
- `POST /add-historical` - Add historical proposal
- `GET /health` - Health check

### Novelty Service (Port 8004)

- `POST /assess` - Assess novelty
- `POST /batch-assess` - Batch novelty assessment
- `GET /health` - Health check

### Report Service (Port 8005)

- `POST /generate` - Generate screening report
- `POST /generate-html` - Generate HTML report
- `POST /generate-pdf` - Generate PDF report
- `GET /health` - Health check

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest tests/ --cov=.

# Run specific service tests
pytest tests/test_eligibility_service.py
```

## 📊 Performance

### Expected Processing Times

- Eligibility Check: < 1 second
- Plagiarism Detection: 10-30 seconds (GPU-accelerated)
- Duplication Check: 5-15 seconds
- Novelty Assessment: 15-45 seconds (GPU-accelerated)
- Report Generation: < 2 seconds
- **Total Screening Time: 30-90 seconds** (vs. days/weeks manually)

### GPU Acceleration Benefits

- **10-50x faster** inference for transformer models
- Parallel processing of multiple applications
- Reduced CPU load for other services

## 🔒 Security Considerations

- API keys should be stored in environment variables
- Use HTTPS in production
- Implement authentication/authorization
- Sanitize all user inputs
- Rate limiting to prevent abuse
- Regular security updates

## 🚀 Deployment

### Production Deployment

1. **Use Kubernetes** for orchestration
2. **Enable HTTPS** with SSL certificates
3. **Configure load balancers** for high availability
4. **Set up monitoring** (Prometheus, Grafana)
5. **Implement logging** (ELK stack)
6. **Configure backups** for databases
7. **Use secrets management** (Vault, AWS Secrets Manager)

### Scaling

- **Horizontal scaling**: Add more instances of each service
- **GPU scaling**: Add more GPU nodes for ML services
- **Database scaling**: Use read replicas for PostgreSQL
- **Cache scaling**: Use Redis Cluster

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- NCST Rwanda for the use case and requirements
- Sentence Transformers for embedding models
- Hugging Face for transformer models
- FastAPI for the web framework

## 📧 Contact

For questions or support, please contact [your-email@example.com]

## 🗺️ Roadmap

- [ ] Web dashboard for reviewers
- [ ] Integration with external databases (PubMed, Google Scholar)
- [ ] Advanced plagiarism detection with citation analysis
- [ ] Multi-language support
- [ ] Real-time collaboration features
- [ ] Mobile application
- [ ] Advanced analytics and reporting
- [ ] Integration with grant management systems
