#!/bin/bash

# =============================================================================
# COMPLETE FRONTEND TESTING SCRIPT
# =============================================================================

echo "🚀 Starting Complete Frontend Testing Suite"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC} $message"
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC} $message"
            ;;
    esac
}

# Function to check if containers are running
check_containers() {
    echo -e "\n${BLUE}🔍 Checking Container Status${NC}"
    
    containers=("foodsave-frontend" "foodsave-backend" "foodsave-redis" "foodsave-ollama")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2}')
            print_status "PASS" "$container: $status"
        else
            print_status "FAIL" "$container: Not running"
        fi
    done
}

# Function to test basic connectivity
test_connectivity() {
    echo -e "\n${BLUE}🌐 Testing Connectivity${NC}"
    
    # Test frontend
    if curl -s -f http://localhost:8085/ > /dev/null; then
        print_status "PASS" "Frontend accessible on port 8085"
    else
        print_status "FAIL" "Frontend not accessible on port 8085"
    fi
    
    # Test backend
    if curl -s -f http://localhost:8000/health > /dev/null; then
        print_status "PASS" "Backend accessible on port 8000"
    else
        print_status "FAIL" "Backend not accessible on port 8000"
    fi
    
    # Test API proxy
    if curl -s -f http://localhost:8085/health > /dev/null; then
        print_status "PASS" "API proxy working"
    else
        print_status "FAIL" "API proxy not working"
    fi
}

# Function to run Python tests
run_python_tests() {
    echo -e "\n${BLUE}🐍 Running Python Integration Tests${NC}"
    
    if command -v python3 &> /dev/null; then
        if python3 test_frontend_backend_integration.py; then
            print_status "PASS" "Integration tests completed"
        else
            print_status "FAIL" "Integration tests failed"
        fi
    else
        print_status "WARN" "Python3 not found, skipping integration tests"
    fi
}

# Function to run functionality tests
run_functionality_tests() {
    echo -e "\n${BLUE}🎨 Running Frontend Functionality Tests${NC}"
    
    if command -v python3 &> /dev/null; then
        if python3 test_frontend_functionality.py; then
            print_status "PASS" "Functionality tests completed"
        else
            print_status "FAIL" "Functionality tests failed"
        fi
    else
        print_status "WARN" "Python3 not found, skipping functionality tests"
    fi
}

# Function to test API endpoints
test_api_endpoints() {
    echo -e "\n${BLUE}🔌 Testing API Endpoints${NC}"
    
    endpoints=(
        "http://localhost:8085/api/agents/agents"
        "http://localhost:8085/api/v2/test"
        "http://localhost:8085/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s -f "$endpoint" > /dev/null; then
            print_status "PASS" "$(basename "$endpoint")"
        else
            print_status "FAIL" "$(basename "$endpoint")"
        fi
    done
}

# Function to check file sizes
check_file_sizes() {
    echo -e "\n${BLUE}📊 Checking File Sizes${NC}"
    
    files=(
        "http://localhost:8085/style.css"
        "http://localhost:8085/app.js"
        "http://localhost:8085/index.html"
    )
    
    for file in "${files[@]}"; do
        size=$(curl -s -I "$file" | grep -i content-length | awk '{print $2}' | tr -d '\r')
        if [ -n "$size" ] && [ "$size" -gt 1000 ]; then
            print_status "PASS" "$(basename "$file"): ${size} bytes"
        else
            print_status "FAIL" "$(basename "$file"): Too small or not found"
        fi
    done
}

# Function to show quick access info
show_access_info() {
    echo -e "\n${BLUE}🔗 Quick Access Information${NC}"
    echo "Frontend URL: http://localhost:8085"
    echo "Backend URL: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8085/health"
}

# Main execution
main() {
    echo "Starting comprehensive frontend testing..."
    echo "Timestamp: $(date)"
    echo ""
    
    check_containers
    test_connectivity
    test_api_endpoints
    check_file_sizes
    run_python_tests
    run_functionality_tests
    show_access_info
    
    echo -e "\n${GREEN}🎉 Testing Complete!${NC}"
    echo "Check the results above for any issues."
    echo "Frontend is accessible at: http://localhost:8085"
}

# Run main function
main "$@" 