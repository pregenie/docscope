# DocScope Installation Guide

## 🎯 Overview

DocScope provides multiple installation methods to suit different environments and use cases. The **Intelligent Installer** is recommended for most users as it automatically handles port conflicts and configuration.

## 🚀 Quick Installation (Recommended)

### Prerequisites

- Docker and Docker Compose installed
- Git
- 2GB RAM available
- 1GB disk space

### One-Command Installation

```bash
git clone https://github.com/pregenie/docscope.git
cd docscope
chmod +x install.sh
./install.sh
```

**The installer will:**
1. ✅ Check Docker installation
2. 🔍 Detect available ports automatically  
3. ⚙️ Create configuration files
4. 📦 Generate management scripts
5. 🚀 Optionally start services immediately

## 📋 What the Installer Does

### Port Detection

The intelligent installer scans for available ports to avoid conflicts:

```
🔍 Detecting available ports...

Service          Default Port  →  Available Port
─────────────────────────────────────────────────
API              8000         →  8000     ✓
Web UI           8080         →  8080     ✓  
PostgreSQL       5432         →  5433     ↻
Redis            6379         →  6379     ✓
HTTP             80           →  8081     ↻
HTTPS            443          →  8443     ↻
```

**Legend:**
- ✓ = Port available (using default)
- ↻ = Port conflict detected (using alternative)

### Generated Files

The installer creates several configuration files:

1. **`.env.docker`** - Environment variables with detected ports
2. **`docker-compose.override.yml`** - Port mappings for Docker Compose
3. **`start-docscope.sh`** - Start all services
4. **`stop-docscope.sh`** - Stop all services  
5. **`status-docscope.sh`** - Check service status

### Conflicting Services Detection

If ports are already in use, the installer shows what's using them:

```
📋 Conflicting services:
  Port 5432 (PostgreSQL): used by postgres
  Port 80 (HTTP): used by httpd
```

## 🎮 Service Management

After installation, use the generated management scripts:

### Starting Services

```bash
# Start all services
./start-docscope.sh

# Output:
# Starting DocScope...
# ✅ DocScope is starting!
#
# Access points:
#   • API:     http://localhost:8000
#   • Web UI:  http://localhost:8080
#   • API Docs: http://localhost:8000/docs
```

### Stopping Services

```bash
# Stop all services
./stop-docscope.sh

# Output:
# Stopping DocScope...
# ✅ DocScope stopped
```

### Checking Status

```bash
# Check service status
./status-docscope.sh

# Output:
# DocScope Service Status:
# ────────────────────────
#   API: ✓ Running (port 8000)
#   Web UI: ✓ Running (port 8080)
#   PostgreSQL: ✓ Running (port 5433)
#   Redis: ✓ Running (port 6379)
#   Nginx: ✓ Running (port 8081)
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f docscope
docker-compose logs -f postgres
docker-compose logs -f redis
```

## 🔧 Manual Installation

### Method 1: Standard Docker Compose

```bash
git clone https://github.com/pregenie/docscope.git
cd docscope

# Start with default ports (may conflict)
docker-compose up -d

# Access at default URLs:
# API: http://localhost:8000
# UI: http://localhost:8080
```

### Method 2: Custom Port Configuration

```bash
# Create custom environment file
cat > .env.local << EOF
DOCSCOPE_API_PORT=8100
DOCSCOPE_UI_PORT=8101
DOCSCOPE_POSTGRES_PORT=5433
DOCSCOPE_REDIS_PORT=6380
EOF

# Create override file
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  docscope:
    ports:
      - "\${DOCSCOPE_API_PORT}:8000"
      - "\${DOCSCOPE_UI_PORT}:8080"
  postgres:
    ports:
      - "\${DOCSCOPE_POSTGRES_PORT}:5432"
  redis:
    ports:
      - "\${DOCSCOPE_REDIS_PORT}:6379"
EOF

# Start with custom configuration
docker-compose --env-file .env.local up -d
```

## 🐳 Docker-Only Installation

### Single Container

```bash
# Build image
docker build -t docscope .

# Run with volume mapping
docker run -d \
  --name docscope \
  -p 8000:8000 \
  -p 8080:8080 \
  -v docscope-data:/data \
  -e DOCSCOPE_DATABASE_URL=sqlite:///data/docscope.db \
  docscope
```

### With External Database

