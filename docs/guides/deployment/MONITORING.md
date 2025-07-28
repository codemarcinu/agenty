# Monitoring i Telemetria - FoodSave AI

## Wprowadzenie

System monitoringu i telemetrii w FoodSave AI zapewnia kompleksowy wgląd w działanie aplikacji, umożliwiając śledzenie wydajności, diagnozowanie problemów i optymalizację zasobów. Implementacja opiera się na standardach OpenTelemetry i wykorzystuje popularne narzędzia open-source.

## Komponenty Systemu

### 1. **OpenTelemetry**

OpenTelemetry służy jako podstawa systemu telemetrii, zapewniając:
- Distributed tracing
- Metryki wydajności
- Logowanie zdarzeń
- Instrumentację automatyczną dla popularnych bibliotek

#### Zaimplementowane pakiety:
- `opentelemetry-api` - API dla instrumentacji kodu
- `opentelemetry-sdk` - Implementacja SDK
- `opentelemetry-instrumentation-fastapi` - Automatyczna instrumentacja FastAPI
- `opentelemetry-instrumentation-sqlalchemy` - Instrumentacja SQLAlchemy dla baz danych
- `opentelemetry-instrumentation-httpx` - Instrumentacja klienta HTTP
- `opentelemetry-exporter-jaeger` - Eksporter do systemu Jaeger
- `prometheus-client` - Klient Prometheus dla metryk
- `prometheus-fastapi-instrumentator` - Instrumentacja FastAPI dla Prometheus

### 2. **Prometheus**

Prometheus służy do zbierania i przechowywania metryk z różnych komponentów systemu:
- Metryki wydajności aplikacji
- Metryki zasobów systemowych (CPU, pamięć, dysk)
- Metryki niestandardowe specyficzne dla aplikacji
- Alerty oparte na progach

### 3. **Grafana**

Grafana zapewnia wizualizację danych monitoringu:
- Dashboardy dla różnych aspektów systemu
- Wykresy metryk w czasie rzeczywistym
- Wizualizacja logów (Loki)
- Alerty i powiadomienia

#### Dashboardy

- **FoodSave AI Dashboard** – ogólne metryki systemu (Prometheus)
- **Chat Interactions Dashboard** – aktywność czatu, logi backend/frontend (Loki)

Dashboardy są automatycznie ładowane z katalogu `monitoring/grafana/dashboards`.

#### Przeglądanie logów (Loki)

1. Wejdź do Grafany: [http://localhost:3001](http://localhost:3001) (admin/admin)
2. W menu „Explore” wybierz źródło danych **Loki**
3. Przykładowe zapytania:
   - `{job="backend_logs"}` – logi backendu
   - `{job="frontend_logs"}` – logi frontendu
   - `{job="redis_logs"}` – logi Redis
   - `{job="postgres_logs"}` – logi PostgreSQL
   - `{job="ollama_logs"}` – logi Ollama
4. Możesz filtrować po poziomie logu, usłudze, tagu itp.

#### Przykładowy dashboard logów:
- **Chat Interactions Dashboard** – wizualizuje liczbę interakcji czatu na backendzie i frontendzie, pozwala analizować trendy i błędy.

### 4. **Loki**

Loki to system agregacji logów, który:
- Zbiera logi z różnych komponentów
- Umożliwia wyszukiwanie i filtrowanie logów
- Integruje się z Grafaną dla wizualizacji
- Zapewnia długoterminowe przechowywanie logów

#### Konfiguracja Loki:

Loki wymaga specjalnej konfiguracji, aby działać poprawnie:

```yaml
loki:
  image: grafana/loki:latest
  container_name: foodsave-loki-dev
  volumes:
    - ./monitoring/loki-config.yaml:/etc/loki/local-config.yaml
    - loki_data:/loki
```

### 5. **Promtail**

Promtail to agent zbierający logi dla Loki:
- Śledzi pliki logów
- Przesyła logi do Loki
- Dodaje etykiety i metadane
- Obsługuje różne formaty logów (JSON, syslog, itp.)

## Konfiguracja i Uruchomienie

### Uruchamianie systemu monitoringu:

```bash
docker compose -f docker-compose.dev.yaml up -d loki promtail grafana prometheus
```

### Dostęp do interfejsów:

- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

## Dashboardy

Dashboardy są automatycznie provisionowane z katalogu `monitoring/grafana/dashboards`.

- **FoodSave AI Dashboard** – metryki Prometheus
- **Chat Interactions Dashboard** – logi i aktywność czatu (Loki)

## Rozwiązywanie problemów

### Problemy z uprawnieniami Loki

Jeśli w logach Loki pojawiają się błędy typu:

```
level=error ts=... msg="failed to flush" err="failed to flush chunks: ... permission denied"
```

Rozwiązania:
1. Użyj nazwanego wolumenu Docker zamiast montowania lokalnego katalogu
2. Upewnij się, że katalog docelowy ma odpowiednie uprawnienia

### Problemy z siecią Docker

Jeśli występują konflikty sieci:

```
failed to create network ...: Error response from daemon: invalid pool request: Pool overlaps with other one on this address space
```

Rozwiązania:
1. Usuń definicję sieci z pliku docker-compose.yaml i pozwól Docker Compose utworzyć ją automatycznie
2. Zatrzymaj wszystkie kontenery i sieci przed ponownym uruchomieniem
3. Użyj `docker network prune` aby usunąć nieużywane sieci

## Dobre praktyki

1. Regularnie monitoruj dashboardy Grafana
2. Ustaw alerty dla kluczowych metryk
3. Analizuj logi w przypadku problemów
4. Utrzymuj odpowiednią retencję danych
5. Twórz kopie zapasowe konfiguracji dashboardów

## Przyszły rozwój

- Implementacja distributed tracingu z Jaeger
- Rozszerzenie metryk specyficznych dla aplikacji
- Automatyczne alerty przez email/Slack
- Integracja z systemami CI/CD
