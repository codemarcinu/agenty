#!/bin/bash

# Skrypt konfiguracji aliasu "asystent"
# Autor: Agenty Team
# Wersja: 1.0.0

set -e

# Kolorowe komunikaty
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Sprawdzenie czy skrypt asystent istnieje
if [ ! -f "./asystent" ]; then
    print_error "Plik 'asystent' nie istnieje w bieżącym katalogu!"
    print_info "Upewnij się, że jesteś w katalogu projektu AGENTY"
    exit 1
fi

# Ścieżka do projektu
PROJECT_PATH=$(pwd)
ALIAS_COMMAND="alias asystent='$PROJECT_PATH/asystent'"

print_info "Konfiguracja aliasu 'asystent'..."
print_info "Ścieżka projektu: $PROJECT_PATH"

# Sprawdzenie typu powłoki
SHELL_TYPE=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_TYPE="zsh"
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_TYPE="bash"
    SHELL_RC="$HOME/.bashrc"
else
    print_warning "Nieznana powłoka. Sprawdzam dostępne pliki konfiguracyjne..."
    
    # Sprawdzenie dostępnych plików konfiguracyjnych
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_TYPE="bash"
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_TYPE="zsh"
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.profile" ]; then
        SHELL_TYPE="profile"
        SHELL_RC="$HOME/.profile"
    else
        print_error "Nie znaleziono pliku konfiguracyjnego powłoki!"
        print_info "Ręcznie dodaj alias do swojego pliku konfiguracyjnego:"
        echo "  $ALIAS_COMMAND"
        exit 1
    fi
fi

print_info "Wykryta powłoka: $SHELL_TYPE"
print_info "Plik konfiguracyjny: $SHELL_RC"

# Sprawdzenie czy alias już istnieje
if grep -q "alias asystent=" "$SHELL_RC"; then
    print_warning "Alias 'asystent' już istnieje w $SHELL_RC"
    read -p "Czy chcesz go zaktualizować? (y/N): " update_choice
    
    if [[ $update_choice =~ ^[Yy]$ ]]; then
        # Usuń stary alias
        sed -i '/alias asystent=/d' "$SHELL_RC"
        print_info "Stary alias został usunięty"
    else
        print_info "Alias nie został zmieniony"
        exit 0
    fi
fi

# Dodanie aliasu do pliku konfiguracyjnego
echo "" >> "$SHELL_RC"
echo "# Alias dla aplikacji Agenty" >> "$SHELL_RC"
echo "$ALIAS_COMMAND" >> "$SHELL_RC"

print_success "Alias 'asystent' został dodany do $SHELL_RC"

# Instrukcje dla użytkownika
echo ""
print_info "Instrukcje aktywacji:"
echo "1. Zrestartuj terminal lub wykonaj:"
echo "   source $SHELL_RC"
echo ""
echo "2. Sprawdź czy alias działa:"
echo "   asystent help"
echo ""
echo "3. Dostępne komendy:"
echo "   asystent          - Menu główne"
echo "   asystent dev      - Tryb deweloperski"
echo "   asystent prod     - Tryb produkcyjny"
echo "   asystent status   - Status usług"
echo "   asystent stop     - Zatrzymaj usługi"
echo "   asystent logs     - Pokaż logi"
echo "   asystent test     - Uruchom testy"
echo "   asystent help     - Pomoc"
echo ""

# Opcjonalna aktywacja aliasu w bieżącej sesji
read -p "Czy chcesz aktywować alias w bieżącej sesji? (Y/n): " activate_choice

if [[ $activate_choice =~ ^[Nn]$ ]]; then
    print_info "Alias zostanie aktywny po restarcie terminala"
else
    eval "$ALIAS_COMMAND"
    print_success "Alias został aktywowany w bieżącej sesji!"
    
    # Test aliasu
    print_info "Testowanie aliasu..."
    if command -v asystent &> /dev/null; then
        print_success "Alias działa poprawnie!"
        echo ""
        print_info "Możesz teraz używać komendy 'asystent' z dowolnego miejsca"
    else
        print_warning "Alias nie został poprawnie aktywowany"
        print_info "Spróbuj zrestartować terminal"
    fi
fi

echo ""
print_success "Konfiguracja zakończona! 🎉" 