# Health Check Configuration Guide

## 🔧 Zapamiętane ustawienia Health Check

### Problem
Kontenery Docker były oznaczone jako "unhealthy" z powodu błędnej konfiguracji health check.

### Rozwiązanie

#### 1. **Ujednolicenie endpointów (2025-06-30)**
Wszystkie health check używają teraz endpointu `/health`:
- ✅ **Docker health check**: `/health`
- ✅ **Skrypt `food`**: `/health` 
- ✅ **Skrypt `start_foodsave_ai`**: `/health`
- ✅ **Dokumentacja**: `/health`

**Uwaga**: Endpoint `/monitoring/health` nadal istnieje dla zaawansowanego monitoringu, ale nie jest używany w health check.

#### 2. **Dockerfile Frontend (myappassistant-chat-frontend/Dockerfile.prod)**

```dockerfile
# Use the official Node.js runtime as the base image
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat curl
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
# Use cache mount for npm to speed up builds
RUN --mount=type=cache,target=/root/.npm \
    npm ci --legacy-peer-deps

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED 1

# Use cache mount for npm during build
RUN --mount=type=cache,target=/root/.npm \
    npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
# Uncomment the following line in case you want to disable telemetry during runtime.
ENV NEXT_TELEMETRY_DISABLED 1

# Combine user creation commands to reduce layers
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Install curl for health checks
RUN apk add --no-cache curl

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache and create .next directory in one layer
RUN mkdir .next && \
    chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
# set hostname to localhost
ENV HOSTNAME "0.0.0.0"

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/next-config-js/output
CMD ["node", "server.js"]
```

#### 2. **Docker Compose Health Checks (docker-compose.yml)**

**Backend:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Frontend:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Celery Worker & Beat:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://backend:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 3. **Kluczowe zasady:**

- **Kontenery bezpośrednio eksponujące porty** → używają `localhost:PORT`
- **Kontenery wewnętrzne** → używają nazwy serwisu `backend:8000`
- **Frontend wymaga curl** → musi być zainstalowany w Dockerfile
- **Backend ma endpoint `/health`** → zwraca `{"status": "healthy", "timestamp": "..."}`

### 4. **Komendy do restartu:**

```bash
# Zatrzymanie
docker compose down

# Przebudowanie i uruchomienie
docker compose up --build -d

# Sprawdzenie statusu
docker ps
```

### 5. **Sprawdzenie health check:**

```bash
# Sprawdzenie endpointu backend
curl -f http://localhost:8000/health

# Sprawdzenie frontendu
curl -f http://localhost:3000

# Sprawdzenie z wnętrza kontenera Celery
docker exec aiasisstmarubo-celery_worker-1 curl -f http://backend:8000/health
```

### 6. **Oczekiwany status:**

Po prawidłowej konfiguracji wszystkie kontenery powinny mieć status:
- ✅ **Backend**: healthy
- ✅ **Frontend**: healthy  
- ✅ **Celery Worker**: healthy
- ✅ **Celery Beat**: healthy
- ✅ **SQLite**: healthy
- ✅ **Redis**: healthy
- ✅ **Ollama**: running (bez health check)

### 7. **Rozwiązywanie problemów:**

1. **Kontener unhealthy** → sprawdź logi: `docker logs <container_name>`
2. **Brak curl** → dodaj do Dockerfile: `RUN apk add --no-cache curl`
3. **Błędny adres** → sprawdź czy używany jest `localhost` czy nazwa serwisu
4. **Timeout** → zwiększ `timeout` w health check

---

**Data utworzenia:** 2025-06-30  
**Ostatnia aktualizacja:** 2025-06-30  
**Status:** ✅ Działające 