"""Config command implementation"""

import click
import yaml
import json
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from ...core.config import Config
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group(name='config')
def config_group():
    """Configuration management commands"""
    pass


@config_group.command(name='show')
@click.option('--format', '-f',
              type=click.Choice(['yaml', 'json', 'table']),
              default='yaml', help='Output format')
@click.option('--key', '-k', help='Show specific configuration key')
@click.pass_context
def show_command(ctx, format, key):
    """Show current configuration
    
    Display the current configuration or a specific key.
    """
    config = ctx.obj['config']
    
    try:
        if key:
            # Get specific key value
            value = config.get(key)
            if value is None:
                console.print(f"[yellow]Key '{key}' not found[/yellow]")
                return
            
            if isinstance(value, (dict, list)):
                if format == 'json':
                    click.echo(json.dumps(value, indent=2))
                else:
                    click.echo(yaml.dump(value, default_flow_style=False))
            else:
                console.print(f"{key}: {value}")
        else:
            # Show full configuration
            config_dict = config.to_dict()
            
            if format == 'json':
                click.echo(json.dumps(config_dict, indent=2, default=str))
            elif format == 'yaml':
                yaml_str = yaml.dump(config_dict, default_flow_style=False)
                syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
                console.print(syntax)
            else:
                # Table format
                display_config_table(config_dict)
        
    except Exception as e:
        logger.error(f"Failed to show configuration: {e}")
        console.print(f"[red]Failed to show configuration: {e}[/red]")


@config_group.command(name='get')
@click.argument('key')
@click.pass_context
def get_command(ctx, key):
    """Get a configuration value
    
    Retrieve the value of a specific configuration key.
    """
    config = ctx.obj['config']
    
    try:
        value = config.get(key)
        
        if value is None:
            console.print(f"[yellow]Key '{key}' not found[/yellow]")
        elif isinstance(value, (dict, list)):
            click.echo(yaml.dump(value, default_flow_style=False))
        else:
            click.echo(value)
        
    except Exception as e:
        logger.error(f"Failed to get configuration value: {e}")
        console.print(f"[red]Failed to get configuration value: {e}[/red]")


@config_group.command(name='set')
@click.argument('key')
@click.argument('value')
@click.option('--type', '-t',
              type=click.Choice(['string', 'int', 'bool', 'json']),
              default='string', help='Value type')
@click.pass_context
def set_command(ctx, key, value, type):
    """Set a configuration value
    
    Update a configuration key with a new value.
    """
    config = ctx.obj['config']
    
    try:
        # Parse value based on type
        if type == 'int':
            parsed_value = int(value)
        elif type == 'bool':
            parsed_value = value.lower() in ('true', 'yes', '1')
        elif type == 'json':
            parsed_value = json.loads(value)
        else:
            parsed_value = value
        
        # Set configuration value
        config.set(key, parsed_value)
        
        # Save configuration
        config.save()
        
        console.print(f"[green]✓ Set {key} = {parsed_value}[/green]")
        console.print("\nConfiguration saved")
        
    except ValueError as e:
        console.print(f"[red]Invalid value for type '{type}': {e}[/red]")
    except Exception as e:
        logger.error(f"Failed to set configuration value: {e}")
        console.print(f"[red]Failed to set configuration value: {e}[/red]")


@config_group.command(name='edit')
@click.option('--editor', envvar='EDITOR', help='Editor to use')
@click.pass_context
def edit_command(ctx, editor):
    """Edit configuration file
    
    Open the configuration file in an editor.
    """
    config = ctx.obj['config']
    config_path = config.config_file
    
    if not config_path or not Path(config_path).exists():
        console.print("[red]Configuration file not found[/red]")
        console.print("Initialize a project first with: docscope init")
        return
    
    # Determine editor
    if not editor:
        import os
        editor = os.environ.get('EDITOR', 'nano' if sys.platform != 'win32' else 'notepad')
    
    try:
        import subprocess
        console.print(f"[blue]Opening {config_path} in {editor}...[/blue]")
        subprocess.run([editor, str(config_path)])
        
        # Reload configuration
        config.reload()
        console.print("[green]✓ Configuration reloaded[/green]")
        
    except Exception as e:
        logger.error(f"Failed to edit configuration: {e}")
        console.print(f"[red]Failed to edit configuration: {e}[/red]")


