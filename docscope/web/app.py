"""Web UI Application for DocScope"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..core.logging import get_logger

logger = get_logger(__name__)


def create_web_app() -> FastAPI:
    """Create standalone web application"""
    app = FastAPI(
        title="DocScope Web UI",
        description="Web interface for DocScope documentation system",
        version="1.0.0"
    )
    
    # Get static files directory
    static_dir = Path(__file__).parent / "static"
    templates_dir = Path(__file__).parent / "templates"
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Setup templates if directory exists
    templates = None
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
    
    @app.get("/")
    async def root():
        """Serve the main index.html"""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return HTMLResponse(
                content="<h1>DocScope Web UI</h1><p>Index file not found</p>",
                status_code=404
            )
    
    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon"""
        favicon_file = static_dir / "favicon.ico"
        if favicon_file.exists():
            return FileResponse(str(favicon_file))
        return FileResponse(str(static_dir / "favicon.svg"))
    
    return app


def mount_web_ui(app: FastAPI) -> None:
    """Mount web UI to existing FastAPI application"""
    
    # Get static files directory
    static_dir = Path(__file__).parent / "static"
    
    if not static_dir.exists():
        logger.warning(f"Static directory not found: {static_dir}")
        return
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Add root route if not exists
    @app.get("/", include_in_schema=False)
    async def web_ui_root():
        """Serve the web UI"""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return HTMLResponse(
                content="""
                <html>
                <head>
                    <title>DocScope</title>
                    <style>
                        body {
                            font-family: system-ui, sans-serif;
                            max-width: 800px;
                            margin: 50px auto;
                            padding: 20px;
                        }
                        h1 { color: #0066cc; }
                        .links {
                            margin: 30px 0;
                            display: flex;
                            gap: 20px;
                        }
                        a {
                            color: #0066cc;
                            text-decoration: none;
                            padding: 10px 20px;
                            border: 2px solid #0066cc;
                            border-radius: 5px;
                            transition: all 0.3s;
                        }
                        a:hover {
                            background: #0066cc;
                            color: white;
                        }
                    </style>
                </head>
                <body>
                    <h1>DocScope API Server</h1>
                    <p>Universal Documentation Browser & Search System</p>
                    <div class="links">
                        <a href="/api/docs">API Documentation</a>
                        <a href="/api/v1/health">Health Status</a>
                    </div>
                    <h2>Quick Start</h2>
                    <pre>
# Search documents
curl -X POST http://localhost:8080/api/v1/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "your search term"}'

# List documents  
curl http://localhost:8080/api/v1/documents

# Get statistics
curl http://localhost:8080/api/v1/health/stats
                    </pre>
                </body>
                </html>
                """,
                status_code=200
            )
    
    logger.info("Web UI mounted successfully")