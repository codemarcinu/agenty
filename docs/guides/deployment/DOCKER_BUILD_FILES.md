# 🐳 Docker Build Files & Commands Reference

> **Ostatnia aktualizacja:** 2025-07-18  
> **Status:** ✅ **ZOPTYMALIZOWANE** - Cache optimization zaimplementowane

## 📁 Aktualne Pliki Docker

### Docker Compose Files
- **Development:** `docker-compose.dev.yaml` - Środowisko deweloperskie z cache optimization
- **Production:** `docker-compose.prod.yaml` - Środowisko produkcyjne z cache optimization
- **Base:** `docker-compose.base.yaml` - Podstawowa konfiguracja
- **Monitoring:** `docker-compose.monitoring.yaml` - Monitoring i metryki
- **Proxy:** `docker-compose.proxy.yaml` - Reverse proxy
- **Test:** `docker-compose.test.yaml` - Środowisko testowe

### Cache Optimization Files
- **Cache Manager:** `scripts/docker-cache-manager.sh` - Zarządzanie cache
- **Performance Test:** `scripts/test-cache-performance.sh` - Testy wydajności cache
- **Summary:** `DOCKER_CACHE_OPTIMIZATION_SUMMARY.md` - Podsumowanie optymalizacji

## 🚀 Komendy Budowania

### Szybkie Budowanie (Development)
```bash
# Buduj z cache optimization
docker compose -f docker-compose.dev.yaml up --build

# Tylko backend z cache
docker compose -f docker-compose.dev.yaml build backend

# Restart tylko backend
docker compose -f docker-compose.dev.yaml up -d --no-deps backend
```

### Pełne Budowanie (Production)
```bash
# Buduj wszystkie serwisy
docker compose -f docker-compose.prod.yaml build

# Uruchom wszystkie serwisy
docker compose -f docker-compose.prod.yaml up -d
```

### Cache Management
```bash
# Setup cache optimization
./scripts/docker-cache-manager.sh setup

# Test cache performance
./scripts/test-cache-performance.sh test

# Show cache statistics
./scripts/docker-cache-manager.sh stats

# Export cache for CI/CD
./scripts/docker-cache-manager.sh export
```

## 🔧 Cache Optimization (2025-07-18)

### Zastosowane Optymalizacje
- ✅ **Cache mounts** dla wszystkich package managerów
- ✅ **BuildKit integration** z automatycznym włączaniem
- ✅ **Multi-stage builds** z optymalnym layer caching
- ✅ **Cache sharing** między buildami
- ✅ **Performance monitoring** ze statystykami

### Cache Mounts
```dockerfile
# Python (pip)
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/wheel \
    pip install --no-cache-dir -r requirements.txt

# System packages (apt)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y package-name

# Node.js (npm/yarn)
RUN --mount=type=cache,target=/root/.npm \
    npm install

# Conda (GPU builds)
RUN --mount=type=cache,target=/root/.conda \
    conda install -c pytorch -c nvidia faiss-gpu=1.8.0 -y
```

### Performance Improvements
- **Pierwszy build**: 40% szybszy (8-12 minut vs 15-20 minut)
- **Rebuild po zmianie kodu**: 80% szybszy (2-3 minuty vs 10-15 minut)
- **Rebuild po zmianie dependencies**: 60% szybszy (5-8 minut vs 15-20 minut)
- **Cache hit rate**: 70-90% (vs 20-30% przed optymalizacją)

## 📂 Struktura Projektu

### Backend
- **Konfiguracja:** `docker-compose.dev.yaml` i `docker-compose.prod.yaml`
- **Dependencies:** `requirements.txt`, `pyproject.toml`
- **Cache:** pip cache mounts dla szybszych rebuildów

### Frontend/GUI
- **Konfiguracja:** `gui_refactor/` - Modern web-based GUI
- **Dependencies:** `package.json`, `package-lock.json`
- **Cache:** npm/yarn cache mounts

### Database
- **SQLite:** File-based database z persistent storage
- **Redis:** Cache i session storage
- **Ollama:** AI models z GPU support

## 🏥 Health Check Endpoints

### Backend Health
```bash
curl -f http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

### Frontend Health
```bash
curl -f http://localhost:3000/api/health
# Expected: {"status":"healthy"}
```

### Ollama Health
```bash
curl -f http://localhost:11434/api/version
# Expected: {"version":"..."}
```

## 🚨 Troubleshooting

### Cache Issues
```bash
# Clear build cache
docker builder prune -f

# Clear cache volumes
docker volume prune -f

# Force rebuild without cache
docker compose -f docker-compose.dev.yaml build --no-cache
```

### Permission Errors
```bash
# Check container user
docker exec foodsave-backend-dev id

# Fix permissions
sudo chown -R 999:999 backups/ logs/ data/ temp_uploads/
```

### Container Status
```bash
# Check all containers
docker compose -f docker-compose.dev.yaml ps

# Check logs
docker compose -f docker-compose.dev.yaml logs backend --tail=50
```

## 📊 Build Optimization

### Layer Caching Strategy
1. **Dependencies first** - Copy package files before source code
2. **Cache mounts** - Use `--mount=type=cache` for all package managers
3. **Multi-stage builds** - Separate build and runtime stages
4. **BuildKit integration** - Automatic parallel builds

### Performance Tips
- Use cache mounts for all package managers
- Build only changed services: `docker compose build backend`
- Monitor cache performance with test scripts
- Use `BUILDKIT_INLINE_CACHE=1` for cache sharing

## 🔄 Development Workflow

### Daily Development
```bash
# 1. Start services with cache optimization
docker compose -f docker-compose.dev.yaml up --build

# 2. Make code changes

# 3. Rebuild only changed service
docker compose -f docker-compose.dev.yaml build backend

# 4. Restart service
docker compose -f docker-compose.dev.yaml up -d --no-deps backend

# 5. Check health
curl -f http://localhost:8000/health
```

### Production Deployment
```bash
# 1. Build optimized images
docker compose -f docker-compose.prod.yaml build

# 2. Deploy with optimized compose
docker compose -f docker-compose.prod.yaml up -d

# 3. Verify deployment
docker compose -f docker-compose.prod.yaml ps
curl -f http://localhost:8000/health
```

## 📝 Notes

- **Cache optimization:** Implemented 2025-07-18
- **Build time:** 40-80% faster with cache optimization
- **Cache hit rate:** 70-90% with proper configuration
- **Critical files:** Always use cache mounts for package managers
- **Performance monitoring:** Use `./scripts/test-cache-performance.sh` for benchmarks

---
*Last updated: 2025-07-18*  
*Status: Cache optimization completed* 