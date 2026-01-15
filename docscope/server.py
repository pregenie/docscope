"""DocScope API Server entry point"""

import uvicorn
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docscope.api.app import app
from docscope.api.config import get_settings
from docscope.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def run_server(
    host: str = None,
    port: int = None,
    reload: bool = None,
    workers: int = None
):
    """Run the DocScope API server"""
    
    # Use provided values or defaults from settings
    host = host or settings.host
    port = port or settings.port
    reload = reload if reload is not None else settings.debug
    workers = workers or settings.workers
    
    logger.info(f"Starting DocScope API server on {host}:{port}")
    
    if reload:
        # Development mode with auto-reload
        uvicorn.run(
            "docscope.api.app:app",
            host=host,
            port=port,
            reload=True,
            log_level="info",
            access_log=True
        )
    else:
        # Production mode
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers,
            log_level="info" if settings.debug else "error",
            access_log=settings.debug
        )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DocScope API Server")
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development mode)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes"
    )
    
    args = parser.parse_args()
    
    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )