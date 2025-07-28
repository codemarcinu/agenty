# System Monitorowania Jakości Kodu - MyAssistant/FoodSave AI

## 📋 Przegląd

Ten dokument opisuje kompleksowy system monitorowania jakości kodu dla projektu MyAssistant/FoodSave AI, zaimplementowany zgodnie z `.cursorrules` i najlepszymi praktykami z 2025 roku.

## 🎯 Cele Systemu

### Główne Cele
- **Proaktywne wykrywanie problemów** przed deploymentem
- **Utrzymanie standardów kodowania** zgodnie z `.cursorrules`
- **Zapewnienie bezpieczeństwa aplikacji** poprzez automatyczne skanowanie
- **Automatyzacja quality gates** w CI/CD pipeline
- **Śledzenie metryk jakości** w czasie rzeczywistym

### Metryki Jakości (Quality Gates)
- **Pokrycie testami**: ≥ 80% linii, ≥ 70% branchy
- **Code Smells**: ≤ 0.5 na KLOC
- **Reliability Rating**: ≤ B
- **Security Rating**: ≤ B
- **Maintainability Rating**: ≤ B
- **Duplicated Lines**: ≤ 3%
- **Technical Debt Ratio**: ≤ 5%

## 🛠️ Narzędzia i Konfiguracja

### 1. SonarQube (Główne Narzędzie)

**Konfiguracja**: `sonar-project.properties`
```properties
sonar.projectKey=myassistant-foodsave-ai
sonar.projectName=MyAssistant/FoodSave AI
sonar.sources=src/
sonar.tests=tests/
sonar.coverage.minimum=80
sonar.qualitygate.wait=true
```

**Docker Compose**: Dodano serwis SonarQube
```yaml
sonarqube:
  image: sonarqube:10.4-community
  ports:
    - "9000:9000"
  environment:
    - SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true
```

### 2. Python - Narzędzia Jakości

#### Ruff (Główny Linter)
**Konfiguracja**: `ruff.toml`
- Zastępuje flake8, isort, black
- Ultraszybki (napisany w Rust)
- Automatyczne naprawy

```bash
# Sprawdzenie
poetry run ruff check .

# Formatowanie
poetry run ruff format .

# Naprawa automatyczna
poetry run ruff check . --fix
```

#### MyPy (Type Checking)
**Konfiguracja**: `mypy.ini`
- Ścisłe sprawdzanie typów
- Integracja z Pydantic v2
- Raporty JSON dla CI/CD

```bash
poetry run mypy src/ --json-report mypy-report.json
```

#### Bandit (Bezpieczeństwo)
**Konfiguracja**: `bandit.yaml`
- Wykrywanie podatności bezpieczeństwa
- Analiza potencjalnych zagrożeń
- Raporty JSON

```bash
poetry run bandit -r src/ -f json -o bandit-report.json
```

#### Pytest (Testy + Coverage)
**Konfiguracja**: `pyproject.toml`
- Pokrycie testami ≥ 80%
- Raporty XML dla SonarQube
- Integracja z coverage.py

```bash
poetry run pytest tests/ --cov=src/ --cov-report=xml --cov-fail-under=80
```

### 3. Frontend - Narzędzia Jakości

#### ESLint
**Konfiguracja**: `myappassistant-chat-frontend/.eslintrc.json`
- Ścisłe reguły TypeScript
- React Hooks rules
- Integracja z Next.js

```bash
npm run lint
npm run lint:fix
```

#### TypeScript
**Konfiguracja**: `tsconfig.json`
- Strict mode enabled
- Sprawdzanie typów bez emisji

```bash
npm run type-check
```

#### Jest + Testing Library
**Konfiguracja**: `jest.config.js`
- Testy jednostkowe
- Pokrycie kodu
- Integracja z React Testing Library

```bash
npm run test:ci
```

### 4. Pre-commit Hooks

**Konfiguracja**: `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.1
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**Plik**: `.github/workflows/code-quality.yml`

#### Etapy Pipeline:
1. **Python Quality Analysis**
   - Ruff linting
   - MyPy type checking
   - Bandit security analysis
   - Pytest with coverage

2. **SonarQube Analysis**
   - Statyczna analiza kodu
   - Quality gate check
   - Security hotspots analysis

3. **Frontend Quality Analysis**
   - ESLint
   - TypeScript check
   - Jest tests
   - Build verification

4. **Security Analysis**
   - Trivy vulnerability scanner
   - pip-audit
   - npm audit

5. **Quality Gate Check**
   - Final validation
   - Summary report

### Konfiguracja Secrets
```bash
SONAR_TOKEN=your_sonar_token
SONAR_HOST_URL=http://localhost:9000
```

## 📊 Monitoring i Raporty

### 1. Lokalne Sprawdzanie Jakości

**Skrypt**: `scripts/quality-check.sh`
```bash
# Uruchomienie pełnej analizy
./scripts/quality-check.sh

