#!/bin/bash

# DocScope Intelligent Installation Script with Port Detection
# This script automatically finds available ports and configures Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default ports (will be changed if not available)
DEFAULT_API_PORT=8000
DEFAULT_UI_PORT=8080
DEFAULT_POSTGRES_PORT=5432
DEFAULT_REDIS_PORT=6379
DEFAULT_NGINX_HTTP_PORT=80
DEFAULT_NGINX_HTTPS_PORT=443
DEFAULT_METRICS_PORT=9090

# Configuration file
CONFIG_FILE=".env.docker"
COMPOSE_OVERRIDE="docker-compose.override.yml"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to check if a port is available
is_port_available() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        # Use lsof if available (macOS, Linux)
        ! lsof -i:$port >/dev/null 2>&1
    elif command -v netstat >/dev/null 2>&1; then
        # Use netstat as fallback
        ! netstat -tuln 2>/dev/null | grep -q ":$port "
    else
        # Use nc (netcat) as last resort
        ! nc -z localhost $port 2>/dev/null
    fi
}

# Function to find an available port starting from a given port
find_available_port() {
    local start_port=$1
    local max_attempts=100
    local port=$start_port
    
    for ((i=0; i<$max_attempts; i++)); do
        if is_port_available $port; then
            echo $port
            return 0
        fi
        ((port++))
    done
    
    # If no port found in range, return 0 (error)
    echo 0
    return 1
}

# Function to detect all available ports
detect_available_ports() {
    print_color $BLUE "🔍 Detecting available ports..."
    echo ""
    
    # Find available ports
    API_PORT=$(find_available_port $DEFAULT_API_PORT)
    UI_PORT=$(find_available_port $DEFAULT_UI_PORT)
    POSTGRES_PORT=$(find_available_port $DEFAULT_POSTGRES_PORT)
    REDIS_PORT=$(find_available_port $DEFAULT_REDIS_PORT)
    NGINX_HTTP_PORT=$(find_available_port $DEFAULT_NGINX_HTTP_PORT)
    NGINX_HTTPS_PORT=$(find_available_port $DEFAULT_NGINX_HTTPS_PORT)
    METRICS_PORT=$(find_available_port $DEFAULT_METRICS_PORT)
    
    # Check if all ports were found
    if [[ $API_PORT -eq 0 ]] || [[ $UI_PORT -eq 0 ]] || [[ $POSTGRES_PORT -eq 0 ]] || \
       [[ $REDIS_PORT -eq 0 ]] || [[ $NGINX_HTTP_PORT -eq 0 ]] || [[ $NGINX_HTTPS_PORT -eq 0 ]]; then
        print_color $RED "❌ Error: Could not find available ports"
        exit 1
    fi
    
    # Display port configuration
    print_color $GREEN "✅ Available ports detected:"
    echo ""
    echo "  Service          Default Port  →  Available Port"
    echo "  ─────────────────────────────────────────────────"
    
    # Function to display port with status
    display_port() {
        local service=$1
        local default=$2
        local actual=$3
        local status=""
        
        if [[ $default -eq $actual ]]; then
            status="${GREEN}✓${NC}"
        else
            status="${YELLOW}↻${NC}"
        fi
        
        printf "  %-15s  %-12d  →  %-8d %s\n" "$service" "$default" "$actual" "$(echo -e $status)"
    }
    
    display_port "API" $DEFAULT_API_PORT $API_PORT
    display_port "Web UI" $DEFAULT_UI_PORT $UI_PORT
    display_port "PostgreSQL" $DEFAULT_POSTGRES_PORT $POSTGRES_PORT
    display_port "Redis" $DEFAULT_REDIS_PORT $REDIS_PORT
    display_port "HTTP" $DEFAULT_NGINX_HTTP_PORT $NGINX_HTTP_PORT
    display_port "HTTPS" $DEFAULT_NGINX_HTTPS_PORT $NGINX_HTTPS_PORT
    display_port "Metrics" $DEFAULT_METRICS_PORT $METRICS_PORT
    
    echo ""
    
    # Warn about changed ports
    local changed=false
    if [[ $API_PORT -ne $DEFAULT_API_PORT ]] || [[ $UI_PORT -ne $DEFAULT_UI_PORT ]] || \
       [[ $POSTGRES_PORT -ne $DEFAULT_POSTGRES_PORT ]] || [[ $REDIS_PORT -ne $DEFAULT_REDIS_PORT ]] || \
       [[ $NGINX_HTTP_PORT -ne $DEFAULT_NGINX_HTTP_PORT ]] || [[ $NGINX_HTTPS_PORT -ne $DEFAULT_NGINX_HTTPS_PORT ]]; then
        changed=true
        print_color $YELLOW "⚠️  Some ports were changed to avoid conflicts"
    fi
    
    # Show what's using the default ports if they're not available
    if $changed; then
        echo ""
        print_color $CYAN "📋 Conflicting services:"
        
        check_port_usage() {
            local port=$1
            local service=$2
            if ! is_port_available $port; then
                local process=""
                if command -v lsof >/dev/null 2>&1; then
                    process=$(lsof -i:$port 2>/dev/null | grep LISTEN | awk '{print $1}' | head -1)
                fi
                if [[ -n $process ]]; then
                    echo "  Port $port ($service): used by $process"
                else
                    echo "  Port $port ($service): in use"
                fi
            fi
        }
        
        check_port_usage $DEFAULT_API_PORT "API"
        check_port_usage $DEFAULT_UI_PORT "UI"
        check_port_usage $DEFAULT_POSTGRES_PORT "PostgreSQL"
        check_port_usage $DEFAULT_REDIS_PORT "Redis"
        check_port_usage $DEFAULT_NGINX_HTTP_PORT "HTTP"
        check_port_usage $DEFAULT_NGINX_HTTPS_PORT "HTTPS"
    fi
}

