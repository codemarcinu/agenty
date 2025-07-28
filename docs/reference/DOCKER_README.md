# Docker Setup - FoodSave AI

## Overview

This document describes the Docker containerization setup for the FoodSave AI project, following the `.cursorrules` guidelines for security, optimization, and best practices.

## Architecture

The project uses a microservices architecture with the following containers:

- **Backend**: FastAPI (Python 3.12+) with async support
- **Frontend**: Next.js 15 + React 18 + TypeScript
- **Database**: SQLite (file-based)
- **Cache**: Redis 7 for session and task queue
- **AI Models**: Ollama with local Bielik model
- **Task Queue**: Celery with Redis broker
- **Monitoring**: Health checks and logging

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM (16GB+ recommended for AI models)
- NVIDIA GPU with CUDA support (optional, for GPU acceleration)

### Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd AIASISSTMARUBO

# Start development environment
docker-compose -f docker-compose.dev.yaml up -d

# Check health
./health-check.sh

# View logs
docker-compose -f docker-compose.dev.yaml logs -f
```

### Production Environment

```bash
# Build optimized containers
./scripts/deployment/build-all-optimized.sh

# Start production environment
docker-compose up -d

# Check health
./health-check.sh
```

## Container Details

### Backend Container

**Image**: `foodsave-backend:latest`  
**Base**: `python:3.12-slim`  
**Features**:
- Multi-stage build for optimization
- Non-root user for security
- Health checks with retries
- Hot-reload in development
- OCR and AI model support

**Environment Variables**:
```bash
ENVIRONMENT=production
DATABASE_URL=sqlite+aiosqlite:///./foodsave.db
REDIS_URL=redis://host:port
OLLAMA_URL=http://ollama:11434
SECRET_KEY=your-secret-key
```

### Frontend Container

**Image**: `foodsave-frontend:latest`  
**Base**: `node:18-alpine`  
**Features**:
- Multi-stage build with standalone output
- Non-root user for security
- TypeScript strict mode
- Polish localization support
- Optimized bundle size

**Environment Variables**:
```bash
NODE_ENV=production
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_TELEMETRY_DISABLED=1
```

### Database Container

**Image**: `(not applicable for file-based DB)`  
**Features**:
- Persistent data storage
- Health checks (not applicable for file-based DB)
- UTF-8 encoding
- Optimized for async operations

### Cache Container

**Image**: `redis:7-alpine`  
**Features**:
- AOF persistence
- Health checks
- Optional password protection
- Optimized for session storage

### AI Models Container

**Image**: `ollama/ollama:latest`  
**Features**:
- GPU acceleration support
- Local model storage
- Health checks
- Polish language model (Bielik)

## Build Process

### Optimized Build Script

The project includes an optimized build script that follows `.cursorrules` guidelines:

```bash
# Build all containers
./scripts/deployment/build-all-optimized.sh

# Build only development containers
./scripts/deployment/build-all-optimized.sh --dev-only

# Build only production containers
./scripts/deployment/build-all-optimized.sh --prod-only

# Build with custom platform
./scripts/deployment/build-all-optimized.sh --platform linux/arm64
```

### Build Features

- **Multi-stage builds** for smaller final images
- **Layer caching** for faster rebuilds
- **Security scanning** with hadolint and trivy
- **Health check validation**
- **Automatic cleanup** of build artifacts

## Security Features

### Container Security

- **Non-root users**: All containers run as non-root users
- **Minimal base images**: Using slim/alpine variants
- **No unnecessary packages**: Clean package installation
- **Health checks**: Comprehensive health monitoring
- **Resource limits**: Memory and CPU constraints

### Network Security

- **Isolated networks**: Separate network for each environment
- **Port exposure**: Only necessary ports exposed
- **Internal communication**: Services communicate via internal network

### Data Security

- **Encrypted volumes**: Sensitive data stored in encrypted volumes
- **Environment variables**: Secrets managed via environment variables
- **No hardcoded secrets**: All secrets externalized

## Monitoring and Health Checks

### Health Check Script

The project includes a comprehensive health check script:

```bash
# Run health checks
./health-check.sh

# Generate health report
./health-check.sh --report
```

### Health Check Features

- **Retry logic**: Up to 3 retries with configurable delays
- **Service validation**: Checks all running services
- **Resource monitoring**: CPU, memory, and disk usage
- **Log analysis**: Recent error detection
- **Report generation**: Comprehensive health reports

### Monitoring Endpoints

- **Backend**: `http://localhost:8000/health`
- **Frontend**: `http://localhost:3000`
- **Database**: SQLite readiness check (not applicable for file-based DB)
- **Cache**: Redis ping
- **AI Models**: Ollama process check

## Development Workflow

### Hot Reload

Development containers support hot reload:

```bash
# Backend hot reload
docker-compose -f docker-compose.dev.yaml up backend

# Frontend hot reload
docker-compose -f docker-compose.dev.yaml up frontend
```

### Debugging

```bash
# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check container status
docker-compose ps
```

### Testing

```bash
# Run tests in containers
docker-compose exec backend pytest
docker-compose exec frontend npm test

# Run integration tests
docker-compose -f docker-compose.test.yaml up --abort-on-container-exit
```

## Production Deployment

### Environment Configuration

Create a `.env` file for production:

```bash
# Database
POSTGRES_DB=foodsave_prod
POSTGRES_USER=foodsave_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_PASSWORD=secure_redis_password

# Backend
SECRET_KEY=your-super-secure-secret-key
ENVIRONMENT=production
LOG_LEVEL=INFO

# AI Models
OLLAMA_MODEL=SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0
```

### Deployment Commands

```bash
# Build production images
./scripts/deployment/build-all-optimized.sh --prod-only

# Deploy with docker-compose
docker-compose up -d

# Verify deployment
./health-check.sh

# Monitor logs
docker-compose logs -f
```

### Scaling

```bash
# Scale backend workers
docker-compose up -d --scale celery_worker=3

# Scale frontend (with load balancer)
docker-compose up -d --scale frontend=2
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports 8000, 3000, 5433, 6379 are available
2. **Memory issues**: Ensure sufficient RAM for AI models
3. **GPU issues**: Verify NVIDIA Docker runtime for GPU acceleration
4. **Permission issues**: Check file permissions for mounted volumes

### Debug Commands

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs --tail=100 backend

# Check resource usage
docker stats

# Inspect container
docker-compose exec backend bash

# Check network connectivity
docker-compose exec backend ping postgres
```

### Performance Optimization

1. **Use BuildKit**: Enable for faster builds
2. **Layer caching**: Leverage Docker layer caching
3. **Multi-stage builds**: Reduce final image size
4. **Resource limits**: Set appropriate memory/CPU limits

## Compliance with .cursorrules

This Docker setup follows all `.cursorrules` guidelines:

- ✅ **Security-first**: Non-root users, minimal images
- ✅ **Optimization**: Multi-stage builds, layer caching
- ✅ **Monitoring**: Health checks with retries ≤3
- ✅ **Quality gates**: Security scanning, linting
- ✅ **Documentation**: Comprehensive README and examples
- ✅ **Testing**: Integration test support
- ✅ **CI/CD**: Automated build and test pipelines

## Support

For issues and questions:

1. Check the health report: `./health-check.sh`
2. Review container logs: `docker-compose logs -f`
3. Consult the troubleshooting section
4. Check the project documentation

## License

This Docker setup is part of the FoodSave AI project and follows the same license terms. 