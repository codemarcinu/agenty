# 🎨 Plan Ulepszeń Frontend - Integracja Telegram

## 🎯 Cel
Dodanie panelu konfiguracji Telegram Bot do interfejsu użytkownika, aby można było łatwo zarządzać botem bez użycia terminala.

## 📋 Funkcjonalności do Dodania

### 1. Panel Ustawień Telegram
```typescript
// src/components/settings/TelegramSettings.tsx
interface TelegramSettings {
  enabled: boolean;
  botToken: string;
  botUsername: string;
  webhookUrl: string;
  webhookSecret: string;
  maxMessageLength: number;
  rateLimitPerMinute: number;
}
```

### 2. Funkcje Panelu
- ✅ **Konfiguracja Token** - Wprowadzanie tokenu z BotFather
- ✅ **Test Połączenia** - Sprawdzanie czy bot działa
- ✅ **Status Webhook** - Sprawdzanie statusu webhook
- ✅ **Ustawienie Webhook** - Konfiguracja webhook URL
- ✅ **Statystyki** - Liczba wiadomości, czas odpowiedzi
- ✅ **Logi** - Podgląd logów Telegram w czasie rzeczywistym

### 3. Integracja z GUI
- Dodanie zakładki "Telegram" w ustawieniach
- Ikona Telegram w głównym menu
- Powiadomienia o statusie bota
- Szybki dostęp do konfiguracji

---

## 🔧 Implementacja

### 1. Komponent Ustawień
```typescript
// src/components/settings/TelegramSettings.tsx
import React, { useState, useEffect } from 'react';
import { telegramAPI } from '../../services/telegramApi';

export default function TelegramSettings() {
  const [settings, setSettings] = useState<TelegramSettings>({
    enabled: false,
    botToken: '',
    botUsername: '',
    webhookUrl: '',
    webhookSecret: '',
    maxMessageLength: 4096,
    rateLimitPerMinute: 30
  });

  const [isLoading, setIsLoading] = useState(false);
  const [testResult, setTestResult] = useState<string>('');
  const [webhookStatus, setWebhookStatus] = useState<string>('');

  // Funkcje do implementacji:
  // - loadSettings()
  // - saveSettings()
  // - testConnection()
  // - setWebhook()
  // - getWebhookInfo()
}
```

### 2. API Service
```typescript
// src/services/telegramApi.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const telegramAPI = {
  // Pobierz ustawienia bota
  getBotSettings: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v2/telegram/settings`);
    return response.data;
  },

  // Zaktualizuj ustawienia bota
  updateBotSettings: async (settings: TelegramSettings) => {
    const response = await axios.put(`${API_BASE_URL}/api/v2/telegram/settings`, settings);
    return response.data;
  },

  // Test połączenia z botem
  testConnection: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v2/telegram/test-connection`);
    return response.data;
  },

  // Pobierz informacje o webhook
  getWebhookInfo: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v2/telegram/webhook-info`);
    return response.data;
  },

  // Ustaw webhook
  setWebhook: async (webhookUrl: string) => {
    const response = await axios.post(`${API_BASE_URL}/api/v2/telegram/set-webhook`, {
      webhook_url: webhookUrl
    });
    return response.data;
  },

  // Wyślij wiadomość testową
  sendTestMessage: async (chatId: number, message: string) => {
    const response = await axios.post(`${API_BASE_URL}/api/v2/telegram/send-message`, {
      chat_id: chatId,
      message: message
    });
    return response.data;
  }
};
```

### 3. Store Integration
```typescript
// src/stores/settingsStore.ts - Dodaj do UserSettings
interface UserSettings {
  // ... istniejące pola
  integrations: {
    telegram: TelegramSettings;
    weather: WeatherSettings;
  };
}