# Function to create environment file
create_env_file() {
    print_color $BLUE "\n📝 Creating environment configuration..."
    
    cat > $CONFIG_FILE << EOF
# DocScope Docker Environment Configuration
# Generated on $(date)
# This file contains the port mappings for your DocScope installation

# Service Ports
DOCSCOPE_API_PORT=${API_PORT}
DOCSCOPE_UI_PORT=${UI_PORT}
DOCSCOPE_POSTGRES_PORT=${POSTGRES_PORT}
DOCSCOPE_REDIS_PORT=${REDIS_PORT}
DOCSCOPE_NGINX_HTTP_PORT=${NGINX_HTTP_PORT}
DOCSCOPE_NGINX_HTTPS_PORT=${NGINX_HTTPS_PORT}
DOCSCOPE_METRICS_PORT=${METRICS_PORT}

# Database Configuration
POSTGRES_DB=docscope
POSTGRES_USER=docscope
POSTGRES_PASSWORD=docscope-dev-password

# Redis Configuration
REDIS_PASSWORD=

# Application Configuration
DOCSCOPE_SECRET_KEY=change-me-in-production-$(openssl rand -hex 32)
DOCSCOPE_DEBUG=false
DOCSCOPE_LOG_LEVEL=INFO

# URLs (using discovered ports)
DOCSCOPE_DATABASE_URL=postgresql://docscope:docscope-dev-password@postgres:5432/docscope
DOCSCOPE_REDIS_URL=redis://redis:6379/0

# CORS Configuration
DOCSCOPE_CORS_ORIGINS=http://localhost:${UI_PORT},http://localhost:${NGINX_HTTP_PORT}
EOF
    
    print_color $GREEN "✅ Environment file created: $CONFIG_FILE"
}

