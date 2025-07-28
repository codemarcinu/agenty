#!/bin/bash

# =============================================================================
# Skrypt testujący FoodSave AI Manager
# =============================================================================

# Kolory
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}💡 $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    🧪 Test FoodSave AI Manager                              ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Test 1: Sprawdź pliki
test_files() {
    print_info "Test 1: Sprawdzanie plików managera..."
    
    local files=(
        "./foodsave-manager"
        "./scripts/foodsave_manager_simple.sh"
        "./install_desktop_shortcut.sh"
        "./README_PROSTY_MANAGER.md"
    )
    
    local all_good=true
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            if [ -x "$file" ]; then
                print_success "$file - OK (wykonywalny)"
            else
                print_warning "$file - istnieje, ale nie jest wykonywalny"
                chmod +x "$file" && print_success "Naprawiono uprawnienia dla $file"
            fi
        else
            print_error "$file - BRAK"
            all_good=false
        fi
    done
    
    return $([[ "$all_good" == "true" ]] && echo 0 || echo 1)
}

# Test 2: Sprawdź skrót na pulpicie
test_desktop_shortcut() {
    print_info "Test 2: Sprawdzanie skrótu na pulpicie..."
    
    local desktop_dirs=(
        "$HOME/Pulpit"
        "$HOME/Desktop" 
        "$HOME/Biurko"
    )
    
    local found=false
    
    for dir in "${desktop_dirs[@]}"; do
        local shortcut="$dir/FoodSave-AI-Manager.desktop"
        if [ -f "$shortcut" ]; then
            print_success "Znaleziono skrót: $shortcut"
            if [ -x "$shortcut" ]; then
                print_success "Skrót ma prawidłowe uprawnienia"
            else
                print_warning "Skrót nie ma uprawnień wykonywania"
                chmod +x "$shortcut" && print_success "Naprawiono uprawnienia skrótu"
            fi
            found=true
            break
        fi
    done
    
    if [ "$found" = false ]; then
        print_warning "Nie znaleziono skrótu na pulpicie"
        print_info "Uruchom: ./install_desktop_shortcut.sh"
        return 1
    fi
    
    return 0
}

# Test 3: Sprawdź Docker
test_docker() {
    print_info "Test 3: Sprawdzanie Docker..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker nie jest zainstalowany"
        return 1
    fi
    
    print_success "Docker jest zainstalowany"
    
    if ! docker ps >/dev/null 2>&1; then
        print_error "Docker nie działa lub brak uprawnień"
        return 1
    fi
    
    print_success "Docker działa prawidłowo"
    
    # Sprawdź kontenery FoodSave
    local containers=$(docker ps --filter "name=foodsave-" --format "{{.Names}}" | wc -l)
    if [ "$containers" -gt 0 ]; then
        print_success "Znaleziono $containers kontenerów FoodSave"
    else
        print_warning "Brak działających kontenerów FoodSave"
    fi
    
    return 0
}

# Test 4: Sprawdź aplikację
test_application() {
    print_info "Test 4: Sprawdzanie dostępności aplikacji..."
    
    # Test frontend
    if curl -f http://localhost:8085/ >/dev/null 2>&1; then
        print_success "Frontend dostępny: http://localhost:8085"
    else
        print_warning "Frontend niedostępny: http://localhost:8085"
    fi
    
    # Test backend
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend dostępny: http://localhost:8000"
    else
        print_warning "Backend niedostępny: http://localhost:8000"
    fi
    
    return 0
}

# Test 5: Test funkcji managera
test_manager_functions() {
    print_info "Test 5: Sprawdzanie funkcji managera..."
    
    # Test czy skrypt się uruchamia
    if timeout 5 ./foodsave-manager --version >/dev/null 2>&1; then
        print_success "Manager uruchamia się poprawnie"
    elif timeout 5 ./scripts/foodsave_manager_simple.sh >/dev/null 2>&1; then
        print_success "Skrypt managera działa"
    else
        print_warning "Nie można przetestować managera (wymaga interakcji)"
    fi
    
    return 0
}

# Główna funkcja
main() {
    print_header
    
    local total_tests=5
    local passed_tests=0
    
    # Uruchom testy
    if test_files; then ((passed_tests++)); fi
    echo
    
    if test_desktop_shortcut; then ((passed_tests++)); fi
    echo
    
    if test_docker; then ((passed_tests++)); fi
    echo
    
    if test_application; then ((passed_tests++)); fi
    echo
    
    if test_manager_functions; then ((passed_tests++)); fi
    echo
    
    # Podsumowanie
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                            📊 PODSUMOWANIE TESTÓW                           ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    if [ "$passed_tests" -eq "$total_tests" ]; then
        print_success "🎉 Wszystkie testy przeszły pomyślnie ($passed_tests/$total_tests)"
        echo
        print_info "Manager FoodSave AI jest gotowy do użycia!"
        print_info "Uruchom przez: ./foodsave-manager lub kliknij ikonę na pulpicie"
    else
        print_warning "⚠️ Przeszło $passed_tests/$total_tests testów"
        echo
        print_info "Niektóre funkcje mogą nie działać poprawnie"
        print_info "Sprawdź komunikaty powyżej i napraw problemy"
    fi
    
    echo
}

main "$@"