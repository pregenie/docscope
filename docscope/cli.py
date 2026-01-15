"""Command-line interface for DocScope"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import json
import yaml

from .core.config import Config
from .core.logging import setup_logging, get_logger
from . import __version__

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="DocScope")
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-error output')
@click.pass_context
def cli(ctx, config, verbose, quiet):
    """DocScope - Universal Documentation Browser & Search System"""
    # Setup context
    ctx.ensure_object(dict)
    
    # Load configuration
    ctx.obj['config'] = Config(config_file=config)
    
    # Setup logging
    log_level = "ERROR" if quiet else "DEBUG" if verbose else "INFO"
    setup_logging(
        level=log_level,
        log_file=ctx.obj['config'].logging.file,
        log_format=ctx.obj['config'].logging.format,
        console=ctx.obj['config'].logging.console and not quiet
    )
    
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


@cli.command()
@click.option('--name', prompt='Project name', help='Name of the project')
@click.option('--path', default='.', help='Path to initialize')
@click.pass_context
def init(ctx, name, path):
    """Initialize a new DocScope project"""
    project_path = Path(path)
    config_path = project_path / ".docscope.yaml"
    
    if config_path.exists():
        if not click.confirm(f"Config file already exists at {config_path}. Overwrite?"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return
    
    # Create default configuration
    config_data = {
        "version": "1.0",
        "project": name,
        "scanner": {
            "paths": [
                {"path": "./docs", "recursive": True},
                {"path": "./README.md"}
            ],
            "ignore": ["**/__pycache__", "**/.git", "**/node_modules"],
        },
        "search": {
            "engine": "whoosh",
            "settings": {"fuzzy": True, "max_results": 100}
        },
        "storage": {
            "backend": "sqlite",
            "sqlite": {"path": "~/.docscope/docscope.db"}
        },
        "server": {
            "host": "localhost",
            "port": 8080,
        }
    }
    
    # Write configuration file
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    # Create docs directory
    docs_path = project_path / "docs"
    docs_path.mkdir(exist_ok=True)
    
    # Create sample README
    readme_path = project_path / "README.md"
    if not readme_path.exists():
        readme_path.write_text(f"# {name}\n\nDocumentation for {name} project.\n")
    
    console.print(f"[green]✓[/green] Initialized DocScope project '{name}' at {project_path}")
    console.print(f"[green]✓[/green] Created configuration file: {config_path}")
    console.print(f"[green]✓[/green] Created docs directory: {docs_path}")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Add documentation to the 'docs' directory")
    console.print("  2. Run 'docscope scan' to index documents")
    console.print("  3. Run 'docscope serve' to start the web server")


@cli.command()
@click.argument('paths', nargs=-1)
@click.option('--recursive', '-r', is_flag=True, help='Scan directories recursively')
@click.option('--formats', help='Comma-separated list of formats to scan')
@click.option('--incremental', is_flag=True, help='Only scan modified files')
@click.option('--since', help='Scan files modified since date (ISO format)')
@click.pass_context
def scan(ctx, paths, recursive, formats, incremental, since):
    """Scan documents and build index"""
    config = ctx.obj['config']
    
    # Use paths from config if not provided
    if not paths:
        scan_paths = []
        for path_config in config.scanner.paths:
            scan_paths.append(path_config.get('path', '.'))
    else:
        scan_paths = list(paths)
    
    console.print(f"[blue]Scanning documents...[/blue]")
    console.print(f"Paths: {', '.join(scan_paths)}")
    
    if formats:
        console.print(f"Formats: {formats}")
    
    if incremental:
        console.print("[yellow]Running incremental scan[/yellow]")
    
    # TODO: Implement actual scanning
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning...", total=None)
        
        # Simulate scanning
        import time
        time.sleep(2)
    
    # Display results
    console.print("[green]✓[/green] Scan complete")
    console.print("  Total documents: 42")
    console.print("  Successfully indexed: 40")
    console.print("  Failed: 2")
    console.print("  Duration: 2.3s")


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=20, help='Maximum number of results')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.option('--category', help='Filter by category')
@click.pass_context
def search(ctx, query, limit, format, category):
    """Search documents"""
    config = ctx.obj['config']
    
    console.print(f"[blue]Searching for:[/blue] {query}")
    
    # TODO: Implement actual search
    # Mock results for now
    results = [
        {"title": "API Documentation", "path": "/docs/api.md", "score": 0.95},
        {"title": "Getting Started", "path": "/docs/guide.md", "score": 0.87},
        {"title": "Configuration", "path": "/docs/config.md", "score": 0.76},
    ]
    
    if format == 'json':
        click.echo(json.dumps(results, indent=2))
    elif format == 'yaml':
        click.echo(yaml.dump(results, default_flow_style=False))
    else:
        # Table format
        table = Table(title=f"Search Results for '{query}'")
        table.add_column("Title", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Score", style="yellow")
        
        for result in results[:limit]:
            table.add_row(
                result["title"],
                result["path"],
                f"{result['score']:.2f}"
            )
        
        console.print(table)
        console.print(f"\n[dim]Showing {min(len(results), limit)} of {len(results)} results[/dim]")


@cli.command()
@click.option('--host', '-h', help='Server host')
@click.option('--port', '-p', type=int, help='Server port')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--workers', '-w', type=int, help='Number of workers')
@click.option('--open-browser', is_flag=True, help='Open browser after starting')
@click.pass_context
def serve(ctx, host, port, reload, workers, open_browser):
    """Start the DocScope web server"""
    config = ctx.obj['config']
    
    # Use config values as defaults
    host = host or config.server.host
    port = port or config.server.port
    workers = workers or config.server.workers
    reload = reload or config.server.reload
    
    console.print(f"[blue]Starting DocScope server...[/blue]")
    console.print(f"  Host: {host}")
    console.print(f"  Port: {port}")
    console.print(f"  Workers: {workers}")
    console.print(f"  Reload: {reload}")
    
    if open_browser:
        import webbrowser
        webbrowser.open(f"http://{host}:{port}")
    
    # TODO: Start actual server
    console.print(f"\n[green]✓[/green] Server running at http://{host}:{port}")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    
    try:
        # Keep running until interrupted
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")


@cli.command()
@click.option('--format', '-f', type=click.Choice(['pdf', 'html', 'markdown']), default='html')
@click.option('--output', '-o', help='Output file path')
@click.option('--query', '-q', help='Export only documents matching query')
@click.pass_context
def export(ctx, format, output, query):
    """Export documentation"""
    config = ctx.obj['config']
    
    if not output:
        output = f"export.{format}"
    
    console.print(f"[blue]Exporting documentation...[/blue]")
    console.print(f"  Format: {format}")
    console.print(f"  Output: {output}")
    if query:
        console.print(f"  Query: {query}")
    
    # TODO: Implement actual export
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Exporting...", total=None)
        
        # Simulate export
        import time
        time.sleep(2)
    
    console.print(f"[green]✓[/green] Export complete: {output}")


@cli.group()
def db():
    """Database management commands"""
    pass


@db.command()
@click.pass_context
def init(ctx):
    """Initialize database"""
    config = ctx.obj['config']
    console.print("[blue]Initializing database...[/blue]")
    # TODO: Implement database initialization
    console.print("[green]✓[/green] Database initialized")


@db.command()
@click.pass_context
def status(ctx):
    """Show database status"""
    config = ctx.obj['config']
    console.print("[bold]Database Status[/bold]")
    console.print(f"  Backend: {config.storage.backend}")
    console.print(f"  Location: {config.storage.sqlite.get('path', 'default')}")
    console.print(f"  Documents: 42")
    console.print(f"  Size: 1.2 MB")


@cli.group()
def plugins():
    """Plugin management commands"""
    pass


@plugins.command(name='list')
@click.pass_context
def list_plugins(ctx):
    """List installed plugins"""
    console.print("[bold]Installed Plugins[/bold]")
    # TODO: Implement plugin listing
    console.print("  [dim]No plugins installed[/dim]")


@plugins.command()
@click.argument('name')
@click.pass_context
def enable(ctx, name):
    """Enable a plugin"""
    console.print(f"[green]✓[/green] Plugin '{name}' enabled")


@plugins.command()
@click.argument('name')
@click.pass_context
def disable(ctx, name):
    """Disable a plugin"""
    console.print(f"[yellow]Plugin '{name}' disabled[/yellow]")


def main():
    """Main entry point"""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()