# 🖥️ FoodSave AI - GUI Refactor Guide

> **Nowoczesna aplikacja webowa z glassmorphism design i integracją z backendem**

---

## 🎯 Przegląd

FoodSave AI GUI Refactor to nowoczesna aplikacja webowa zapewniająca:
- 🎨 **Glassmorphism design** z efektami przezroczystego szkła
- 💬 **Chat-centered interface** z centralnym asystentem AI
- 🤖 **Integracja z backendem** FoodSave AI
- 📱 **Responsive design** dla wszystkich urządzeń
- 🌙 **Dark/Light mode** z automatycznym przełączaniem

---

## 🚀 Szybki Start

### **Wymagania**
- **Backend FoodSave AI** uruchomiony na localhost:8000
- **Python 3** lub **Node.js** (do serwera HTTP)
- **Przeglądarka internetowa** (Chrome, Firefox, Safari, Edge)

### **Uruchomienie**
```bash
# Użyj dedykowanego skryptu (ZALECANE)
./scripts/gui_refactor.sh

# Lub ręcznie
cd gui_refactor/
python3 -m http.server 8080
# Następnie otwórz http://localhost:8080
```

---

## 🎛️ Tryby Uruchomienia

### **1. Development Mode (Zalecany)**
```bash
./scripts/gui_refactor.sh
```
- ✅ Automatyczne sprawdzanie backendu
- ✅ Serwer HTTP na porcie 8080
- ✅ Hot reload przy zmianach plików

### **2. Custom Port**
```bash
./scripts/gui_refactor.sh -p 3000
```
- ✅ Uruchom na porcie 3000
- ✅ Sprawdź status backendu: `./scripts/gui_refactor.sh -b`

### **3. Manual Server**
```bash
cd gui_refactor/
python3 -m http.server 8080
# Lub z Node.js
npx http-server -p 8080
```

---

## 🖼️ Funkcjonalności GUI

### **Główne Elementy Interfejsu**

#### **Header**
- 🤖 **Logo FoodSave AI** z gradientem
- 🟢 **Status połączenia** z backendem (real-time)
- ☀️/🌙 **Theme toggle** (dark/light mode)

#### **Chat Section (60%)**
- 💬 **Historia wiadomości** z avatarem i timestampami
- 📝 **Input area** z wyślij przyciskiem
- ⏳ **Typing indicator** podczas przetwarzania
- 🎯 **Quick suggestions** - szybkie akcje

#### **Agents Sidebar (40%)**
- 🤖 **Karty agentów** z statystykami:
  - 🍽️ **Agent Żywnościowy** - zarządzanie produktami
  - 🛒 **Agent Zakupowy** - lista zakupów
  - 👤 **Asystent Osobisty** - zadania i przypomnienia
  - 📅 **Agent Kalendarza** - zarządzanie terminami
  - 📧 **Agent Mailowy** - korespondencja

---

## 🔧 Konfiguracja i Personalizacja

### **Backend Connection**
Aplikacja automatycznie łączy się z backendem na:
- **URL**: `http://localhost:8000`
- **Health Check**: `/health` endpoint
- **Chat API**: `/api/agents/execute`

### **Zmiana URL Backendu**
W `gui_refactor/app.js` znajdź:
```javascript
this.backendUrl = 'http://localhost:8000';
```

### **Dodawanie Nowych Agentów**
W `gui_refactor/app.js` w sekcji `agents`:
```javascript
{
    id: "new_agent",
    name: "Nowy Agent",
    icon: "🎯",
    description: "Opis funkcji",
    status: "active",
    data: {
        tasks: 0,
        completed: 0
    }
}
```

---

## 🎨 Design System

### **Kolory**
- **Primary**: `#6366f1` (Indigo)
- **Secondary**: `#8b5cf6` (Purple)
- **Success**: `#10b981` (Green)
- **Warning**: `#f59e0b` (Amber)
- **Error**: `#ef4444` (Red)

### **Glassmorphism Effects**
- **Background**: `rgba(255, 255, 255, 0.05)`
- **Border**: `rgba(255, 255, 255, 0.1)`
- **Backdrop Filter**: `blur(20px)`
- **Shadow**: `0 8px 32px rgba(0, 0, 0, 0.3)`

### **Typography**
- **Font Family**: Inter, system-ui, sans-serif
- **Weights**: 300, 400, 500, 600, 700
- **Sizes**: 12px, 14px, 16px, 18px, 24px

---

## 🔄 Komunikacja z Backend

### **API Endpoints Używane**
```javascript
// Health check
GET /health

// Chat z agentami  
POST /api/agents/execute
{
  "task": "user message",
  "session_id": "gui-refactor-session", 
  "usePerplexity": true,
  "useBielik": false,
  "agent_states": {}
}
```

### **Error Handling**
- ❌ **Connection errors** - Fallback do lokalnych odpowiedzi
- ❌ **API errors** - Wyświetlanie błędów w konsoli
- ❌ **Network issues** - Graceful degradation

---

## 🛠️ Development

### **Struktura Projektu**
```
gui_refactor/
├── index.html          # Główna struktura aplikacji
├── style.css           # Glassmorphism styles
├── app.js              # Logika aplikacji i API
└── README-redesign.md  # Dokumentacja designu
```

### **Dodawanie Nowych Funkcji**

#### **JavaScript**
- Edytuj `app.js` dla logiki aplikacji
- Dodaj nowe metody do klasy `FoodSaveAI`
- Użyj `fetch()` dla komunikacji z backendem

#### **Styling**
- Edytuj `style.css` dla nowych komponentów
- Zachowaj glassmorphism theme
- Użyj CSS custom properties dla kolorów

### **Building i Testing**
```bash
# Development z hot reload
./scripts/gui_refactor.sh

# Test backend connection
./scripts/gui_refactor.sh -b

# Manual testing
curl http://localhost:8000/health
```

---

## 🚦 Troubleshooting

### **Backend Connection Issues**
1. ✅ Sprawdź czy backend działa: `curl http://localhost:8000/health`
2. ✅ Uruchom backend: `./scripts/main/foodsave-all.sh`
3. ✅ Sprawdź CORS settings w backend

### **GUI Not Loading**
```bash
# Sprawdź port
lsof -i :8080

# Uruchom na innym porcie
./scripts/gui_refactor.sh -p 3000
```

### **Development Issues**
```bash
# Clear browser cache
Ctrl+Shift+R (hard refresh)

# Check browser console
F12 → Console tab

# Test API manually
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"test","session_id":"test"}'
```

---

## 🔮 Roadmap

### **Planowane Funkcje**
- 📄 **File upload** - przesyłanie paragonów
- 🔔 **Real-time notifications** - powiadomienia o statusie
- 💾 **Local storage** - zapisywanie ustawień
- 🎙️ **Voice input** - głosowe wiadomości
- 📊 **Analytics dashboard** - szczegółowe statystyki

### **Performance Optimizations**
- ⚡ **Service Worker** - offline capabilities
- 🗂️ **Virtual scrolling** - dla długich czatów
- 📦 **Code splitting** - lepsze ładowanie
- 🎯 **Progressive Web App** - instalacja jako aplikacja

---

## 📚 Dodatkowe Zasoby

- **[Glassmorphism Design](https://glassmorphism.com/)** - Glassmorphism guide
- **[Modern CSS](https://developer.mozilla.org/en-US/docs/Web/CSS)** - CSS documentation
- **[Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)** - HTTP requests
- **[FoodSave AI Backend](../../../docs/core/API_REFERENCE.md)** - API documentation

---

*Wygenerowane automatycznie dla GUI Refactor - Lipiec 2025* 