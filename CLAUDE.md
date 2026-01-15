# DocScope - Universal Documentation Browser & Search System

## Project Overview
DocScope is a standalone, enterprise-ready documentation browser and search system designed to provide scalable, performant documentation management across multiple formats and sources.

## Project Structure
```
docscope/
├── docscope/          # Core Python package
│   ├── scanner.py     # Multi-threaded document scanner
│   ├── search.py      # Full-text search engine
│   ├── storage.py     # Storage abstraction layer
│   ├── server.py      # FastAPI REST API server
│   └── plugins.py     # Plugin system architecture
├── web/              # Web UI components
├── cli/              # Command-line interface
├── tests/            # Test suite
├── docs/             # Documentation
└── .docscope.yaml    # Configuration file
```

## Key Technologies
- **Backend**: Python 3.10+, FastAPI
- **Search**: Whoosh/Elasticsearch/SQLite FTS
- **Database**: SQLite/PostgreSQL/MongoDB
- **Frontend**: Web UI with real-time WebSocket updates
- **Formats**: Markdown, PDF, Office docs, Notebooks, Code files

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install with extras
pip install -e ".[ai,ocr,enterprise]"
```

### Running
```bash
# Initialize project
docscope init --name "My Docs"

# Scan documentation
docscope scan ./docs --recursive --formats md,pdf,html

# Start server
docscope serve --port 8080 --host 0.0.0.0

# Run tests
pytest tests/

# Linting
ruff check .
mypy docscope/
```

### Docker
```bash
# Build image
docker build -t docscope .

# Run container
docker-compose up -d
```

## Core Components

### Scanner Engine
- Multi-threaded document scanning
- Support for 20+ document formats
- Incremental updates for modified files
- Format detection and metadata extraction

### Search Engine
- Full-text search with advanced queries
- Boolean, phrase, wildcard, regex support
- TF-IDF/BM25 ranking algorithms
- Real-time search suggestions

### Storage Layer
- Abstracted backend (SQLite, PostgreSQL, MongoDB)
- Document versioning
- Efficient caching with Redis
- Content deduplication

### API Server
- RESTful API with FastAPI
- WebSocket for real-time updates
- OpenAPI documentation
- Rate limiting and CORS support

### Plugin System
- Custom format parsers
- Content processors
- AI enrichment plugins
- Third-party integrations

## Configuration
Main configuration in `.docscope.yaml`:
- Scanner paths and ignore patterns
- Search engine settings
- Storage backend configuration
- Server settings (host, port, auth)
- AI features toggle
- Plugin management

## Key Features
- **10x faster search** than file-based systems
- **Real-time indexing** with file watching
- **AI-powered features** for intelligent categorization
- **Multi-format support** including PDF, Office, notebooks
- **Enterprise features**: Auth, permissions, audit trails
- **Extensible** via plugin system

## Performance Targets
- Indexing: 1000 docs/second
- Search latency: <100ms (95th percentile)
- Memory: <500MB base footprint
- Concurrent users: 1000+

## Security
- Authentication: JWT, OAuth 2.0, SAML
- Encryption: AES-256 at rest, TLS 1.3 in transit
- Compliance: GDPR, HIPAA ready
- Audit logging for all access

## Testing Strategy
- Unit tests for core components
- Integration tests for API endpoints
- Performance benchmarks
- Security testing
- Plugin compatibility tests

## Development Phases
1. **Foundation**: Core scanner, search, storage, API
2. **Enhanced Features**: Plugins, advanced search, WebSocket
3. **Intelligence Layer**: AI features, smart categorization
4. **Enterprise Ready**: Auth, permissions, high availability

## Contributing
- Follow existing code patterns and conventions
- Use type hints and docstrings
- Write tests for new features
- Update documentation
- Run linting before commits