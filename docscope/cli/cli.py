"""Enhanced Command-line interface for DocScope"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..core.config import Config
from ..core.logging import setup_logging, get_logger
from .. import __version__

# Import commands
from .commands import (
    scan_command,
    search_command,
    serve_command,
    export_command,
    db_group,
    plugins_group,
    watch_command,
    stats_command,
    config_group
)

console = Console()
logger = get_logger(__name__)


class DocScopeContext:
    """Context object for DocScope CLI"""
    
    def __init__(self):
        self.config = None
        self.verbose = False
        self.quiet = False
        self.debug = False


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(version=__version__, prog_name="DocScope")
@click.option('--config', '-c', type=click.Path(), 
              help='Path to configuration file', 
              envvar='DOCSCOPE_CONFIG')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-error output')
@click.option('--debug', is_flag=True, help='Enable debug mode', hidden=True)
@click.option('--no-color', is_flag=True, help='Disable colored output')
@click.pass_context
def cli(ctx, config, verbose, quiet, debug, no_color):
    """DocScope - Universal Documentation Browser & Search System
    
    A powerful tool for indexing, searching, and managing documentation
    across multiple formats and sources.
    
    Examples:
    
    \b
    # Initialize a new project
    docscope init --name "My Project"
    
    \b
    # Scan documents
    docscope scan /path/to/docs --recursive
    
    \b
    # Search for content
    docscope search "api authentication"
    
    \b
    # Start the web server
    docscope serve --open-browser
    
    For more information, visit: https://github.com/docscope/docscope
    """
    # Create context object
    ctx.obj = DocScopeContext()
    
    # Handle color output
    if no_color:
        console._force_terminal = False
    
    # Find and load configuration
    config_file = None
    if config:
        config_file = Path(config)
    else:
        # Search for configuration file
        search_paths = [
            Path.cwd() / ".docscope.yaml",
            Path.cwd() / "docscope.yaml",
            Path.home() / ".config" / "docscope" / "config.yaml",
            Path.home() / ".docscope" / "config.yaml"
        ]
        
        for path in search_paths:
            if path.exists():
                config_file = path
                break
    
    # Load configuration
    try:
        ctx.obj.config = Config(config_file=config_file)
    except Exception as e:
        if debug:
            raise
        # Use default configuration
        ctx.obj.config = Config()
    
    # Setup logging
    log_level = "DEBUG" if (debug or verbose) else "ERROR" if quiet else "INFO"
    setup_logging(
        level=log_level,
        log_file=ctx.obj.config.logging.file if ctx.obj.config.logging else None,
        console=not quiet
    )
    
    # Store flags in context
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet
    ctx.obj.debug = debug


@cli.command()
@click.option('--name', prompt='Project name', help='Name of the project')
@click.option('--path', default='.', type=click.Path(), help='Path to initialize')
@click.option('--template', type=click.Choice(['basic', 'full', 'minimal']), 
              default='basic', help='Configuration template to use')
@click.pass_context
def init(ctx, name, path, template):
    """Initialize a new DocScope project
    
    Create a new DocScope project with configuration file and
    directory structure.
    """
    project_path = Path(path).resolve()
    config_path = project_path / ".docscope.yaml"
    
    # Check if already initialized
    if config_path.exists():
        if not click.confirm(f"Configuration already exists at {config_path}. Overwrite?"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return
    
    console.print(f"\n[bold blue]Initializing DocScope project: {name}[/bold blue]")
    
    # Create project structure
    docs_path = project_path / "docs"
    docs_path.mkdir(exist_ok=True)
    
    # Configuration templates
    templates = {
        'minimal': {
            "version": "1.0",
            "project": name,
            "scanner": {
                "paths": ["./docs"]
            }
        },
        'basic': {
            "version": "1.0",
            "project": name,
            "scanner": {
                "paths": [
                    {"path": "./docs", "recursive": True},
                    {"path": "./README.md"}
                ],
                "ignore": ["**/__pycache__", "**/.git", "**/node_modules"],
                "formats": ["markdown", "text", "yaml", "json"]
            },
            "search": {
                "engine": "whoosh",
                "settings": {
                    "fuzzy": True,
                    "max_results": 100
                }
            },
            "storage": {
                "backend": "sqlite",
                "sqlite": {
                    "path": "./.docscope/docscope.db"
                }
            },
            "server": {
                "host": "localhost",
                "port": 8080
            }
        },
        'full': {
            "version": "1.0",
            "project": name,
            "description": f"Documentation for {name}",
            "scanner": {
                "paths": [
                    {"path": "./docs", "recursive": True},
                    {"path": "./README.md"},
                    {"path": "./examples", "recursive": True}
                ],
                "ignore": [
                    "**/__pycache__", "**/.git", "**/node_modules",
                    "**/*.pyc", "**/.DS_Store", "**/build", "**/dist"
                ],
                "formats": ["markdown", "text", "yaml", "json", "html", "code"],
                "workers": 4,
                "follow_symlinks": False
            },
            "search": {
                "engine": "whoosh",
                "settings": {
                    "fuzzy": True,
                    "fuzzy_distance": 2,
                    "max_results": 100,
                    "highlight": True,
                    "facets": ["format", "category", "tags"]
                }
            },
            "storage": {
                "backend": "sqlite",
                "sqlite": {
                    "path": "./.docscope/docscope.db",
                    "journal_mode": "WAL"
                }
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "workers": 2,
                "reload": False,
                "cors_origins": ["*"]
            },
            "export": {
                "formats": ["html", "pdf", "markdown"],
                "themes": ["light", "dark"]
            },
            "plugins": {
                "enabled": [],
                "directories": ["./plugins"]
            },
            "logging": {
                "level": "INFO",
                "file": "./.docscope/docscope.log",
                "max_bytes": 10485760,
                "backup_count": 5
            }
        }
    }
    
    # Write configuration file
    import yaml
    config_data = templates[template]
    
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    # Create additional directories for full template
    if template == 'full':
        (project_path / "examples").mkdir(exist_ok=True)
        (project_path / "plugins").mkdir(exist_ok=True)
        (project_path / ".docscope").mkdir(exist_ok=True)
    
    # Create sample README if it doesn't exist
    readme_path = project_path / "README.md"
    if not readme_path.exists():
        readme_path.write_text(f"""# {name}

