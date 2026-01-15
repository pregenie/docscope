"""Serve command implementation"""

import click
import webbrowser
import signal
import sys
from rich.console import Console
from rich.table import Table

from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command(name='serve')
@click.option('--host', '-h', default=None, help='Server host')
@click.option('--port', '-p', type=int, default=None, help='Server port')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--workers', '-w', type=int, default=None, help='Number of workers')
@click.option('--open-browser', '-o', is_flag=True, help='Open browser after starting')
@click.option('--production', is_flag=True, help='Run in production mode')
@click.option('--log-level', 
              type=click.Choice(['debug', 'info', 'warning', 'error']),
              default='info', help='Log level')
@click.pass_context
def serve_command(ctx, host, port, reload, workers, open_browser, production, log_level):
    """Start the DocScope web server
    
    Starts the REST API server and web interface for DocScope.
    The server provides both API endpoints and a web UI for browsing
    and searching documentation.
    """
    config = ctx.obj.config
    
    # Use config values as defaults
    host = host or config.server.host or "0.0.0.0"
    port = port or config.server.port or 8080
    workers = workers or config.server.workers or 1
    
    # In production mode, disable reload and set appropriate defaults
    if production:
        reload = False
        if workers == 1:
            workers = 4
        log_level = 'error' if log_level == 'info' else log_level
    
    # Display server configuration
    console.print("\n[bold blue]Server Configuration[/bold blue]")
    
    config_table = Table(show_header=False, box=None)
    config_table.add_column(style="cyan")
    config_table.add_column()
    
    config_table.add_row("Host:", host)
    config_table.add_row("Port:", str(port))
    config_table.add_row("Workers:", str(workers))
    config_table.add_row("Auto-reload:", "Yes" if reload else "No")
    config_table.add_row("Mode:", "Production" if production else "Development")
    config_table.add_row("Log level:", log_level)
    config_table.add_row("API URL:", f"http://{host}:{port}/api/v1")
    config_table.add_row("Docs URL:", f"http://{host}:{port}/api/docs" if not production else "Disabled")
    
    console.print(config_table)
    console.print()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        console.print("\n[yellow]Shutting down server...[/yellow]")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Import server module
        from ...server import run_server
        
        # Open browser if requested
        if open_browser:
            url = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}"
            console.print(f"[blue]Opening browser at {url}[/blue]")
            webbrowser.open(url)
        
        # Start server
        console.print("[green]Starting DocScope server...[/green]")
        console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")
        
        run_server(
            host=host,
            port=port,
            reload=reload,
            workers=workers
        )
        
    except ImportError as e:
        console.print(f"[red]Failed to import server module: {e}[/red]")
        console.print("[yellow]Make sure FastAPI and Uvicorn are installed:[/yellow]")
        console.print("  pip install fastapi uvicorn")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Server failed: {e}")
        console.print(f"\n[red]Server failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)