// Domyślne ustawienia
const defaultSettings: UserSettings = {
  // ... istniejące pola
  integrations: {
    telegram: {
      enabled: false,
      botToken: '',
      botUsername: '',
      webhookUrl: '',
      webhookSecret: '',
      maxMessageLength: 4096,
      rateLimitPerMinute: 30
    },
    weather: {
      enabled: true,
      location: 'Warsaw, Poland',
      units: 'metric'
    }
  }
};
```

### 4. Routing i Menu
```typescript
// src/App.tsx - Dodaj do menu
const menuItems = [
  // ... istniejące elementy
  {
    label: 'Telegram Bot',
    icon: '🤖',
    path: '/settings/telegram',
    component: TelegramSettings
  }
];
```

---

## 🎨 UI/UX Design

### 1. Panel Konfiguracji
```typescript
// Komponent z formularzem
<div className="telegram-settings">
  <h2>🤖 Konfiguracja Telegram Bot</h2>
  
  {/* Status Webhook */}
  <div className="webhook-status">
    <span>Status: {webhookStatus}</span>
  </div>
  
  {/* Formularz konfiguracji */}
  <form onSubmit={handleSaveSettings}>
    <input 
      type="password" 
      placeholder="Token z BotFather"
      value={settings.botToken}
      onChange={(e) => setSettings({...settings, botToken: e.target.value})}
    />
    
    <input 
      type="text" 
      placeholder="Username bota"
      value={settings.botUsername}
      onChange={(e) => setSettings({...settings, botUsername: e.target.value})}
    />
    
    <input 
      type="url" 
      placeholder="Webhook URL"
      value={settings.webhookUrl}
      onChange={(e) => setSettings({...settings, webhookUrl: e.target.value})}
    />
    
    <button type="submit">Zapisz Ustawienia</button>
  </form>
  
  {/* Przyciski akcji */}
  <div className="action-buttons">
    <button onClick={handleTestConnection}>Test Połączenia</button>
    <button onClick={handleSetWebhook}>Ustaw Webhook</button>
    <button onClick={handleGetWebhookInfo}>Sprawdź Status</button>
  </div>
</div>
```

### 2. Statystyki i Monitoring
```typescript
// Komponent statystyk
<div className="telegram-stats">
  <h3>📊 Statystyki Telegram</h3>
  
  <div className="stats-grid">
    <div className="stat-item">
      <span className="stat-label">Wiadomości dzisiaj</span>
      <span className="stat-value">{stats.messagesToday}</span>
    </div>
    
    <div className="stat-item">
      <span className="stat-label">Średni czas odpowiedzi</span>
      <span className="stat-value">{stats.avgResponseTime}ms</span>
    </div>
    
    <div className="stat-item">
      <span className="stat-label">Aktywni użytkownicy</span>
      <span className="stat-value">{stats.activeUsers}</span>
    </div>
  </div>
</div>
```

### 3. Logi w Czasie Rzeczywistym
```typescript
// Komponent logów
<div className="telegram-logs">
  <h3>📝 Logi Telegram</h3>
  
  <div className="logs-container">
    {logs.map((log, index) => (
      <div key={index} className={`log-entry log-${log.level}`}>
        <span className="log-timestamp">{log.timestamp}</span>
        <span className="log-message">{log.message}</span>
      </div>
    ))}
  </div>
  
  <button onClick={handleRefreshLogs}>Odśwież Logi</button>