# Wyniki:
# - ruff-report.json
# - mypy-report.json
# - bandit-report.json
# - coverage-report.json
# - quality-report-YYYYMMDD_HHMMSS.md
```

### 2. Metryki do Śledzenia

#### Cykliczne Kompleksowości
- **Funkcje**: ≤ 10
- **Klasy**: ≤ 20
- **Moduły**: ≤ 50

#### Pokrycie Testami
- **Linie kodu**: ≥ 80%
- **Branchy**: ≥ 70%
- **Funkcje**: ≥ 90%

#### Bezpieczeństwo
- **Vulnerabilities**: 0
- **Security Hotspots**: 0
- **Critical Issues**: 0

#### Dług Techniczny
- **Technical Debt Ratio**: ≤ 5%
- **Code Smells**: ≤ 0.5/KLOC
- **Duplicated Lines**: ≤ 3%

### 3. Dashboardy i Raporty

#### SonarQube Dashboard
- **URL**: http://localhost:9000
- **Projekt**: myassistant-foodsave-ai
- **Metryki**: Real-time quality metrics

#### GitHub Actions Artifacts
- **Python Quality Reports**: ruff-report.json, mypy-report.json
- **Security Reports**: bandit-report.json, pip-audit-report.json
- **Coverage Reports**: coverage.xml, htmlcov/

## 🚀 Wdrażanie i Uruchamianie

### 1. Pierwsze Uruchomienie

```bash
# 1. Uruchom SonarQube
docker-compose up -d sonarqube

# 2. Poczekaj na start (60s)
sleep 60

# 3. Sprawdź jakość kodu
./scripts/quality-check.sh

# 4. Skonfiguruj pre-commit hooks
poetry run pre-commit install
```

### 2. Codzienne Użycie

```bash
# Przed commitem (automatyczne)
git add .
git commit -m "feat: add new feature"

# Ręczne sprawdzenie
./scripts/quality-check.sh

# Naprawa problemów
poetry run ruff check . --fix
poetry run ruff format .
```

### 3. CI/CD Pipeline

```bash
# Automatyczne uruchamianie przy:
# - Push do main/develop
# - Pull Request
# - Manual trigger

# Sprawdzenie statusu
gh run list --workflow=code-quality.yml
```

## 🔧 Konfiguracja IDE

### VS Code / Cursor

#### Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.ruff",
    "ms-python.mypy-type-checker",
    "ms-python.black-formatter",
    "ms-vscode.vscode-typescript-next",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "sonarsource.sonarlint-vscode"
  ]
}
```

#### Settings
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "typescript.preferences.includePackageJsonAutoImports": "on",
  "eslint.validate": ["javascript", "typescript", "javascriptreact", "typescriptreact"]
}
```

### SonarLint Integration
- **Plugin**: SonarLint for VS Code
- **Rules**: Synchronizacja z SonarQube
- **Real-time**: Analiza podczas kodowania

## 📈 Continuous Improvement

### 1. Miesięczne Audyty

**Proces**:
1. Analiza trendów jakości
2. Identyfikacja problemów
3. Aktualizacja quality gates
4. Szkolenia zespołu

**Raport**: `docs/quality-log.md`

### 2. Metryki Wydajności

#### Pipeline Performance
- **Build Time**: < 20 min
- **Test Time**: < 10 min
- **Analysis Time**: < 15 min

#### Quality Trends
- **Coverage Trend**: Rosnący
- **Technical Debt**: Malejący
- **Security Issues**: 0

### 3. Automatyzacja

#### Alerty
- **Slack Integration**: Alerty o failed builds
- **Email Notifications**: Weekly quality reports
- **GitHub Issues**: Automatic issue creation

#### Escalation
- **Critical Issues**: Immediate notification
- **Quality Gate Failures**: Block merge
- **Security Vulnerabilities**: Emergency response

## 🛡️ Bezpieczeństwo

### 1. Dependency Scanning
```bash
# Python
poetry run pip-audit

# Node.js
npm audit --audit-level=high

# Docker
trivy fs .
```

### 2. Secret Scanning
- **GitHub Secret Scanning**: Enabled
- **Pre-commit Hooks**: Check for secrets
- **SonarQube**: Security hotspots analysis

### 3. Code Security
- **Bandit**: Python security analysis
- **ESLint Security**: JavaScript security rules
- **SonarQube**: Multi-language security analysis

## 📚 Zasoby i Dokumentacja

### Kluczowe Pliki
- `.cursorrules` - Główne reguły projektu
- `sonar-project.properties` - Konfiguracja SonarQube
- `ruff.toml` - Konfiguracja Ruff
- `.eslintrc.json` - Konfiguracja ESLint
- `.pre-commit-config.yaml` - Pre-commit hooks
- `scripts/quality-check.sh` - Skrypt sprawdzania jakości

### Dokumentacja
- **SonarQube**: https://docs.sonarqube.org/
- **Ruff**: https://docs.astral.sh/ruff/
- **MyPy**: https://mypy.readthedocs.io/
- **ESLint**: https://eslint.org/docs/
- **GitHub Actions**: https://docs.github.com/en/actions

### Wsparcie
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Wiki**: Projekt Wiki
- **Slack**: #code-quality channel

## 🎯 Podsumowanie

System monitorowania jakości kodu MyAssistant/FoodSave AI zapewnia:

✅ **Automatyzację** wszystkich procesów jakości  
✅ **Shift-Left Testing** - wczesne wykrywanie problemów  
✅ **Security-First** - priorytet bezpieczeństwa  
✅ **Continuous Monitoring** - ciągłe śledzenie metryk  
✅ **Quality Gates** - automatyczne blokowanie złej jakości  
✅ **Polish Support** - lokalizacja i specyficzne reguły  

System jest w pełni zgodny z `.cursorrules` i najlepszymi praktykami z 2025 roku, zapewniając wysoką jakość kodu i bezpieczeństwo aplikacji. 