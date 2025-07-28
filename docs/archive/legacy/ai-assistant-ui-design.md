# 🚀 AI Assistant Dashboard - Nowy UI Design

**Data:** 29 czerwca 2025  
**Wersja:** 1.0  
**Projekt:** FoodSave AI - Modernizacja UI

## 📋 Spis treści

1. [Przegląd projektu](#przegląd-projektu)
2. [Analiza istniejącego systemu](#analiza-istniejącego-systemu)
3. [Architektura nowego UI](#architektura-nowego-ui)
4. [Funkcjonalności kluczowe](#funkcjonalności-kluczowe)
5. [Design System](#design-system)
6. [Komponenty interfejsu](#komponenty-interfejsu)
7. [Funkcjonalności zaawansowane](#funkcjonalności-zaawansowane)
8. [Implementacja techniczna](#implementacja-techniczna)
9. [Roadmapa rozwoju](#roadmapa-rozwoju)
10. [Załączniki](#załączniki)

## 🎯 Przegląd projektu

### Cel
Zaprojektowanie nowoczesnego, intuicyjnego interfejsu użytkownika dla aplikacji AI Assistant (FoodSave AI), który będzie głównym punktem interakcji między użytkownikiem a zaawansowanym systemem wieloagentowym AI.

### Główne założenia
- **Dashboard-centric design** - centralną częścią jest okno czatu
- **Material UI aesthetics** - zgodność z najnowszymi wzorcami Material Design
- **Responsywność** - działanie na desktop i mobile
- **Interaktywność** - płynne animacje i feedback użytkownika
- **Dostępność** - zgodność z WCAG 2.1 AA

## 🔍 Analiza istniejącego systemu

### Obecna architektura FoodSave AI
- **Backend:** FastAPI + Python 3.12+
- **Frontend:** React 18 + TypeScript + Next.js
- **AI Engine:** Ollama (lokalny hosting LLM)
- **Baza danych:** SQLite + SQLAlchemy
- **Agenty AI:** 5 wyspecjalizowanych agentów
- **Tauri v2:** Implementacja desktopowa

### Zidentyfikowane potrzeby
1. Centralizacja interakcji poprzez dashboard
2. Uproszczenie dostępu do funkcjonalności agentów
3. Lepsze zarządzanie załącznikami (paragony)
4. Intuicyjny panel ustawień i zarządzania RAG
5. Nowoczesny, responsywny design

## 🏗️ Architektura nowego UI

### Główne sekcje aplikacji

#### 1. **Header** 
- Logo i tytuł aplikacji
- Status agentów AI (5 aktywnych)
- Przełącznik motywu (jasny/ciemny)
- Przycisk ustawień

#### 2. **Sidebar** (nawigacja)
- 🏠 Dashboard (główna)
- 📷 OCR (analiza paragonów)
- 🧊 Pantry (zarządzanie spiżarnią)
- 📊 Analytics (analityka wydatków)
- 📚 RAG Management (baza wiedzy)
- ⚙️ Settings (ustawienia systemowe)

#### 3. **Główny obszar**
- **Okno czatu** (centralne)
- **Panel gotowych komend**
- **Obszar upload załączników**
- **Status bar agentów**

#### 4. **Modalne panele**
- Ustawienia aplikacji
- Zarządzanie bazą RAG
- Szczegóły agentów

## ⚡ Funkcjonalności kluczowe

### Gotowe komendy
1. **🛒 "Zrobiłem zakupy"**
   - Automatyczne uruchomienie OCR
   - Upload i analiza paragonów
   - Aktualizacja spiżarni

2. **🌤️ "Jaka pogoda na dzisiaj i najbliższe 3 dni"**
   - Lokalizacje: Ząbki i Warszawa
   - Szczegółowa prognoza
   - Rekomendacje ubraniowe

3. **🍳 "Co na śniadanie?"**
   - Analiza dostępnych składników
   - 2 propozycje śniadaniowe
   - Uwzględnienie preferencji dietetycznych

4. **🥪 "Co na obiad do pracy?"**
   - Analiza spiżarni na 3 dni
   - 2 warianty na każdy dzień
   - Automatyczna lista zakupów jeśli brak składników

5. **🧊 "Co mam do jedzenia?"**
   - Tabela zawartości spiżarni
   - Daty ważności
   - Kategoryzacja produktów

### Zarządzanie załącznikami
- **Drag & drop** dla paragonów
- **OCR processing** w czasie rzeczywistym
- **Podgląd** przed wysłaniem
- **Obsługa formatów:** JPG, PNG, PDF

## 🎨 Design System

### Kolorystyka
- **Główny gradient:** niebieski (#007AFF) → fioletowy (#5856D6)
- **Akcenty pozytywne:** zielony (#34C759)
- **Akcenty ostrzegawcze:** pomarańczowy (#FF9500)
- **Błędy:** czerwony (#FF3B30)
- **Motywy:** jasny i ciemny

### Typografia
- **Główna:** SF Pro / Inter
- **Rozmiary:** 12px, 14px, 16px, 18px, 24px, 32px
- **Wagi:** Regular (400), Medium (500), Semibold (600)

### Komponenty Material UI
- **Karty** z zaokrąglonymi rogami (16px)
- **Przyciski** z efektami hover i ripple
- **Pola input** z floating labels
- **Snackbars** dla notyfikacji
- **Progress indicators** dla operacji długotrwałych

## 🧩 Komponenty interfejsu

### ChatWindow
```jsx
interface ChatWindowProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  isTyping: boolean
  allowFileUpload: boolean
}
```

### QuickCommands
```jsx
interface QuickCommand {
  id: string
  label: string
  icon: string
  action: string
  description: string
}
```

### AgentStatus
```jsx
interface Agent {
  id: string
  name: string
  status: 'active' | 'idle' | 'error'
  description: string
  color: string
}
```

### FileUploadArea
```jsx
interface FileUploadProps {
  accept: string[]
  maxSize: number
  onUpload: (files: File[]) => void
  preview: boolean
}
```

## ⚙️ Funkcjonalności zaawansowane

### Panel ustawień
- **Modele AI:** wybór i konfiguracja (Gemma3:12b, inne)
- **Prompty systemowe:** edycja i personalizacja
- **API endpoints:** konfiguracja połączeń
- **Backup:** automatyczny i ręczny eksport danych
- **Języki:** wsparcie dla polskiego i angielskiego
- **Notyfikacje:** desktop i push

### Zarządzanie RAG
- **Upload dokumentów:** PDF, DOC, TXT
- **Kategoryzacja:** przepisy, instrukcje, diety
- **Wyszukiwanie semantyczne:** vector search
- **Embedding models:** wybór modelu
- **Indeksowanie:** automatyczne i ręczne
- **Analytics:** statystyki użycia bazy wiedzy

### System promptów
- **Prompt templates:** gotowe szablony
- **Custom prompts:** użytkownika
- **Versioning:** historia zmian
- **A/B testing:** testowanie wariantów
- **Performance metrics:** skuteczność promptów

## 💻 Implementacja techniczna

### Stack technologiczny
- **Frontend:** Next.js 15 + React 18 + TypeScript
- **UI Library:** Material-UI (MUI) v6
- **State Management:** Zustand + TanStack Query
- **Styling:** Emotion + CSS-in-JS
- **Desktop:** Tauri v2
- **Build:** Vite/Turbopack

### Architektura komponentów
```
src/
├── components/
│   ├── chat/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageBubble.tsx
│   │   └── TypingIndicator.tsx
│   ├── dashboard/
│   │   ├── Dashboard.tsx
│   │   ├── QuickCommands.tsx
│   │   └── AgentStatus.tsx
│   ├── common/
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   └── modals/
│       ├── SettingsModal.tsx
│       └── RAGModal.tsx
├── hooks/
│   ├── useChat.ts
│   ├── useAgents.ts
│   └── useSettings.ts
├── stores/
│   ├── chatStore.ts
│   ├── agentStore.ts
│   └── settingsStore.ts
└── types/
    ├── chat.ts
    ├── agents.ts
    └── settings.ts
```

### API Endpoints
- `POST /api/v2/chat` - wysyłanie wiadomości
- `POST /api/v2/upload` - upload plików
- `GET /api/v2/agents` - status agentów
- `POST /api/v2/rag/search` - wyszukiwanie RAG
- `PUT /api/v2/settings` - aktualizacja ustawień

## 📱 Responsywność

### Breakpoints
- **Mobile:** 320px - 768px
- **Tablet:** 768px - 1024px
- **Desktop:** 1024px+

### Adaptacje mobile
- Składany sidebar
- Dotykowe gesty
- Optymalizacja czatu
- Voice input

## 🚀 Roadmapa rozwoju

### Faza 1 (Q3 2025) - MVP
- ✅ Podstawowy dashboard z oknem czatu
- ✅ Gotowe komendy (5 głównych)
- ✅ Upload paragonów
- ✅ Panel ustawień podstawowych

### Faza 2 (Q4 2025) - Rozszerzone funkcjonalności
- 🔄 Zaawansowane zarządzanie RAG
- 🔄 System promptów użytkownika
- 🔄 Analytics i raporty
- 🔄 Integracje zewnętrzne

### Faza 3 (Q1 2026) - AI Enhancements
- 📅 Voice interface
- 📅 Predictive UI
- 📅 Advanced personalization
- 📅 Multi-agent orchestration

### Faza 4 (Q2 2026) - Ecosystem
- 📅 Plugin system
- 📅 Third-party integrations
- 📅 Mobile companion app
- 📅 Cloud sync

## 🎯 Dodatkowe funkcjonalności do rozważenia

### Smart Assistant Features
1. **Kontekstowe sugestie** - AI przewiduje potrzeby użytkownika
2. **Learning from behavior** - personalizacja na podstawie użytkowania
3. **Proactive notifications** - przypomnienia o datach ważności
4. **Shopping optimization** - analizy oszczędności i marnotrawstwa
5. **Meal planning AI** - automatyczne planowanie posiłków na tydzień

### Integracje
1. **Kalendarze** - Google Calendar, Outlook
2. **E-commerce** - automatyczne zamówienia
3. **IoT devices** - lodówki, wagi kuchenne
4. **Health apps** - tracking kalorii, diet
5. **Social features** - udostępnianie przepisów

### Advanced Analytics
1. **Spending patterns** - analizy wydatków na żywność
2. **Waste reduction metrics** - tracking marnotrawstwa
3. **Nutrition tracking** - analiza wartości odżywczych
4. **Carbon footprint** - wpływ na środowisko
5. **Predictive analytics** - przewidywanie potrzeb

## 📊 Metryki sukcesu

### UX Metrics
- **Time to first interaction:** < 3 sekundy
- **Task completion rate:** > 90%
- **User satisfaction:** > 4.5/5
- **Feature adoption:** > 70% dla głównych funkcji

### Performance Metrics
- **Loading time:** < 2 sekundy
- **Response time:** < 1 sekunda
- **Crash rate:** < 0.1%
- **Memory usage:** < 150MB

## 🔧 Techniczne szczegóły implementacji

### State Management
```typescript
// Chat Store
interface ChatState {
  messages: Message[]
  isTyping: boolean
  currentAgent: string | null
  addMessage: (message: Message) => void
  setTyping: (typing: boolean) => void
}

// Agent Store  
interface AgentState {
  agents: Agent[]
  activeAgent: string | null
  setActiveAgent: (agentId: string) => void
  updateAgentStatus: (agentId: string, status: AgentStatus) => void
}
```

### Theme System
```typescript
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#007AFF',
      gradient: 'linear-gradient(45deg, #007AFF 30%, #5856D6 90%)'
    },
    secondary: {
      main: '#34C759'
    },
    background: {
      default: '#000000',
      paper: '#1C1C1E'
    }
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          backdropFilter: 'blur(20px)'
        }
      }
    }
  }
})
```

## 📋 Załączniki

### Aplikacja demonstracyjna
- **URL:** [AI Assistant Dashboard Demo](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/4d8397d00b85fe9d59784d8f1dc66681/72e1aa77-1daa-49c6-8f93-8eb01b4b6a27/index.html)
- **Funkcjonalności:** Pełny UI z interaktywnymi elementami
- **Dane testowe:** Przykładowe agenty, wiadomości, ustawienia

### Repozytorium GitHub
- **URL:** [codemarcinu/my_assistant](https://github.com/codemarcinu/my_assistant)
- **Branch:** feature/tauri-implementation
- **Status:** Gotowy do wdrożenia

---

**Opracowano:** AI Assistant Design Team  
**Kontakt:** [GitHub Issues](https://github.com/codemarcinu/my_assistant/issues)  
**Licencja:** MIT

> 💡 **Tip:** Ten design document służy jako kompletny przewodnik implementacji. Wszystkie komponenty są gotowe do integracji z istniejącym backendem FoodSave AI.