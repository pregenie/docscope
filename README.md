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

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/docscope.git
cd docscope

# Start all services
docker-compose up -d

# Access the application
# API: http://localhost:8000
# Web UI: http://localhost:8080
# API Docs: http://localhost:8000/docs
```

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize the database
python -m docscope init

# Start scanning documents
python -m docscope scan /path/to/docs

# Run the server
python -m docscope serve
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

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**DocScope** - *Making documentation discoverable*