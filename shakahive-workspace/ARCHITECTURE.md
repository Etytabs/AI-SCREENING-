# NOVARAai Architecture Documentation

## System Overview

NOVARAai is a microservices-based platform for AI-powered research and grant screening. The system is designed to be scalable, fault-tolerant, and high-performance, with GPU acceleration for ML-intensive operations.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         API Gateway                          │
│                      (Port 8000)                            │
│  - Request orchestration                                   │
│  - Load balancing                                           │
│  - Authentication & authorization                           │
└──────────┬──────────────────────────────────────────────────┘
           │
           ├──────────────────────────────────────────────────┐
           │                                                  │
           ▼                                                  ▼
┌──────────────────────┐                          ┌──────────────────────┐
│ Eligibility Service  │                          │ Plagiarism Service   │
│   (Port 8001)        │                          │   (Port 8002)        │
│                      │                          │                      │
│ - Criteria validation│                          │ - Text similarity     │
│ - Field checking     │                          │ - GPU acceleration    │
│ - Rule engine        │                          │ - Embedding models    │
└──────────────────────┘                          └──────────────────────┘
           │                                                  │
           │                                                  │
           ▼                                                  ▼
┌──────────────────────┐                          ┌──────────────────────┐
│ Duplication Service  │                          │ Novelty Service      │
│   (Port 8003)        │                          │   (Port 8004)        │
│                      │                          │                      │
│ - Similarity search  │                          │ - Innovation scoring │
│ - Historical DB      │                          │ - GPU acceleration    │
│ - Fuzzy matching     │                          │ - Multi-dim analysis │
└──────────────────────┘                          └──────────────────────┘
           │                                                  │
           └──────────────────┬───────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Report Service      │
                    │   (Port 8005)        │
                    │                      │
                    │ - Report generation  │
                    │ - HTML/PDF output    │
                    │ - Scoring logic      │
                    └──────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │   PostgreSQL         │
                    │   (Port 5432)        │
                    │                      │
                    │ - Applications        │
                    │ - Reports            │
                    │ - Historical data    │
                    └──────────────────────┘

Supporting Services:
- Redis (Port 6379): Caching and job queue
- Elasticsearch (Port 9200): Similarity search indexing
```

## Service Communication

### Synchronous Communication
- API Gateway → All services via HTTP/REST
- Services communicate synchronously for real-time operations

### Asynchronous Communication
- Background tasks via Celery + Redis
- Event-driven architecture for scalability

## Data Flow

### Screening Process Flow

1. **Application Submission**
   - Client → API Gateway
   - API Gateway stores application in PostgreSQL

2. **Screening Initiation**
   - Client → API Gateway: POST /screen/{id}
   - API Gateway creates background task

3. **Parallel Screening**
   - API Gateway calls all services in parallel:
     - Eligibility Service
     - Plagiarism Service
     - Duplication Service
     - Novelty Service

4. **Result Aggregation**
   - API Gateway collects results from all services
   - Results sent to Report Service

5. **Report Generation**
   - Report Service generates comprehensive report
   - Report stored in PostgreSQL

6. **Client Notification**
   - Client polls status endpoint
   - Final report retrieved when complete

## Technology Stack

### Core Services
- **Framework**: FastAPI (Python 3.11)
- **API Documentation**: OpenAPI/Swagger (auto-generated)
- **Async Runtime**: Uvicorn

### Machine Learning
- **Embeddings**: Sentence Transformers
- **Deep Learning**: PyTorch
- **GPU Support**: CUDA 11.8
- **Similarity**: Cosine similarity, fuzzy matching

### Data Storage
- **Primary Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **Search Engine**: Elasticsearch 8

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (dev), Kubernetes (prod)
- **Load Balancing**: Nginx (prod)

## Performance Optimization

### GPU Acceleration
- Plagiarism Service: CUDA-accelerated embeddings
- Novelty Service: GPU-based transformer inference
- Batch processing for multiple applications

### Caching Strategy
- Redis for frequently accessed data
- Model caching in GPU memory
- Embedding caching for repeated texts

### Database Optimization
- Connection pooling
- Read replicas for reporting
- Indexed queries for fast lookups

### Load Balancing
- Horizontal scaling of stateless services
- GPU node scaling for ML services
- Request queuing for resource-intensive operations

## Security Architecture

### Authentication
- JWT tokens for API authentication
- API key authentication for service-to-service communication

### Authorization
- Role-based access control (RBAC)
- Service-specific permissions

### Data Protection
- Encryption at rest (PostgreSQL)
- Encryption in transit (HTTPS)
- Sensitive data in environment variables

### Rate Limiting
- Per-IP rate limiting
- Per-user rate limiting
- Service-specific limits

## Monitoring & Observability

### Metrics
- Prometheus metrics for all services
- Custom metrics for ML operations
- Performance tracking

### Logging
- Structured JSON logging
- Centralized log aggregation (ELK stack)
- Log levels: DEBUG, INFO, WARNING, ERROR

### Tracing
- Distributed tracing with OpenTelemetry
- Request correlation IDs
- Service dependency mapping

### Health Checks
- /health endpoint for all services
- Dependency health checks
- GPU availability monitoring

## Scalability Strategy

### Horizontal Scaling
- Stateless services can be scaled horizontally
- Load balancer distributes requests
- Auto-scaling based on metrics

### Vertical Scaling
- GPU nodes for ML services
- Memory-optimized nodes for database
- CPU-optimized nodes for API services

### Database Scaling
- Read replicas for reporting queries
- Connection pooling
- Query optimization

## Deployment Architecture

### Development
- Docker Compose for local development
- Hot reload for code changes
- Shared local database

### Staging
- Kubernetes cluster
- Production-like configuration
- Limited resources

### Production
- Kubernetes cluster with auto-scaling
- Multiple availability zones
- CDN for static assets
- Managed database services

## Disaster Recovery

### Backup Strategy
- Daily database backups
- Incremental backups for reports
- Off-site backup storage

### High Availability
- Multi-region deployment
- Failover mechanisms
- Health-based routing

### Recovery Procedures
- Automated backup restoration
- Service restart automation
- Data integrity checks

## Future Enhancements

1. **Web Dashboard**: React-based UI for reviewers
2. **Real-time Collaboration**: WebSocket support
3. **Advanced ML**: Custom fine-tuned models
4. **External Integrations**: PubMed, Google Scholar APIs
5. **Multi-language Support**: Translation services
6. **Mobile App**: iOS and Android applications
