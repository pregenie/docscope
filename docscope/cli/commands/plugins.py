"""Plugins command implementation"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ...core.config import Config
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group(name='plugins')
def plugins_group():
    """Plugin management commands"""
    pass


@plugins_group.command(name='list')
@click.option('--format', '-f', 
              type=click.Choice(['table', 'json']),
              default='table', help='Output format')
@click.pass_context
def list_command(ctx, format):
    """List installed plugins
    
    Display all installed plugins with their status and version.
    """
    config = ctx.obj['config']
    
    try:
        # Get plugin manager (would be implemented in plugin system)
        from ...plugins import PluginManager
        plugin_manager = PluginManager(config)
        
        plugins = plugin_manager.list_plugins()
        
        if not plugins:
            console.print("[yellow]No plugins installed[/yellow]")
            console.print("\nInstall plugins using: docscope plugins install <plugin-name>")
            return
        
        if format == 'json':
            output = {
                'plugins': [
                    {
                        'name': p.name,
                        'version': p.version,
                        'enabled': p.enabled,
                        'author': p.author,
                        'description': p.description
                    }
                    for p in plugins
                ]
            }
            click.echo(json.dumps(output, indent=2))
        else:
            # Table format
            table = Table(title="Installed Plugins")
            table.add_column("Name", style="cyan")
            table.add_column("Version")
            table.add_column("Status")
            table.add_column("Author")
            table.add_column("Description", no_wrap=False)
            
            for plugin in plugins:
                status = "[green]Enabled[/green]" if plugin.enabled else "[red]Disabled[/red]"
                table.add_row(
                    plugin.name,
                    plugin.version,
                    status,
                    plugin.author or "-",
                    plugin.description or "-"
                )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(plugins)} plugins[/dim]")
        
    except ImportError:
        console.print("[yellow]Plugin system not available[/yellow]")
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        console.print(f"[red]Failed to list plugins: {e}[/red]")


@plugins_group.command(name='enable')
@click.argument('name')
@click.pass_context
def enable_command(ctx, name):
    """Enable a plugin
    
    Enable a disabled plugin by name.
    """
    config = ctx.obj['config']
    
    try:
        from ...plugins import PluginManager
        plugin_manager = PluginManager(config)
        
        if plugin_manager.enable_plugin(name):
            console.print(f"[green]✓ Plugin '{name}' enabled[/green]")
            console.print("\nRestart DocScope for changes to take effect")
        else:
            console.print(f"[red]Failed to enable plugin '{name}'[/red]")
            console.print("Check if the plugin exists and is properly installed")
        
    except ImportError:
        console.print("[yellow]Plugin system not available[/yellow]")
    except Exception as e:
        logger.error(f"Failed to enable plugin: {e}")
        console.print(f"[red]Failed to enable plugin: {e}[/red]")


@plugins_group.command(name='disable')
@click.argument('name')
@click.pass_context
def disable_command(ctx, name):
    """Disable a plugin
    
    Disable an enabled plugin by name.
    """
    config = ctx.obj['config']
    
    try:
        from ...plugins import PluginManager
        plugin_manager = PluginManager(config)
        
        if plugin_manager.disable_plugin(name):
            console.print(f"[yellow]Plugin '{name}' disabled[/yellow]")
            console.print("\nRestart DocScope for changes to take effect")
        else:
            console.print(f"[red]Failed to disable plugin '{name}'[/red]")
            console.print("Check if the plugin exists")
        
    except ImportError:
        console.print("[yellow]Plugin system not available[/yellow]")
    except Exception as e:
        logger.error(f"Failed to disable plugin: {e}")
        console.print(f"[red]Failed to disable plugin: {e}[/red]")


@plugins_group.command(name='install')
@click.argument('name')
@click.option('--version', help='Specific version to install')
@click.option('--from-file', type=click.Path(exists=True), help='Install from local file')
@click.pass_context
def install_command(ctx, name, version, from_file):
    """Install a plugin
    
    Install a plugin from the plugin repository or a local file.
    """
    config = ctx.obj['config']
    
    console.print(f"[blue]Installing plugin '{name}'...[/blue]")
    
    try:
        from ...plugins import PluginManager
        plugin_manager = PluginManager(config)
        
        if from_file:
            # Install from local file
            result = plugin_manager.install_from_file(Path(from_file))
        else:
            # Install from repository
            result = plugin_manager.install_plugin(name, version=version)
        
        if result:
            console.print(f"[green]✓ Plugin '{name}' installed successfully[/green]")
            console.print(f"  Version: {result.get('version')}")
            console.print(f"  Author: {result.get('author')}")
            
            if result.get('dependencies'):
                console.print("\nDependencies installed:")
                for dep in result['dependencies']:
                    console.print(f"  • {dep}")
            
            console.print("\nEnable the plugin with: docscope plugins enable " + name)
        else:
            console.print(f"[red]Failed to install plugin '{name}'[/red]")
        
    except ImportError:
        console.print("[yellow]Plugin system not available[/yellow]")
    except Exception as e:
        logger.error(f"Failed to install plugin: {e}")
        console.print(f"[red]Failed to install plugin: {e}[/red]")


@plugins_group.command(name='uninstall')
@click.argument('name')
@click.option('--keep-config', is_flag=True, help='Keep plugin configuration')
@click.pass_context
def uninstall_command(ctx, name, keep_config):
    """Uninstall a plugin
    
    Remove a plugin and optionally its configuration.
    """
    config = ctx.obj['config']
    
    if not click.confirm(f"Are you sure you want to uninstall '{name}'?"):
        console.print("[yellow]Uninstall cancelled[/yellow]")
        return
    
    console.print(f"[blue]Uninstalling plugin '{name}'...[/blue]")
    
    try:
        from ...plugins import PluginManager
        plugin_manager = PluginManager(config)
        
        if plugin_manager.uninstall_plugin(name, keep_config=keep_config):
            console.print(f"[green]✓ Plugin '{name}' uninstalled[/green]")
            if keep_config:
                console.print("  Configuration files preserved")
        else:
            console.print(f"[red]Failed to uninstall plugin '{name}'[/red]")
        
    except ImportError:
        console.print("[yellow]Plugin system not available[/yellow]")
    except Exception as e:
        logger.error(f"Failed to uninstall plugin: {e}")
        console.print(f"[red]Failed to uninstall plugin: {e}[/red]")


@plugins_group.command(name='info')
@click.argument('name')
@click.pass_context
def info_command(ctx, name):
    """Show plugin information
    
    Display detailed information about a specific plugin.
    """
    config = ctx.obj['config']
    
    try:
        from ...plugins import PluginManager
        plugin_manager = PluginManager(config)
        
        plugin = plugin_manager.get_plugin_info(name)
        
        if not plugin:
            console.print(f"[red]Plugin '{name}' not found[/red]")
            return
        
        console.print(f"\n[bold blue]Plugin: {plugin.name}[/bold blue]")
        
        info_table = Table(show_header=False, box=None)
        info_table.add_column(style="cyan")
        info_table.add_column()
        
        info_table.add_row("Version:", plugin.version)
        info_table.add_row("Author:", plugin.author or "-")
        info_table.add_row("Status:", 
                          "[green]Enabled[/green]" if plugin.enabled else "[red]Disabled[/red]")
        info_table.add_row("Description:", plugin.description or "-")
        
        if plugin.website:
            info_table.add_row("Website:", plugin.website)
        if plugin.license:
            info_table.add_row("License:", plugin.license)
        
        console.print(info_table)
        
        # Show capabilities
        if plugin.capabilities:
            console.print("\n[bold]Capabilities:[/bold]")
            for cap in plugin.capabilities:
                console.print(f"  • {cap}")
        
        # Show configuration
        if plugin.config_schema:
            console.print("\n[bold]Configuration:[/bold]")
            for key, schema in plugin.config_schema.items():
                required = "[red]*[/red]" if schema.get('required') else ""
                console.print(f"  {key}{required}: {schema.get('description', '-')}")
        
        # Show commands
        if plugin.commands:
            console.print("\n[bold]Commands:[/bold]")
            for cmd in plugin.commands:
                console.print(f"  • {cmd.name}: {cmd.description}")
        
    except ImportError:
        console.print("[yellow]Plugin system not available[/yellow]")
    except Exception as e:
        logger.error(f"Failed to get plugin info: {e}")
        console.print(f"[red]Failed to get plugin info: {e}[/red]")


@plugins_group.command(name='search')
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, help='Maximum results')
@click.pass_context
def search_command(ctx, query, limit):
    """Search for plugins
    
    Search the plugin repository for available plugins.
    """
    config = ctx.obj['config']
    
    console.print(f"[blue]Searching for plugins matching '{query}'...[/blue]")
    
    try:
        from ...plugins import PluginManager
        plugin_manager = PluginManager(config)
        
        results = plugin_manager.search_plugins(query, limit=limit)
        
        if not results:
            console.print(f"[yellow]No plugins found matching '{query}'[/yellow]")
            return
        
        table = Table(title=f"Available Plugins for '{query}'")
        table.add_column("Name", style="cyan")
        table.add_column("Version")
        table.add_column("Author")
        table.add_column("Description", no_wrap=False, max_width=40)
        
        for plugin in results:
            table.add_row(
                plugin['name'],
                plugin['version'],
                plugin.get('author', '-'),
                plugin.get('description', '-')
            )
        
        console.print(table)
        console.print(f"\n[dim]Found {len(results)} plugins[/dim]")
        console.print("\nInstall with: docscope plugins install <plugin-name>")
        
    except ImportError:
        console.print("[yellow]Plugin system not available[/yellow]")
    except Exception as e:
        logger.error(f"Failed to search plugins: {e}")
        console.print(f"[red]Failed to search plugins: {e}[/red]")