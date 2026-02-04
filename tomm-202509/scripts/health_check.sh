#!/bin/bash

# Health Check Script for Typesense Services
# This script tests the health of Typesense and Dashboard services
# You have to run this script outside of the Docker container.

echo "🔍 Checking Typesense and Dashboard Health..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test a service
test_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $service_name... "
    
    # Test connection with timeout
    response=$(curl -s -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null)
    http_code="${response: -3}"
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY (HTTP: $http_code)${NC}"
        return 1
    fi
}

# Function to test JSON API response
test_json_api() {
    local service_name=$1
    local url=$2
    local api_key=${3:-""}
    
    echo -n "Testing $service_name API... "
    
    # Prepare curl command with optional API key
    curl_cmd="curl -s --connect-timeout 5 --max-time 10"
    if [ -n "$api_key" ]; then
        curl_cmd="$curl_cmd -H \"X-TYPESENSE-API-KEY: $api_key\""
    fi
    
    # Execute curl and check response
    response=$(eval "$curl_cmd \"$url\"" 2>/dev/null)
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API RESPONDING${NC}"
        echo -e "   ${BLUE}Response:${NC} $response"
        return 0
    else
        echo -e "${RED}❌ API NOT RESPONDING${NC}"
        echo -e "   ${YELLOW}Response:${NC} $response"
        return 1
    fi
}

# Test Typesense API Health
echo -e "\n${BLUE}🔍 Testing Typesense Server${NC}"
test_json_api "Typesense Collections" "http://localhost:8108/collections" "xyz"
test_json_api "Typesense Stats" "http://localhost:8108/stats.json" "xyz"

# Test Port Forwarding
echo -e "\n${BLUE}🔍 Testing Port Forwarding${NC}"
test_service "Typesense (localhost:8108)" "http://localhost:8108/health"
test_service "Dashboard (localhost:80)" "http://localhost:80" "200"

# Summary
echo ""
echo "================================================"
echo -e "${BLUE}🏥 Health Check Complete!${NC}"
echo ""
echo -e "If services are healthy, you can access:"
echo -e "  • Typesense API: ${GREEN}http://localhost:8108${NC}"
echo -e "  • Typesense Dashboard: ${GREEN}http://localhost:80${NC}"
echo ""
