# 🛡️ Anti-Hallucination System Guide

## 📋 Spis treści

1. [Przegląd systemu](#przegląd-systemu)
2. [Specjalizowane walidatory](#specjalizowane-walidatory)
3. [Konfiguracja agentów](#konfiguracja-agentów)
4. [Dekoratory](#dekoratory)
5. [Metryki i monitoring](#metryki-i-monitoring)
6. [Przykłady użycia](#przykłady-użycia)
7. [Optymalizacje](#optymalizacje)

---

## 🎯 Przegląd systemu

System anti-hallucination w FoodSave AI został zoptymalizowany z wykorzystaniem **specjalizowanych walidatorów** dla różnych typów agentów. Każdy agent ma dedykowany walidator dostosowany do jego specyficznych wymagań.

### 🏗️ Architektura

```
OptimizedAntiHallucinationSystem
├── SpecializedValidators
│   ├── ChefValidator (STRICT)
│   ├── ReceiptAnalysisValidator (STRICT)
│   ├── WeatherValidator (LENIENT)
│   ├── SearchValidator (MODERATE)
│   └── DefaultValidator (MODERATE)
├── AgentSpecificConfig
│   ├── Validation levels
│   ├── Thresholds
│   └── Patterns
└── OptimizedCache
    ├── Agent-specific TTL
    └── Performance metrics
```

---

## 🔧 Specjalizowane walidatory

### ChefValidator
**Poziom:** STRICT  
**Specjalizacja:** Walidacja składników i przepisów

```python
from backend.core.specialized_validators import ChefValidator

validator = ChefValidator()
result = await validator.validate(
    response="Dodaj 500g makaronu i 2 pomidory",
    context="Przepis na spaghetti",
    validation_level=ValidationLevel.STRICT,
    available_ingredients=["makaron", "pomidory", "cebula"]
)
```

**Wzorce:**
- Składniki z miarami: `\b\d+\s*(g|kg|ml|l|łyżk[ai])\s+[a-zA-Ząćęłńóśźż]+\b`
- Nierzeczywiste miary: `\b\d{4,}\s*gram\b`
- Temperatury: `\b\d{3,}\s*stopni\b`

### ReceiptAnalysisValidator
**Poziom:** STRICT  
**Specjalizacja:** Walidacja danych paragonów

```python
from backend.core.specialized_validators import ReceiptAnalysisValidator

validator = ReceiptAnalysisValidator()
result = await validator.validate(
    response="Paragon z 15.01.2024, kwota 45.67 zł",
    context="Analiza paragonu",
    validation_level=ValidationLevel.STRICT
)
```

**Wzorce:**
- Ceny: `\b\d+[,.]\d{2}\s*zł\b`
- Daty: `\b\d{1,2}\.\d{1,2}\.\d{4}\b`
- NIP: `\b\d{3}-\d{3}-\d{2}-\d{2}\b`

### WeatherValidator
**Poziom:** LENIENT  
**Specjalizacja:** Walidacja danych pogodowych

```python
from backend.core.specialized_validators import WeatherValidator

validator = WeatherValidator()
result = await validator.validate(
    response="Temperatura 22°C, wilgotność 65%",
    context="Pogoda w Warszawie",
    validation_level=ValidationLevel.LENIENT
)
```

**Wzorce:**
- Temperatury: `\b\d+\s*stopni\b`
- Wilgotność: `\b\d+\s*%\b`
- Wiatr: `\b\d+\s*km/h\b`

### SearchValidator
**Poziom:** MODERATE  
**Specjalizacja:** Walidacja wyników wyszukiwania

```python
from backend.core.specialized_validators import SearchValidator

validator = SearchValidator()
result = await validator.validate(
    response="Według źródeł z 2024 roku...",
    context="Wyszukiwanie informacji",
    validation_level=ValidationLevel.MODERATE
)
```

**Wzorce:**
- Niezweryfikowane twierdzenia: `\b(na pewno|zdecydowanie|bez wątpienia)\b`
- Fakty bez źródeł: `\b\d{4}\s*rok[iu]?\b`

---

## ⚙️ Konfiguracja agentów

### Agent-specific konfiguracje

```python
from backend.core.agent_specific_config import get_agent_config

# Pobierz konfigurację dla ChefAgent
chef_config = get_agent_config("chef")
print(f"Confidence threshold: {chef_config.confidence_threshold}")
print(f"Hallucination threshold: {chef_config.hallucination_threshold}")
print(f"Validation level: {chef_config.validation_level}")
```

### Dostępne konfiguracje

| Agent Type | Validation Level | Confidence Threshold | Hallucination Threshold |
|------------|------------------|---------------------|------------------------|
| **chef** | STRICT | 0.7 | 0.3 |
| **receipt_analysis** | STRICT | 0.8 | 0.2 |
| **weather** | LENIENT | 0.5 | 0.4 |
| **search** | MODERATE | 0.7 | 0.3 |
| **analytics** | MODERATE | 0.75 | 0.25 |
| **meal_planner** | MODERATE | 0.7 | 0.3 |
| **general_conversation** | LENIENT | 0.5 | 0.5 |

---

## 🎨 Dekoratory

### Podstawowy dekorator

```python
from backend.core.anti_hallucination_decorator_optimized import (
    with_optimized_anti_hallucination,
    OptimizedAntiHallucinationConfig
)

class ChefAgent(BaseAgent):
    @with_optimized_anti_hallucination(
        OptimizedAntiHallucinationConfig(
            validation_level=ValidationLevel.STRICT,
            log_validation=True,
            raise_on_high_hallucination=True
        )
    )
    async def generate_recipe(self, input_data: dict) -> AgentResponse:
        # Logika generowania przepisu
        return AgentResponse(...)
```

### Specjalizowane dekoratory

```python
from backend.core.anti_hallucination_decorator_optimized import (
    with_chef_validation,
    with_receipt_validation,
    with_weather_validation,
    with_search_validation,
    with_general_validation
)

class ChefAgent(BaseAgent):
    @with_chef_validation(
        available_ingredients=["makaron", "pomidory", "cebula"],
        validation_level=ValidationLevel.STRICT
    )
    async def generate_recipe(self, input_data: dict) -> AgentResponse:
        return AgentResponse(...)

class ReceiptAnalysisAgent(BaseAgent):
    @with_receipt_validation(validation_level=ValidationLevel.STRICT)
    async def analyze_receipt(self, input_data: dict) -> AgentResponse:
        return AgentResponse(...)

class WeatherAgent(BaseAgent):
    @with_weather_validation(validation_level=ValidationLevel.LENIENT)
    async def get_weather(self, input_data: dict) -> AgentResponse:
        return AgentResponse(...)

class SearchAgent(BaseAgent):
    @with_search_validation(validation_level=ValidationLevel.MODERATE)
    async def search_information(self, input_data: dict) -> AgentResponse:
        return AgentResponse(...)
```

### Automatyczna detekcja agenta

```python
from backend.core.anti_hallucination_decorator_optimized import (
    with_agent_specific_validation
)

class MyAgent(BaseAgent):
    @with_agent_specific_validation()  # Automatyczna detekcja
    async def process(self, input_data: dict) -> AgentResponse:
        return AgentResponse(...)
```

---

## 📊 Metryki i monitoring

### Pobieranie metryk

```python
from backend.core.anti_hallucination_system_optimized import (
    optimized_anti_hallucination_system
)

# Pobierz ogólne metryki
metrics = optimized_anti_hallucination_system.get_metrics()
print(f"Total validations: {metrics['total_validations']}")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.2f}")
print(f"Average validation time: {metrics['avg_validation_time']:.3f}s")

# Pobierz metryki dla konkretnego agenta
agent_metrics = metrics['agent_metrics']['ChefAgent']
print(f"ChefAgent success rate: {agent_metrics['successful_validations'] / agent_metrics['total_validations']:.2f}")
```

### Statystyki cache

```python
cache_stats = optimized_anti_hallucination_system.get_cache_stats()
print(f"Cache size: {cache_stats['cache_size']}")
print(f"Cache hits: {cache_stats['cache_hits']}")
print(f"Cache misses: {cache_stats['cache_misses']}")
```

---

## 💡 Przykłady użycia

### 1. ChefAgent z walidacją składników

```python
from backend.core.anti_hallucination_decorator_optimized import with_chef_validation

class ChefAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ChefAgent")
        self.pantry_items = ["makaron", "pomidory", "cebula", "czosnek", "olej"]

    @with_chef_validation(
        available_ingredients=lambda self, *args, **kwargs: self.pantry_items
    )
    async def generate_recipe(self, input_data: dict) -> AgentResponse:
        # Logika generowania przepisu
        recipe_text = "Dodaj 300g makaronu, 2 pomidory i 1 cebulę..."
        
        return AgentResponse(
            success=True,
            text=recipe_text,
            confidence=0.9
        )
```

### 2. ReceiptAnalysisAgent z walidacją danych

```python
from backend.core.anti_hallucination_decorator_optimized import with_receipt_validation

class ReceiptAnalysisAgent(BaseAgent):
    @with_receipt_validation(validation_level=ValidationLevel.STRICT)
    async def analyze_receipt(self, input_data: dict) -> AgentResponse:
        # Logika analizy paragonu
        analysis_text = "Paragon z 15.01.2024, kwota 45.67 zł, NIP: 123-456-78-90"
        
        return AgentResponse(
            success=True,
            text=analysis_text,
            confidence=0.95
        )
```

### 3. WeatherAgent z lenientną walidacją

```python
from backend.core.anti_hallucination_decorator_optimized import with_weather_validation

class WeatherAgent(BaseAgent):
    @with_weather_validation(validation_level=ValidationLevel.LENIENT)
    async def get_weather(self, input_data: dict) -> AgentResponse:
        # Logika pobierania pogody
        weather_text = "Temperatura 22°C, wilgotność 65%, wiatr 15 km/h"
        
        return AgentResponse(
            success=True,
            text=weather_text,
            confidence=0.8
        )
```

---

## 🚀 Optymalizacje

### 1. Cache z agent-specific TTL

```python
# Każdy agent ma własny TTL cache
chef_config = get_agent_config("chef")
cache_ttl_minutes = chef_config.timeout_seconds / 60  # 15 minut

weather_config = get_agent_config("weather")
cache_ttl_minutes = weather_config.timeout_seconds / 60  # 8 minut
```

### 2. Równoległa walidacja

```python
# Walidatory wykonują się równolegle
async def validate_all(self, response, context, agent_name, validation_level):
    tasks = [
        self._validate_patterns(response),
        self._validate_context(response, context),
        self._validate_ingredients(response, available_ingredients),
        self._validate_measurements(response)
    ]
    results = await asyncio.gather(*tasks)
```

### 3. Adaptacyjne progi

```python
# Progi dostosowane do typu agenta
if agent_type == "chef":
    confidence_threshold = 0.7
    hallucination_threshold = 0.3
elif agent_type == "weather":
    confidence_threshold = 0.5
    hallucination_threshold = 0.4
```

---

## 📈 Oczekiwane korzyści

| Metryka | Przed optymalizacją | Po optymalizacji | Poprawa |
|---------|---------------------|-------------------|---------|
| **Dokładność ChefAgent** | 75% | 95% | +20% |
| **Dokładność ReceiptAnalysis** | 80% | 98% | +18% |
| **Dokładność WeatherAgent** | 60% | 85% | +25% |
| **Czas walidacji** | 100ms | 50ms | -50% |
| **False positives** | 15% | 3% | -80% |
| **Cache hit rate** | 30% | 70% | +40% |

---

## 🔧 Rozszerzanie systemu

### Dodawanie nowego walidatora

```python
from backend.core.specialized_validators import SpecializedValidator

class CustomValidator(SpecializedValidator):
    def __init__(self):
        self.custom_patterns = {
            HallucinationType.FACTUAL_ERROR: [
                r"\b\d{4}\s*rok\b",
            ],
        }
    
    async def validate(self, response, context, validation_level, **kwargs):
        # Implementacja walidacji
        pass
    
    def get_validation_patterns(self):
        return self.custom_patterns
    
    def get_confidence_threshold(self):
        return 0.7
    
    def get_hallucination_threshold(self):
        return 0.3

# Rejestracja walidatora
from backend.core.specialized_validators import ValidatorFactory
ValidatorFactory.register_validator("custom", CustomValidator)
```

### Dodawanie nowej konfiguracji agenta

```python
from backend.core.agent_specific_config import register_agent_config, AgentValidationConfig

custom_config = AgentValidationConfig(
    validation_level=ValidationLevel.MODERATE,
    confidence_threshold=0.7,
    hallucination_threshold=0.3,
    enabled_patterns=["factual"],
    custom_patterns={},
    timeout_seconds=10.0,
    cache_enabled=True,
    log_validation=True,
    raise_on_high_hallucination=False,
    high_hallucination_threshold=0.8,
)

register_agent_config("custom_agent", custom_config)
```

---

## 📝 Podsumowanie

Zoptymalizowany system anti-hallucination zapewnia:

✅ **Specjalizowane walidatory** - każdy agent ma dedykowany walidator  
✅ **Agent-specific konfiguracje** - specyficzne progi i wzorce  
✅ **Zoptymalizowany cache** - agent-specific TTL  
✅ **Lepsze metryki** - szczegółowe statystyki wydajności  
✅ **Łatwe rozszerzanie** - modularna architektura  
✅ **Wsteczna kompatybilność** - istniejące agenty działają bez zmian  

System jest teraz bardziej efektywny, dokładny i łatwiejszy w utrzymaniu. 