</div>
```

---

## 🔧 Funkcjonalności Zaawansowane

### 1. Automatyczna Konfiguracja
```typescript
// Funkcja automatycznej konfiguracji
const handleAutoSetup = async () => {
  try {
    setIsLoading(true);
    
    // 1. Sprawdź czy token jest poprawny
    const connectionTest = await telegramAPI.testConnection();
    if (!connectionTest.ok) {
      throw new Error('Nieprawidłowy token bota');
    }
    
    // 2. Wygeneruj webhook URL
    const webhookUrl = `${window.location.origin}/api/v2/telegram/webhook`;
    
    // 3. Ustaw webhook
    const webhookResult = await telegramAPI.setWebhook(webhookUrl);
    if (!webhookResult.ok) {
      throw new Error('Nie udało się ustawić webhook');
    }
    
    // 4. Zapisz ustawienia
    await telegramAPI.updateBotSettings({
      ...settings,
      webhookUrl: webhookUrl,
      enabled: true
    });
    
    setTestResult('✅ Konfiguracja zakończona pomyślnie!');
    
  } catch (error) {
    setTestResult(`❌ Błąd: ${error.message}`);
  } finally {
    setIsLoading(false);
  }
};
```

### 2. Test Wiadomości
```typescript
// Funkcja testowania wiadomości
const handleSendTestMessage = async () => {
  try {
    const response = await telegramAPI.sendTestMessage(
      testChatId, 
      '🤖 Test wiadomości z FoodSave AI!'
    );
    
    if (response.status === 'success') {
      setTestResult('✅ Wiadomość testowa wysłana pomyślnie!');
    } else {
      setTestResult('❌ Błąd wysyłania wiadomości');
    }
    
  } catch (error) {
    setTestResult(`❌ Błąd: ${error.message}`);
  }
};
```

### 3. Monitoring w Czasie Rzeczywistym
```typescript
// Hook do monitorowania w czasie rzeczywistym
const useTelegramMonitoring = () => {
  const [stats, setStats] = useState<TelegramStats>({
    messagesToday: 0,
    avgResponseTime: 0,
    activeUsers: 0,
    errors: 0
  });

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await telegramAPI.getStats();
        setStats(response.data);
      } catch (error) {
        console.error('Błąd pobierania statystyk:', error);
      }
    }, 30000); // Aktualizuj co 30 sekund

    return () => clearInterval(interval);
  }, []);

  return stats;
};
```

---

## 🎯 Scenariusze Użycia

### 1. Pierwsza Konfiguracja
1. Użytkownik przechodzi do Ustawienia → Telegram
2. Wprowadza token z BotFather
3. Kliknie "Test Połączenia"
4. Kliknie "Automatyczna Konfiguracja"
5. Bot jest gotowy do użycia

### 2. Monitoring Codzienny
1. Sprawdzenie statystyk w panelu
2. Przeglądanie logów w czasie rzeczywistym
3. Sprawdzanie statusu webhook
4. Testowanie funkcjonalności

### 3. Rozwiązywanie Problemów
1. Sprawdzenie logów błędów
2. Test połączenia z botem
3. Resetowanie webhook
4. Kontakt z supportem

---

## 📊 Metryki i Analytics

### 1. Statystyki Użytkowników
- Liczba aktywnych użytkowników
- Czas spędzony z botem
- Najpopularniejsze komendy
- Wskaźnik retencji

### 2. Metryki Wydajności
- Czas odpowiedzi AI
- Liczba błędów
- Użycie zasobów
- Rate limiting

### 3. Metryki Biznesowe
- Liczba analizowanych paragonów
- Liczba wyszukanych przepisów
- Satysfakcja użytkowników
- ROI integracji

---

## 🔒 Bezpieczeństwo

### 1. Walidacja Danych
```typescript
// Walidacja tokenu
const validateBotToken = (token: string): boolean => {
  const tokenRegex = /^\d+:[A-Za-z0-9_-]{35}$/;
  return tokenRegex.test(token);
};

// Walidacja URL
const validateWebhookUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === 'https:';
  } catch {
    return false;
  }
};
```

### 2. Szyfrowanie Danych
```typescript
// Szyfrowanie tokenu w localStorage
const encryptToken = (token: string): string => {
  return btoa(token); // Podstawowe szyfrowanie
};

const decryptToken = (encryptedToken: string): string => {
  return atob(encryptedToken);
};
```

### 3. Rate Limiting
```typescript
// Rate limiting dla API calls
const rateLimiter = {
  lastCall: 0,
  minInterval: 1000, // 1 sekunda między wywołaniami
  
  canMakeCall: (): boolean => {
    const now = Date.now();
    if (now - rateLimiter.lastCall >= rateLimiter.minInterval) {
      rateLimiter.lastCall = now;
      return true;
    }
    return false;
  }
};
```

---

## 🚀 Plan Wdrożenia

### Faza 1: Podstawowa Implementacja (1-2 dni)
- [ ] Komponent TelegramSettings
- [ ] API service dla Telegram
- [ ] Integracja ze store
- [ ] Podstawowy routing

### Faza 2: Funkcjonalności Zaawansowane (3-5 dni)
- [ ] Automatyczna konfiguracja
- [ ] Monitoring w czasie rzeczywistym
- [ ] Statystyki i analytics
- [ ] System logów

### Faza 3: Optymalizacja (1-2 dni)
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Optymalizacja wydajności
- [ ] Dokumentacja

---

## 🎉 Rezultat

Po implementacji będziesz mieć:

1. **🤖 Przyjazny Panel Konfiguracji** - Łatwe zarządzanie botem
2. **📊 Monitoring w Czasie Rzeczywistym** - Statystyki i logi
3. **🔧 Automatyczna Konfiguracja** - Jednym kliknięciem
4. **🛡️ Bezpieczeństwo** - Walidacja i szyfrowanie
5. **📱 Mobilny Dostęp** - Telegram jako interfejs mobilny

**Telegram Bot stanie się pełnoprawnym mobilnym interfejsem do Twojego systemu FoodSave AI!** 