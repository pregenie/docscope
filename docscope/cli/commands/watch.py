"""Watch command implementation"""

import click
import time
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live

from ...scanner import DocumentScanner
from ...storage import DocumentStore
from ...search import SearchEngine
from ...core.config import Config
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command(name='watch')
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--interval', '-i', type=int, default=5, help='Check interval in seconds')
@click.option('--recursive', '-r', is_flag=True, default=True, help='Watch directories recursively')
@click.option('--formats', help='Comma-separated list of formats to watch')
@click.option('--auto-index', is_flag=True, default=True, help='Automatically index changes')
@click.option('--notify', is_flag=True, help='Show desktop notifications')
@click.pass_context
def watch_command(ctx, paths, interval, recursive, formats, auto_index, notify):
    """Watch directories for changes
    
    Monitor specified directories for document changes and automatically
    update the index when files are added, modified, or deleted.
    """
    config = ctx.obj['config']
    
    # Initialize components
    scanner = DocumentScanner(config)
    storage = DocumentStore(config)
    search_engine = SearchEngine(config)
    
    # Determine paths to watch
    if not paths:
        watch_paths = []
        for path_config in config.scanner.paths:
            if isinstance(path_config, dict):
                watch_paths.append(Path(path_config.get('path', '.')))
            else:
                watch_paths.append(Path(path_config))
    else:
        watch_paths = [Path(p) for p in paths]
    
    # Parse formats
    format_list = None
    if formats:
        format_list = [f.strip() for f in formats.split(',')]
    
    console.print("\n[bold blue]Watch Configuration[/bold blue]")
    
    config_table = Table(show_header=False, box=None)
    config_table.add_column(style="cyan")
    config_table.add_column()
    
    config_table.add_row("Paths:", ", ".join(str(p) for p in watch_paths))
    config_table.add_row("Interval:", f"{interval} seconds")
    config_table.add_row("Recursive:", "Yes" if recursive else "No")
    if format_list:
        config_table.add_row("Formats:", ", ".join(format_list))
    config_table.add_row("Auto-index:", "Yes" if auto_index else "No")
    config_table.add_row("Notifications:", "Yes" if notify else "No")
    
    console.print(config_table)
    console.print("\n[green]Watching for changes...[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    # Track file states
    file_states = {}
    
    def scan_directory(path):
        """Scan directory for files"""
        files = {}
        
        if path.is_file():
            files[str(path)] = {
                'size': path.stat().st_size,
                'mtime': path.stat().st_mtime
            }
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    # Check format filter
                    if format_list and file_path.suffix.lower() not in format_list:
                        continue
                    
                    files[str(file_path)] = {
                        'size': file_path.stat().st_size,
                        'mtime': file_path.stat().st_mtime
                    }
        
        return files
    
    def detect_changes(old_state, new_state):
        """Detect file changes"""
        added = []
        modified = []
        deleted = []
        
        # Check for added and modified files
        for file_path, state in new_state.items():
            if file_path not in old_state:
                added.append(file_path)
            elif (state['size'] != old_state[file_path]['size'] or
                  state['mtime'] != old_state[file_path]['mtime']):
                modified.append(file_path)
        
        # Check for deleted files
        for file_path in old_state:
            if file_path not in new_state:
                deleted.append(file_path)
        
        return added, modified, deleted
    
    def show_notification(message):
        """Show desktop notification"""
        if notify:
            try:
                import subprocess
                if sys.platform == 'darwin':
                    subprocess.run([
                        'osascript', '-e',
                        f'display notification "{message}" with title "DocScope"'
                    ])
                elif sys.platform.startswith('linux'):
                    subprocess.run([
                        'notify-send', 'DocScope', message
                    ])
            except Exception as e:
                logger.warning(f"Failed to show notification: {e}")
    
    try:
        # Initial scan
        for path in watch_paths:
            file_states.update(scan_directory(path))
        
        console.print(f"[dim]Monitoring {len(file_states)} files[/dim]\n")
        
        # Watch loop
        stats_table = Table(title="Watch Statistics", show_header=True)
        stats_table.add_column("Event", style="cyan")
        stats_table.add_column("Count", justify="right")
        stats_table.add_column("Last Update", style="dim")
        
        stats = {
            'added': 0,
            'modified': 0,
            'deleted': 0,
            'indexed': 0,
            'errors': 0
        }
        
        last_update = "Never"
        
        with Live(stats_table, refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(interval)
                
                # Scan for changes
                current_state = {}
                for path in watch_paths:
                    current_state.update(scan_directory(path))
                
                # Detect changes
                added, modified, deleted = detect_changes(file_states, current_state)
                
                if added or modified or deleted:
                    last_update = datetime.now().strftime("%H:%M:%S")
                    
                    # Process added files
                    if added:
                        stats['added'] += len(added)
                        console.print(f"[green]+ Added {len(added)} files:[/green]")
                        for file_path in added[:5]:  # Show first 5
                            console.print(f"  • {file_path}")
                        if len(added) > 5:
                            console.print(f"  ... and {len(added) - 5} more")
                        
                        if auto_index:
                            # Scan and index new files
                            result = scanner.scan([Path(f) for f in added], recursive=False)
                            if result.successful > 0:
                                storage.store_scan_result(result)
                                search_engine.index_documents(result.documents)
                                stats['indexed'] += result.successful
                        
                        show_notification(f"Added {len(added)} files")
                    
                    # Process modified files
                    if modified:
                        stats['modified'] += len(modified)
                        console.print(f"[yellow]~ Modified {len(modified)} files:[/yellow]")
                        for file_path in modified[:5]:
                            console.print(f"  • {file_path}")
                        if len(modified) > 5:
                            console.print(f"  ... and {len(modified) - 5} more")
                        
                        if auto_index:
                            # Re-scan and re-index modified files
                            result = scanner.scan([Path(f) for f in modified], recursive=False)
                            if result.successful > 0:
                                for doc in result.documents:
                                    storage.update_document(doc.id, {
                                        'content': doc.content,
                                        'size': doc.size,
                                        'content_hash': doc.content_hash,
                                        'modified_at': doc.modified_at
                                    })
                                search_engine.index_documents(result.documents)
                                stats['indexed'] += result.successful
                        
                        show_notification(f"Modified {len(modified)} files")
                    
                    # Process deleted files
                    if deleted:
                        stats['deleted'] += len(deleted)
                        console.print(f"[red]- Deleted {len(deleted)} files:[/red]")
                        for file_path in deleted[:5]:
                            console.print(f"  • {file_path}")
                        if len(deleted) > 5:
                            console.print(f"  ... and {len(deleted) - 5} more")
                        
                        if auto_index:
                            # Remove from index
                            for file_path in deleted:
                                # Find document by path
                                docs = storage.list_documents(path=file_path)
                                for doc in docs:
                                    storage.delete_document(doc.id)
                                    search_engine.remove_document(doc.id)
                        
                        show_notification(f"Deleted {len(deleted)} files")
                    
                    console.print()
                    
                    # Update file states
                    file_states = current_state
                
                # Update statistics table
                stats_table = Table(title="Watch Statistics", show_header=True)
                stats_table.add_column("Event", style="cyan")
                stats_table.add_column("Count", justify="right")
                
                stats_table.add_row("Files monitored", str(len(file_states)))
                stats_table.add_row("Files added", f"[green]{stats['added']}[/green]")
                stats_table.add_row("Files modified", f"[yellow]{stats['modified']}[/yellow]")
                stats_table.add_row("Files deleted", f"[red]{stats['deleted']}[/red]")
                if auto_index:
                    stats_table.add_row("Documents indexed", str(stats['indexed']))
                if stats['errors'] > 0:
                    stats_table.add_row("Errors", f"[red]{stats['errors']}[/red]")
                stats_table.add_row("Last update", last_update)
                
                live.update(stats_table)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch stopped[/yellow]")
        
        # Final statistics
        console.print("\n[bold]Final Statistics:[/bold]")
        final_table = Table(show_header=False, box=None)
        final_table.add_column(style="cyan")
        final_table.add_column(justify="right")
        
        final_table.add_row("Total files added:", str(stats['added']))
        final_table.add_row("Total files modified:", str(stats['modified']))
        final_table.add_row("Total files deleted:", str(stats['deleted']))
        if auto_index:
            final_table.add_row("Total documents indexed:", str(stats['indexed']))
        
        console.print(final_table)
        
    except Exception as e:
        logger.error(f"Watch failed: {e}")
        console.print(f"\n[red]Watch failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())