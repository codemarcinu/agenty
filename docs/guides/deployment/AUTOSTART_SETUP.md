# Konfiguracja Autostartu FoodSave AI

## Opcja 1: Systemd Service (Rekomendowana)

### 1. Skopiuj plik service
```bash
sudo cp systemd-autostart.service /etc/systemd/system/foodsave-ai.service
```

### 2. Włącz autostart
```bash
sudo systemctl enable foodsave-ai.service
```

### 3. Sprawdź status
```bash
sudo systemctl status foodsave-ai.service
```

### 4. Ręczne zarządzanie
```bash
# Uruchom teraz
sudo systemctl start foodsave-ai.service

# Zatrzymaj
sudo systemctl stop foodsave-ai.service

# Sprawdź logi
sudo journalctl -u foodsave-ai.service -f
```

## Opcja 2: Docker Compose Autostart

### 1. Dodaj do ~/.bashrc
```bash
echo 'cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO && ./foodsave-dev.sh start' >> ~/.bashrc
```

### 2. Lub utwórz skrypt w ~/.config/autostart/
```bash
mkdir -p ~/.config/autostart/
cat > ~/.config/autostart/foodsave-ai.desktop << EOF
[Desktop Entry]
Type=Application
Name=FoodSave AI
Exec=/home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-dev.sh start
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

## Opcja 3: Cron Job

### 1. Edytuj crontab
```bash
crontab -e
```

### 2. Dodaj linię
```bash
@reboot cd /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO && ./foodsave-dev.sh start
```

## Sprawdzenie działania

Po konfiguracji autostartu:

1. **Restart systemu:**
   ```bash
   sudo reboot
   ```

2. **Sprawdź czy kontenery działają:**
   ```bash
   docker ps
   ./foodsave-dev.sh status
   ```

3. **Sprawdź logi:**
   ```bash
   docker compose -f docker-compose.dev.yaml logs -f
   ```

## Zalecenia

- **Używaj systemd service** - najlepsze zarządzanie i monitoring
- **Sprawdź zasoby** - aplikacja może być wymagająca (GPU dla Ollama)
- **Monitoruj logi** - szczególnie przy pierwszym uruchomieniu
- **Backup danych** - regularnie rób backup SQLite i vector store

## Troubleshooting

### Problem z uprawnieniami
```bash
chmod +x /home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-dev.sh
```

### Problem z Docker
```bash
sudo systemctl enable docker
sudo systemctl start docker
```

### Problem z portami
Sprawdź czy porty 8000, 3000, 11434, 5433 nie są zajęte przez inne aplikacje. 