# Function to create docker-compose override
create_compose_override() {
    print_color $BLUE "\n🔧 Creating Docker Compose override..."
    
    cat > $COMPOSE_OVERRIDE << 'EOF'
# DocScope Docker Compose Override
# This file is automatically generated by install.sh
# It uses environment variables from .env.docker for port configuration

version: '3.8'

services:
  docscope:
    ports:
      - "${DOCSCOPE_API_PORT}:8000"
      - "${DOCSCOPE_UI_PORT}:8080"
    environment:
      - DOCSCOPE_DATABASE_URL=${DOCSCOPE_DATABASE_URL}
      - DOCSCOPE_REDIS_URL=${DOCSCOPE_REDIS_URL}
      - DOCSCOPE_SECRET_KEY=${DOCSCOPE_SECRET_KEY}
      - DOCSCOPE_CORS_ORIGINS=${DOCSCOPE_CORS_ORIGINS}
      - DOCSCOPE_LOG_LEVEL=${DOCSCOPE_LOG_LEVEL}

  postgres:
    ports:
      - "${DOCSCOPE_POSTGRES_PORT}:5432"
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

  redis:
    ports:
      - "${DOCSCOPE_REDIS_PORT}:6379"

  nginx:
    ports:
      - "${DOCSCOPE_NGINX_HTTP_PORT}:80"
      - "${DOCSCOPE_NGINX_HTTPS_PORT}:443"
EOF
    
    print_color $GREEN "✅ Docker Compose override created: $COMPOSE_OVERRIDE"
}

# Function to create start/stop scripts
create_management_scripts() {
    print_color $BLUE "\n📦 Creating management scripts..."
    
    # Create start script
    cat > start-docscope.sh << 'EOF'
#!/bin/bash
# Start DocScope with configured ports

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment
if [ -f .env.docker ]; then
    export $(cat .env.docker | grep -v '^#' | xargs)
    echo -e "${BLUE}Starting DocScope...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
    
    echo -e "\n${GREEN}✅ DocScope is starting!${NC}"
    echo ""
    echo "Access points:"
    echo "  • API:     http://localhost:${DOCSCOPE_API_PORT}"
    echo "  • Web UI:  http://localhost:${DOCSCOPE_UI_PORT}"
    echo "  • API Docs: http://localhost:${DOCSCOPE_API_PORT}/docs"
    echo "  • Metrics: http://localhost:${DOCSCOPE_METRICS_PORT}/metrics"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop:     ./stop-docscope.sh"
else
    echo "Error: .env.docker not found. Run ./install.sh first."
    exit 1
fi
EOF
    
    # Create stop script
    cat > stop-docscope.sh << 'EOF'
#!/bin/bash
# Stop DocScope

set -e

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}Stopping DocScope...${NC}"

if [ -f docker-compose.override.yml ]; then
    docker-compose -f docker-compose.yml -f docker-compose.override.yml down
else
    docker-compose down
fi

echo -e "${GREEN}✅ DocScope stopped${NC}"
EOF
    
    # Create status script
    cat > status-docscope.sh << 'EOF'
#!/bin/bash
# Check DocScope status

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}DocScope Service Status:${NC}"
echo "────────────────────────"

# Load environment for ports
if [ -f .env.docker ]; then
    export $(cat .env.docker | grep -v '^#' | xargs)
fi

# Check each service
check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if docker-compose ps | grep -q "${service}.*Up"; then
        echo -e "  $name: ${GREEN}✓ Running${NC} (port $port)"
    else
        echo -e "  $name: ${RED}✗ Stopped${NC}"
    fi
}

check_service "docscope" "${DOCSCOPE_API_PORT:-8000}" "API"
check_service "docscope" "${DOCSCOPE_UI_PORT:-8080}" "Web UI"
check_service "postgres" "${DOCSCOPE_POSTGRES_PORT:-5432}" "PostgreSQL"
check_service "redis" "${DOCSCOPE_REDIS_PORT:-6379}" "Redis"
check_service "nginx" "${DOCSCOPE_NGINX_HTTP_PORT:-80}" "Nginx"

echo ""
docker-compose ps
EOF
    
    # Make scripts executable
    chmod +x start-docscope.sh stop-docscope.sh status-docscope.sh
    
    print_color $GREEN "✅ Management scripts created:"
    echo "  • ./start-docscope.sh  - Start all services"
    echo "  • ./stop-docscope.sh   - Stop all services"
    echo "  • ./status-docscope.sh - Check service status"
}

