"""Scan command implementation"""

import click
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from ...scanner import DocumentScanner
from ...storage import DocumentStore
from ...search import SearchEngine
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command(name='scan')
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--recursive', '-r', is_flag=True, default=True, help='Scan directories recursively')
@click.option('--formats', help='Comma-separated list of formats to scan')
@click.option('--incremental', '-i', is_flag=True, help='Only scan modified files')
@click.option('--since', type=click.DateTime(), help='Scan files modified since date')
@click.option('--exclude', '-e', multiple=True, help='Patterns to exclude')
@click.option('--category', help='Default category for scanned documents')
@click.option('--tags', help='Comma-separated tags to apply')
@click.option('--dry-run', is_flag=True, help='Show what would be scanned without scanning')
@click.option('--parallel', '-j', type=int, help='Number of parallel workers')
@click.pass_context
def scan_command(ctx, paths, recursive, formats, incremental, since, exclude, 
                category, tags, dry_run, parallel):
    """Scan documents and build index
    
    Scan specified paths for documents and add them to the index.
    If no paths are provided, uses paths from configuration.
    """
    config = ctx.obj.config
    
    # Initialize components
    scanner = DocumentScanner(config)
    storage = DocumentStore(config)
    search_engine = SearchEngine(config)
    
    # Determine paths to scan
    if not paths:
        scan_paths = []
        for path_config in config.scanner.paths:
            if isinstance(path_config, dict):
                scan_paths.append(Path(path_config.get('path', '.')))
            else:
                scan_paths.append(Path(path_config))
    else:
        scan_paths = [Path(p) for p in paths]
    
    # Parse formats
    format_list = None
    if formats:
        format_list = [f.strip() for f in formats.split(',')]
    
    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
    
    # Update scanner configuration
    if parallel:
        scanner.config.workers = parallel
    
    # Display scan configuration
    console.print("\n[bold blue]Scan Configuration[/bold blue]")
    table = Table(show_header=False, box=None)
    table.add_column(style="cyan")
    table.add_column()
    
    table.add_row("Paths:", ", ".join(str(p) for p in scan_paths))
    table.add_row("Recursive:", "Yes" if recursive else "No")
    if format_list:
        table.add_row("Formats:", ", ".join(format_list))
    if incremental:
        table.add_row("Mode:", "Incremental")
    if since:
        table.add_row("Since:", since.strftime("%Y-%m-%d %H:%M"))
    if exclude:
        table.add_row("Exclude:", ", ".join(exclude))
    if category:
        table.add_row("Category:", category)
    if tag_list:
        table.add_row("Tags:", ", ".join(tag_list))
    if parallel:
        table.add_row("Workers:", str(parallel))
    if dry_run:
        table.add_row("Mode:", "[yellow]DRY RUN[/yellow]")
    
    console.print(table)
    console.print()
    
    if dry_run:
        # Dry run - just show what would be scanned
        console.print("[yellow]Performing dry run...[/yellow]")
        
        total_files = 0
        for path in scan_paths:
            if path.is_file():
                console.print(f"  Would scan: {path}")
                total_files += 1
            elif path.is_dir() and recursive:
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        # Check if format matches
                        if format_list:
                            suffix = file_path.suffix.lower()
                            if suffix not in format_list:
                                continue
                        
                        # Check exclusions
                        skip = False
                        for pattern in exclude:
                            if pattern in str(file_path):
                                skip = True
                                break
                        
                        if not skip:
                            console.print(f"  Would scan: {file_path}")
                            total_files += 1
        
        console.print(f"\n[green]Would scan {total_files} files[/green]")
        return
    
    # Perform actual scan
    console.print("[blue]Starting document scan...[/blue]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=False
        ) as progress:
            # Create scan task
            scan_task = progress.add_task("Scanning documents...", total=None)
            
            # Perform scan
            if incremental and since:
                result = scanner.incremental_scan(scan_paths, since=since)
            else:
                result = scanner.scan(scan_paths, recursive=recursive)
            
            # Update progress
            progress.update(scan_task, completed=result.total, total=result.total)
            
            # Store documents
            if result.successful > 0:
                progress.update(scan_task, description="Storing documents...")
                storage.store_scan_result(result)
                
                # Index documents
                progress.update(scan_task, description="Indexing documents...")
                search_engine.index_documents(result.documents)
                
                # Apply category and tags
                if category or tag_list:
                    progress.update(scan_task, description="Applying metadata...")
                    for doc in result.documents:
                        updates = {}
                        if category:
                            updates['category'] = category
                        if tag_list:
                            updates['tags'] = tag_list
                        if updates:
                            storage.update_document(doc.id, updates)
            
            progress.update(scan_task, description="Scan complete!")
        
        # Display results
        console.print("\n[bold green]Scan Results[/bold green]")
        
        results_table = Table(show_header=False, box=None)
        results_table.add_column(style="cyan")
        results_table.add_column(style="bold")
        
        results_table.add_row("Total files:", str(result.total))
        results_table.add_row("Successfully scanned:", f"[green]{result.successful}[/green]")
        if result.skipped > 0:
            results_table.add_row("Skipped (unchanged):", f"[yellow]{result.skipped}[/yellow]")
        if result.failed > 0:
            results_table.add_row("Failed:", f"[red]{result.failed}[/red]")
        results_table.add_row("Duration:", f"{result.duration:.2f}s")
        
        console.print(results_table)
        
        # Show errors if any
        if result.errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in result.errors[:10]:  # Show first 10 errors
                console.print(f"  • {error}")
            if len(result.errors) > 10:
                console.print(f"  ... and {len(result.errors) - 10} more")
        
        # Show format breakdown
        if result.successful > 0:
            format_counts = {}
            for doc in result.documents:
                format_counts[doc.format.value] = format_counts.get(doc.format.value, 0) + 1
            
            console.print("\n[bold]Documents by Format:[/bold]")
            format_table = Table(show_header=True)
            format_table.add_column("Format", style="cyan")
            format_table.add_column("Count", justify="right")
            
            for fmt, count in sorted(format_counts.items(), key=lambda x: x[1], reverse=True):
                format_table.add_row(fmt, str(count))
            
            console.print(format_table)
        
        # Save scan statistics
        storage.save_scan_stats({
            'timestamp': datetime.now(),
            'paths': [str(p) for p in scan_paths],
            'total': result.total,
            'successful': result.successful,
            'failed': result.failed,
            'skipped': result.skipped,
            'duration': result.duration
        })
        
        return result
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan interrupted by user[/yellow]")
        return None
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        console.print(f"\n[red]Scan failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        return None