Documentation for {name} project.

## Getting Started

1. Add your documentation to the `docs` directory
2. Run `docscope scan` to index your documents
3. Use `docscope search <query>` to search
4. Run `docscope serve` to start the web interface

## Configuration

Edit `.docscope.yaml` to customize settings.
""")
    
    # Create sample documentation
    sample_doc = docs_path / "getting-started.md"
    if not sample_doc.exists():
        sample_doc.write_text(f"""# Getting Started with {name}

Welcome to {name} documentation!

## Installation

Instructions for installation...

## Usage

How to use {name}...

## Configuration

Configuration options...
""")
    
    # Display summary
    console.print("\n[green]✓ Project initialized successfully![/green]")
    
    summary = Table(show_header=False, box=None)
    summary.add_column(style="cyan")
    summary.add_column()
    
    summary.add_row("Project:", name)
    summary.add_row("Location:", str(project_path))
    summary.add_row("Configuration:", str(config_path))
    summary.add_row("Template:", template)
    summary.add_row("Docs directory:", str(docs_path))
    
    console.print(summary)
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Add documentation to the 'docs' directory")
    console.print("  2. Run [cyan]docscope scan[/cyan] to index documents")
    console.print("  3. Run [cyan]docscope search <query>[/cyan] to search")
    console.print("  4. Run [cyan]docscope serve[/cyan] to start the web server")
    console.print("\n[dim]Edit .docscope.yaml to customize configuration[/dim]")


# Add commands to CLI
cli.add_command(scan_command)
cli.add_command(search_command)
cli.add_command(serve_command)
cli.add_command(export_command)
cli.add_command(watch_command)
cli.add_command(stats_command)
cli.add_command(db_group)
cli.add_command(plugins_group)
cli.add_command(config_group)


# Additional utility commands
@cli.command()
@click.pass_context
def info(ctx):
    """Show DocScope system information"""
    console.print("\n[bold blue]DocScope System Information[/bold blue]\n")
    
    info_table = Table(show_header=False, box=None)
    info_table.add_column(style="cyan")
    info_table.add_column()
    
    info_table.add_row("Version:", __version__)
    info_table.add_row("Python:", sys.version.split()[0])
    info_table.add_row("Platform:", sys.platform)
    
    if ctx.obj.config.config_file:
        info_table.add_row("Config file:", str(ctx.obj.config.config_file))
    
    info_table.add_row("Project:", ctx.obj.config.project or "Not set")
    
    # Check component availability
    components = []
    try:
        import fastapi
        components.append("API Server")
    except ImportError:
        pass
    
    try:
        import whoosh
        components.append("Search Engine")
    except ImportError:
        pass
    
    try:
        import sqlalchemy
        components.append("Database")
    except ImportError:
        pass
    
    if components:
        info_table.add_row("Components:", ", ".join(components))
    
    console.print(info_table)


@cli.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), 
              help='Shell to generate completion for')
def completion(shell):
    """Generate shell completion script
    
    Generate and display shell completion script for the specified shell.
    """
    if not shell:
        # Detect shell
        import os
        shell_env = os.environ.get('SHELL', '')
        if 'zsh' in shell_env:
            shell = 'zsh'
        elif 'fish' in shell_env:
            shell = 'fish'
        else:
            shell = 'bash'
    
    console.print(f"[blue]Generating {shell} completion script...[/blue]\n")
    
    if shell == 'bash':
        script = """# Add to ~/.bashrc or ~/.bash_profile:
eval "$(_DOCSCOPE_COMPLETE=bash_source docscope)"
"""
    elif shell == 'zsh':
        script = """# Add to ~/.zshrc:
eval "$(_DOCSCOPE_COMPLETE=zsh_source docscope)"
"""
    elif shell == 'fish':
        script = """# Add to ~/.config/fish/completions/docscope.fish:
eval (env _DOCSCOPE_COMPLETE=fish_source docscope)
"""
    
    console.print(script)
    console.print("[dim]Copy the above to your shell configuration file[/dim]")


def main():
    """Main entry point"""
    try:
        cli(prog_name='docscope')
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        if '--debug' in sys.argv:
            raise
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()