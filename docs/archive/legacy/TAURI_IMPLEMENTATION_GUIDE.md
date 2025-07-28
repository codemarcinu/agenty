# 📦 FoodSave AI – Dokumentacja Implementacji Tauri (Linux/Ubuntu)

**Wersja:** 1.0  
**Data:** 27.01.2025  
**Platforma docelowa:** Linux (Ubuntu)  
**Autor:** AI Assistant

---

## Spis treści

1. [Wymagania systemowe](#wymagania-systemowe)
2. [Konfiguracja środowiska](#konfiguracja-środowiska)
3. [Struktura projektu](#struktura-projektu)
4. [Konfiguracja plików](#konfiguracja-plików)
5. [Przykłady implementacji](#przykłady-implementacji)
6. [Testowanie](#testowanie)
7. [Budowanie i dystrybucja](#budowanie-i-dystrybucja)
8. [Troubleshooting](#troubleshooting)
9. [Zasoby](#zasoby)

---

## Wymagania systemowe

- **Ubuntu 22.04+** (zalecane)
- **Rust**: 1.70+  
- **Node.js**: 20+  
- **Cargo**: najnowsza wersja  
- **libwebkit2gtk-4.0-dev**  
- **libgtk-3-dev**  
- **libayatana-appindicator3-dev**  
- **librsvg2-dev**  
- **libssl-dev**  
- **libappindicator3-dev**  
- **patchelf**  

### Instalacja zależności

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  libwebkit2gtk-4.0-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  libssl-dev \
  libappindicator3-dev \
  patchelf \
  curl
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

---

## Konfiguracja środowiska

1. **Instalacja Tauri CLI**
   ```bash
   npm install -g @tauri-apps/cli@2.6.2
   ```

2. **Dodanie skryptów do `package.json`**
   ```json
   {
     "scripts": {
       "tauri": "tauri",
       "tauri:dev": "tauri dev",
       "tauri:build": "tauri build"
     }
   }
   ```

3. **Konfiguracja Next.js**
   - `next.config.ts`:
     ```js
     const nextConfig = {
       output: 'export',
       trailingSlash: true,
       images: { unoptimized: true }
     };
     module.exports = nextConfig;
     ```
   - `tsconfig.json`:
     ```json
     {
       "exclude": ["node_modules", "src-tauri"]
     }
     ```

---

## Struktura projektu

```
AIASISSTMARUBO/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs
│   │   └── api/
│   ├── Cargo.toml
│   ├── build.rs
│   └── tauri.conf.json
├── myappassistant-chat-frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   └── useTauriAPI.ts
│   │   └── components/
│   │       └── tauri/
│   │           └── TauriTestComponent.tsx
│   └── out/
├── package.json
└── tauri.conf.json
```

---

## Konfiguracja plików

### `src-tauri/tauri.conf.json` (fragmenty istotne dla Linux)

```json
{
  "$schema": "https://beta.tauri.app/schema.json",
  "identifier": "com.foodsave.ai",
  "productName": "FoodSave AI",
  "version": "1.0.0",
  "build": {
    "frontendDist": "../out",
    "devUrl": "http://localhost:3000",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "FoodSave AI - Personal Assistant",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "center": true,
        "decorations": true,
        "transparent": false,
        "alwaysOnTop": false,
        "skipTaskbar": false,
        "visible": true,
        "closable": true,
        "minimizable": true,
        "maximizable": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": ["deb", "appimage"],
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "resources": [],
    "externalBin": [],
    "copyright": "",
    "category": "Utility",
    "shortDescription": "Personal AI Assistant for Food Management",
    "longDescription": "FoodSave AI is a comprehensive personal assistant that helps manage food inventory, process receipts, and provide intelligent recommendations for food management."
  },
  "plugins": {
    "fs": {
      "scope": ["$APPDATA/**", "$APPDATA/foodsave-ai/**", "$APPDATA/foodsave-ai/*"]
    },
    "notification": {},
    "globalShortcut": {},
    "window": {},
    "app": {},
    "http": {
      "scope": [
        "http://localhost:8000/**",
        "https://api.foodsave.ai/**"
      ]
    },
    "dialog": {}
  }
}
```

### `Cargo.toml` (fragment)

```toml
[package]
name = "foodsave-ai"
version = "1.0.0"
description = "FoodSave AI - Personal Assistant"
authors = ["FoodSave AI Team"]
license = "MIT"
edition = "2021"

[build-dependencies]
tauri-build = { version = "2.3", features = [] }

[dependencies]
tauri = { version = "2.6" }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }
notify-rust = "4"
notify = "6"
chrono = { version = "0.4", features = ["serde"] }
image = "0.24"
base64 = "0.21"
uuid = { version = "1.0", features = ["v4"] }

[features]
custom-protocol = ["tauri/custom-protocol"]
```

---

## Przykłady implementacji

### Komenda Rust (src-tauri/src/main.rs)

```rust
#[tauri::command]
async fn process_receipt_image(path: String) -> Result<ReceiptData, String> {
    // Przetwarzanie obrazu paragonu (OCR)
    Ok(ReceiptData { /* ... */ })
}

#[tauri::command]
fn show_system_notification(title: String, body: String) -> Result<(), String> {
    notify_rust::Notification::new()
        .summary(&title)
        .body(&body)
        .show()
        .map_err(|e| e.to_string())?;
    Ok(())
}
```

### Hook TypeScript (myappassistant-chat-frontend/src/hooks/useTauriAPI.ts)

```typescript
import { invoke } from '@tauri-apps/api/tauri';

export const useTauriAPI = () => {
  const processReceipt = async (path: string) => {
    return await invoke('process_receipt_image', { path });
  };
  const showNotification = async (title: string, body: string) => {
    return await invoke('show_system_notification', { title, body });
  };
  return { processReceipt, showNotification };
};
```

---

## Testowanie

### Testy Rust

```rust
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_show_system_notification() {
        assert!(show_system_notification("Test".into(), "Body".into()).is_ok());
    }
}
```

### Testy TypeScript

```typescript
import { invoke } from '@tauri-apps/api/tauri';
test('should show notification', async () => {
  await expect(invoke('show_system_notification', {
    title: 'Test', body: 'Body'
  })).resolves.toBeUndefined();
});
```

---

## Budowanie i dystrybucja

### Build dev

```bash
npm run tauri dev
```

### Build produkcyjny (DEB package)

```bash
npm run tauri build
# Wynik: src-tauri/target/release/bundle/deb/foodsave-ai_1.0.0_amd64.deb
```

---

## Troubleshooting

- **Brak WebKit:**  
  `sudo apt install libwebkit2gtk-4.0-dev`
- **Brak uprawnień do plików:**  
  Sprawdź allowlist w `tauri.conf.json`
- **Błędy build:**  
  `cargo clean && npm run build && npm run tauri build`

---

## Zasoby

- [Tauri Docs](https://tauri.app/v1/guides/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Tauri + Next.js Template](https://github.com/kvnxiao/tauri-nextjs-template)

---

**Status:** Dokumentacja kompletna, gotowa do wdrożenia na Ubuntu/Linux.  
**Wersja:** 1.0  
**Data:** 27.01.2025 