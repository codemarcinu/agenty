#!/bin/bash
# Setup aliases for AGENTY Console Application

echo "🔧 Konfigurowanie aliasów dla aplikacji konsolowej AGENTY..."

# Znajdź ścieżkę do projektu
AGENTY_PATH=$(pwd)

# Utwórz funkcje (działają lepiej niż aliasy w skryptach)
ALIAS_CONTENT="
# AGENTY Console Application Functions
agenty() { cd '$AGENTY_PATH' && ./start_agenty_console.sh; }
agenty-test() { cd '$AGENTY_PATH' && python test_console.py; }
agenty-console() { cd '$AGENTY_PATH' && python console_agenty_enhanced.py; }
agenty-simple() { cd '$AGENTY_PATH' && python console_agenty.py; }
agenty-backend() { cd '$AGENTY_PATH/agenty/backend' && python main.py; }

# Również aliasy dla kompatybilności
alias agenty='cd $AGENTY_PATH && ./start_agenty_console.sh' 
alias agenty-test='cd $AGENTY_PATH && python test_console.py'
alias agenty-console='cd $AGENTY_PATH && python console_agenty_enhanced.py'
alias agenty-simple='cd $AGENTY_PATH && python console_agenty.py'
alias agenty-backend='cd $AGENTY_PATH/agenty/backend && python main.py'
"

# Dodaj do .bashrc jeśli istnieje
if [ -f "$HOME/.bashrc" ]; then
    echo "$ALIAS_CONTENT" >> "$HOME/.bashrc"
    echo "✅ Aliasy dodane do ~/.bashrc"
fi

# Dodaj do .zshrc jeśli istnieje  
if [ -f "$HOME/.zshrc" ]; then
    echo "$ALIAS_CONTENT" >> "$HOME/.zshrc"
    echo "✅ Aliasy dodane do ~/.zshrc"
fi

# Utwórz plik z aliasami
echo "$ALIAS_CONTENT" > agenty_aliases.sh
chmod +x agenty_aliases.sh

echo ""
echo "🎯 Dostępne funkcje/aliasy:"
echo "  agenty         - Uruchom aplikację konsolową"
echo "  agenty-test    - Uruchom testy"
echo "  agenty-console - Uruchom bezpośrednio (enhanced)"
echo "  agenty-simple  - Uruchom wersję prostą"
echo "  agenty-backend - Uruchom backend"
echo ""
echo "💡 Aby aktywować:"
echo "  source ~/.bashrc   (dla bash - trwale)"
echo "  source ~/.zshrc    (dla zsh - trwale)"
echo "  source agenty_aliases.sh  (tymczasowo w bieżącej sesji)"
echo ""
echo "🚀 Po aktywacji użyj: agenty"
echo ""
echo "🔧 Aby sprawdzić czy działa:"
echo "  source agenty_aliases.sh && agenty-test"