@config_group.command(name='validate')
@click.pass_context
def validate_command(ctx):
    """Validate configuration
    
    Check if the current configuration is valid and complete.
    """
    config = ctx.obj['config']
    
    console.print("[blue]Validating configuration...[/blue]\n")
    
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = [
        'scanner.paths',
        'storage.backend',
        'search.engine'
    ]
    
    for field in required_fields:
        if not config.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Check paths exist
    if config.scanner.paths:
        for path_config in config.scanner.paths:
            if isinstance(path_config, dict):
                path = path_config.get('path')
            else:
                path = path_config
            
            if path and not Path(path).exists():
                warnings.append(f"Path does not exist: {path}")
    
    # Check database configuration
    if config.storage.backend == 'sqlite':
        db_path = config.storage.sqlite.get('path')
        if not db_path:
            errors.append("SQLite database path not configured")
    elif config.storage.backend == 'postgresql':
        pg_config = config.storage.postgresql
        if not pg_config.get('host') or not pg_config.get('database'):
            errors.append("PostgreSQL connection not fully configured")
    
    # Check server configuration
    if config.server.port:
        if not (1 <= config.server.port <= 65535):
            errors.append(f"Invalid port number: {config.server.port}")
    
    # Display results
    if errors:
        console.print("[bold red]Validation Errors:[/bold red]")
        for error in errors:
            console.print(f"  ✗ {error}")
        console.print()
    
    if warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  ! {warning}")
        console.print()
    
    if not errors and not warnings:
        console.print("[green]✓ Configuration is valid[/green]")
    elif errors:
        console.print("[red]Configuration has errors that need to be fixed[/red]")
    else:
        console.print("[yellow]Configuration is valid but has warnings[/yellow]")
    
    return len(errors) == 0


@config_group.command(name='migrate')
@click.option('--from-version', help='Source configuration version')
@click.option('--backup', is_flag=True, help='Create backup before migration')
@click.pass_context
def migrate_command(ctx, from_version, backup):
    """Migrate configuration to latest version
    
    Update configuration file format to the latest version.
    """
    config = ctx.obj['config']
    config_path = Path(config.config_file) if config.config_file else None
    
    if not config_path or not config_path.exists():
        console.print("[red]Configuration file not found[/red]")
        return
    
    console.print("[blue]Migrating configuration...[/blue]")
    
    try:
        # Create backup if requested
        if backup:
            backup_path = config_path.with_suffix('.yaml.bak')
            import shutil
            shutil.copy2(config_path, backup_path)
            console.print(f"[green]✓ Backup created: {backup_path}[/green]")
        
        # Perform migration
        changes = config.migrate(from_version=from_version)
        
        if changes:
            console.print("\n[bold]Migration changes:[/bold]")
            for change in changes:
                console.print(f"  • {change}")
            
            # Save migrated configuration
            config.save()
            console.print("\n[green]✓ Configuration migrated successfully[/green]")
        else:
            console.print("[green]Configuration is already up to date[/green]")
        
    except Exception as e:
        logger.error(f"Failed to migrate configuration: {e}")
        console.print(f"[red]Failed to migrate configuration: {e}[/red]")
        if backup:
            console.print("[yellow]Restore from backup if needed[/yellow]")


def display_config_table(config_dict, prefix=""):
    """Display configuration as a table"""
    table = Table(title="Configuration", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Type", style="dim")
    
    def add_items(d, prefix=""):
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                add_items(value, full_key)
            elif isinstance(value, list):
                table.add_row(full_key, f"[{len(value)} items]", "list")
            else:
                table.add_row(full_key, str(value), type(value).__name__)
    
    add_items(config_dict)
    console.print(table)