```bash
# Start PostgreSQL
docker run -d \
  --name docscope-postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=docscope \
  -e POSTGRES_USER=docscope \
  -e POSTGRES_PASSWORD=password \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:15

# Start DocScope
docker run -d \
  --name docscope-app \
  -p 8000:8000 \
  -p 8080:8080 \
  --link docscope-postgres:postgres \
  -e DOCSCOPE_DATABASE_URL=postgresql://docscope:password@postgres:5432/docscope \
  docscope
```

## 💻 Local Development Setup

### Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup database
export DOCSCOPE_DATABASE_URL=sqlite:///docscope.db
python -c "from docscope.storage import init_database; init_database()"

# Start development server
python -m docscope.cli serve --reload
```

### Database Setup

```bash
# PostgreSQL (recommended for production)
createdb docscope
export DOCSCOPE_DATABASE_URL=postgresql://user:password@localhost/docscope

# SQLite (development)
export DOCSCOPE_DATABASE_URL=sqlite:///docscope.db

# Initialize database
python -c "from docscope.storage import init_database; init_database()"
```

## 🚨 Troubleshooting

### Port Conflicts

**Problem**: Services fail to start due to port conflicts

**Solution 1** (Recommended): Use the intelligent installer
```bash
./install.sh
```

**Solution 2**: Check what's using the port
```bash
# macOS/Linux
lsof -i :8000
sudo lsof -i :80

# Windows
netstat -ano | findstr :8000
```

**Solution 3**: Use different ports manually
```bash
# Edit docker-compose.override.yml or .env.docker
DOCSCOPE_API_PORT=8100
DOCSCOPE_UI_PORT=8101
```

### Docker Issues

**Problem**: Docker not running
```bash
# Check Docker status
docker info

# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker
```

**Problem**: Permission denied
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Then log out and back in
```

### Memory Issues

**Problem**: Services crash due to insufficient memory

**Solution**: Ensure at least 2GB RAM available
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Increase Docker Desktop memory allocation
# Docker Desktop → Settings → Resources → Memory
```

### Database Connection Issues

**Problem**: Cannot connect to database

**Solution 1**: Check PostgreSQL is running
```bash
docker-compose ps postgres
docker-compose logs postgres
```

**Solution 2**: Verify connection string
```bash
cat .env.docker | grep DATABASE_URL
```

### Network Issues

**Problem**: Cannot access web interface

**Solution 1**: Check service is running
```bash
./status-docscope.sh
docker-compose ps
```

**Solution 2**: Verify port mapping
```bash
cat .env.docker | grep PORT
```

**Solution 3**: Check firewall/security software

## 🔐 Security Considerations

### Development vs Production

**Development** (default):
- SQLite database
- Simple passwords
- HTTP only
- Debug mode enabled

**Production** (recommended changes):
- PostgreSQL database
- Strong passwords/secrets
- HTTPS with certificates
- Debug mode disabled
- Resource limits set

### Securing the Installation

```bash
# Change default passwords
sed -i 's/docscope-dev-password/your-strong-password/g' .env.docker

# Generate secure secret key
openssl rand -hex 32

# Use environment variables for secrets
export DOCSCOPE_SECRET_KEY="your-secret-key"
export POSTGRES_PASSWORD="your-db-password"
```

## 📊 Verification

After installation, verify DocScope is working:

### Health Check

```bash
# Check API health
curl http://localhost:${DOCSCOPE_API_PORT}/health

# Expected response:
{"status": "healthy", "timestamp": "..."}
```

### Web Interface

1. Open browser to `http://localhost:${DOCSCOPE_UI_PORT}`
2. Should see DocScope dashboard
3. Try searching (should work even with no documents)

### API Documentation

1. Open `http://localhost:${DOCSCOPE_API_PORT}/docs`
2. Interactive API documentation should load
3. Try the `/health` endpoint

### Service Status

```bash
./status-docscope.sh

# All services should show "Running"
```

## 🎯 Next Steps

After successful installation:

1. **Add documents**: `python -m docscope.cli scan /path/to/docs`
2. **Configure plugins**: Edit plugin configuration
3. **Set up monitoring**: Configure health checks
4. **Backup strategy**: Set up automated backups
5. **SSL certificates**: Configure HTTPS for production

---

For more help, see:
- [README.md](README.md) - Project overview
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [GitHub Issues](https://github.com/pregenie/docscope/issues) - Report bugs