# Function to check Docker installation
check_docker() {
    print_color $BLUE "🐳 Checking Docker installation..."
    
    if ! command -v docker >/dev/null 2>&1; then
        print_color $RED "❌ Docker is not installed"
        echo "Please install Docker from: https://www.docker.com/get-started"
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        # Try docker compose (v2)
        if docker compose version >/dev/null 2>&1; then
            print_color $YELLOW "⚠️  Using Docker Compose V2 (docker compose)"
            # Create alias for compatibility
            echo '#!/bin/bash' > /tmp/docker-compose
            echo 'docker compose "$@"' >> /tmp/docker-compose
            chmod +x /tmp/docker-compose
            export PATH="/tmp:$PATH"
        else
            print_color $RED "❌ Docker Compose is not installed"
            echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
            exit 1
        fi
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_color $RED "❌ Docker is not running"
        echo "Please start Docker Desktop or Docker service"
        exit 1
    fi
    
    print_color $GREEN "✅ Docker is installed and running"
}

# Function to display summary
display_summary() {
    print_color $MAGENTA "\n╔════════════════════════════════════════════╗"
    print_color $MAGENTA "║         DocScope Installation Summary       ║"
    print_color $MAGENTA "╚════════════════════════════════════════════╝"
    
    echo ""
    print_color $CYAN "📍 Access URLs:"
    echo "  • API:        http://localhost:${API_PORT}"
    echo "  • Web UI:     http://localhost:${UI_PORT}"
    echo "  • API Docs:   http://localhost:${API_PORT}/docs"
    echo "  • PostgreSQL: localhost:${POSTGRES_PORT}"
    echo "  • Redis:      localhost:${REDIS_PORT}"
    
    if [[ $NGINX_HTTP_PORT -ne 80 ]] || [[ $NGINX_HTTPS_PORT -ne 443 ]]; then
        echo "  • Nginx HTTP:  http://localhost:${NGINX_HTTP_PORT}"
        echo "  • Nginx HTTPS: https://localhost:${NGINX_HTTPS_PORT}"
    fi
    
    echo ""
    print_color $CYAN "📂 Configuration Files:"
    echo "  • Port configuration: $CONFIG_FILE"
    echo "  • Docker override:    $COMPOSE_OVERRIDE"
    
    echo ""
    print_color $CYAN "🎮 Management Commands:"
    echo "  • Start:  ./start-docscope.sh"
    echo "  • Stop:   ./stop-docscope.sh"
    echo "  • Status: ./status-docscope.sh"
    echo "  • Logs:   docker-compose logs -f"
    
    echo ""
    print_color $GREEN "✨ Installation complete!"
}

# Function to offer immediate start
offer_start() {
    echo ""
    read -p "$(print_color $YELLOW 'Would you like to start DocScope now? (y/n): ')" -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_color $BLUE "\n🚀 Starting DocScope..."
        ./start-docscope.sh
    else
        print_color $CYAN "\nTo start DocScope later, run: ./start-docscope.sh"
    fi
}

# Main installation flow
main() {
    clear
    print_color $MAGENTA "╔════════════════════════════════════════════╗"
    print_color $MAGENTA "║      DocScope Intelligent Installer         ║"
    print_color $MAGENTA "║         with Automatic Port Detection       ║"
    print_color $MAGENTA "╚════════════════════════════════════════════╝"
    echo ""
    
    # Check Docker
    check_docker
    echo ""
    
    # Detect available ports
    detect_available_ports
    echo ""
    
    # Ask for confirmation
    read -p "$(print_color $YELLOW 'Continue with these ports? (y/n): ')" -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_color $RED "Installation cancelled"
        exit 1
    fi
    
    # Create configuration files
    create_env_file
    create_compose_override
    create_management_scripts
    
    # Display summary
    display_summary
    
    # Offer to start
    offer_start
}

# Run main function
main "$@"