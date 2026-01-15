# DocScope - Universal Documentation Browser & Search System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue)](https://kubernetes.io/)

## 📚 Overview

DocScope is a powerful, enterprise-ready documentation management system that provides intelligent document scanning, indexing, and search capabilities. It supports multiple document formats, offers a RESTful API, CLI interface, and web UI, making it the perfect solution for organizations looking to centralize and search through their documentation efficiently.

### ✨ Key Features

- **Multi-Format Support**: Scan and index Markdown, HTML, JSON, YAML, Python, and more
- **Full-Text Search**: Advanced search with Whoosh integration, faceting, and suggestions
- **RESTful API**: Complete API with FastAPI, WebSocket support, and auto-documentation
- **CLI Interface**: Rich terminal UI with comprehensive commands
- **Web Interface**: Modern SPA with real-time updates and responsive design
- **Plugin System**: Extensible architecture with hooks and custom plugins
- **Production Ready**: Docker, Kubernetes, monitoring, and security best practices
- **Export Capabilities**: Export documents in JSON, YAML, Markdown, HTML, PDF, and CSV
- **File Watching**: Auto-index documents on file system changes
- **Performance Monitoring**: Built-in metrics and health checks

## 🚀 Quick Start

### Intelligent Installation (Recommended)

DocScope includes an intelligent installer that automatically detects available ports to avoid conflicts:

```bash
# Clone the repository
git clone https://github.com/pregenie/docscope.git
cd docscope

# Run the intelligent installer
chmod +x install.sh
./install.sh

# The installer will:
# ✅ Detect available ports automatically
# ✅ Configure Docker Compose
# ✅ Create management scripts
# ✅ Offer to start services immediately
```

**The installer automatically finds free ports and shows you:**
```
Service          Default Port  →  Available Port
─────────────────────────────────────────────────
API              8000         →  8000     ✓
Web UI           8080         →  8080     ✓  
PostgreSQL       5432         →  5433     ↻
Redis            6379         →  6379     ✓
HTTP             80           →  8081     ↻
HTTPS            443          →  8443     ↻
```

### Manual Docker Setup (Alternative)

```bash
# Clone the repository
git clone https://github.com/pregenie/docscope.git
cd docscope

# Start with default ports (may cause conflicts)
docker-compose up -d
```

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize the database
python -m docscope.cli init

# Start scanning documents
python -m docscope.cli scan /path/to/docs

# Run the server
python -m docscope.cli serve
```

## 📖 Documentation

### CLI Usage

```bash
# Scan documents
docscope scan /path/to/documents --recursive --format markdown

# Search documents
docscope search "query" --limit 10 --format json

# List all documents
docscope list --category technical --format table

# Export documents
docscope export --format pdf --output export.pdf

# Start file watcher
docscope watch /path/to/documents --auto-index

# View statistics
docscope stats
```

### API Usage

```python
import requests

# Search documents
response = requests.get("http://localhost:8000/api/search", 
    params={"q": "docker", "limit": 10})
results = response.json()

# Get document by ID
response = requests.get("http://localhost:8000/api/documents/123")
document = response.json()

# Create a new document
response = requests.post("http://localhost:8000/api/documents",
    json={"title": "New Doc", "content": "..."})
```

## 🎮 Service Management

After installation, DocScope provides convenient management scripts:

```bash
# Start all services
./start-docscope.sh

# Stop all services  
./stop-docscope.sh

# Check service status
./status-docscope.sh

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f docscope
docker-compose logs -f postgres
```

### Dynamic Port Access

Your DocScope instance runs on automatically detected ports:

```bash
# Check your configured ports
cat .env.docker

# Example output shows your specific ports:
# DOCSCOPE_API_PORT=8000
# DOCSCOPE_UI_PORT=8080  
# DOCSCOPE_POSTGRES_PORT=5433  # Changed due to conflict
```

**Access your instance:**
- **Web UI**: `http://localhost:{YOUR_UI_PORT}`
- **API**: `http://localhost:{YOUR_API_PORT}`
- **API Docs**: `http://localhost:{YOUR_API_PORT}/docs`

### Port Conflict Resolution

If the installer detects port conflicts, it will:
1. 🔍 **Scan** for the next available port
2. ⚙️ **Configure** Docker Compose automatically  
3. 📋 **Display** which services caused conflicts
4. ✅ **Start** with guaranteed available ports

## 🏗️ Architecture

```
DocScope/
├── docscope/              # Main application package
│   ├── core/              # Core models and configuration
│   ├── scanner/           # Document scanning module
│   ├── storage/           # Database and storage layer
│   ├── search/            # Search engine integration
│   ├── api/               # REST API implementation
│   ├── cli/               # CLI commands
│   ├── ui/                # Web interface
│   ├── plugins/           # Plugin system
│   └── features/          # Advanced features
├── tests/                 # Test suite
├── kubernetes/            # K8s manifests
└── scripts/               # Deployment scripts
```

## 🐳 Docker Deployment

### Intelligent Installation (Recommended)

The intelligent installer handles all port conflicts automatically:

```bash
# One-command installation with port detection
./install.sh

# This creates:
# ✅ .env.docker - Environment with detected ports
# ✅ docker-compose.override.yml - Port mappings
# ✅ Management scripts (start/stop/status)
```

### Manual Docker Build

```bash
# Build custom image
docker build -t docscope:latest .

# Run with custom configuration
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  docscope:latest
```

### Production Deployment

```bash
# Production deployment with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or use Kubernetes
kubectl apply -f kubernetes/
```

### Troubleshooting Port Conflicts

If you encounter port conflicts:

1. **Use the installer**: `./install.sh` (recommended)
2. **Manual override**: Edit `docker-compose.override.yml`
3. **Check what's using ports**:
   ```bash
   # On macOS/Linux
   lsof -i :8000
   
   # On Windows
   netstat -ano | findstr :8000
   ```

### Environment Variables

The installer creates `.env.docker` with discovered ports:

```bash
# View your configuration
cat .env.docker

# Key variables:
DOCSCOPE_API_PORT=8000      # API server port
DOCSCOPE_UI_PORT=8080       # Web UI port
DOCSCOPE_POSTGRES_PORT=5432 # Database port
DOCSCOPE_REDIS_PORT=6379    # Cache port
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**DocScope** - *Making documentation discoverable*