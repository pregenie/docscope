"""Database command implementation"""

import click
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...storage import DocumentStore
from ...search import SearchEngine
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group(name='db')
def db_group():
    """Database management commands"""
    pass


@db_group.command(name='init')
@click.option('--force', is_flag=True, help='Force initialization (will drop existing data)')
@click.pass_context
def init_command(ctx, force):
    """Initialize database
    
    Create database tables and indexes. Use --force to reinitialize
    and drop existing data.
    """
    config = ctx.obj.config
    
    if force:
        if not click.confirm("[red]This will delete all existing data. Continue?[/red]"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return
    
    console.print("[blue]Initializing database...[/blue]")
    
    try:
        storage = DocumentStore(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Creating database schema...", total=None)
            
            # Initialize database
            storage.initialize_database(force=force)
            
            progress.update(task, description="Creating indexes...")
            storage.create_indexes()
            
            progress.update(task, description="Verifying database...")
            storage.verify_database()
            
        console.print("[green]✓ Database initialized successfully[/green]")
        
        # Show database info
        info = storage.get_database_info()
        console.print(f"  Location: {info.get('path', 'default')}")
        console.print(f"  Backend: {info.get('backend', 'unknown')}")
        console.print(f"  Version: {info.get('version', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        console.print(f"[red]Database initialization failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


@db_group.command(name='status')
@click.pass_context
def status_command(ctx):
    """Show database status
    
    Display information about the database including size,
    document count, and health status.
    """
    config = ctx.obj.config
    
    try:
        storage = DocumentStore(config)
        
        console.print("\n[bold blue]Database Status[/bold blue]\n")
        
        # Basic info
        info = storage.get_database_info()
        
        info_table = Table(show_header=False, box=None)
        info_table.add_column(style="cyan")
        info_table.add_column()
        
        info_table.add_row("Backend:", info.get('backend', 'unknown'))
        info_table.add_row("Location:", info.get('path', 'default'))
        info_table.add_row("Version:", info.get('version', 'unknown'))
        
        # Size information
        size = storage.get_database_size()
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        info_table.add_row("Size:", size_str)
        
        # Document counts
        total_docs = storage.count_documents()
        info_table.add_row("Documents:", str(total_docs))
        
        # Category count
        categories = storage.list_categories()
        info_table.add_row("Categories:", str(len(categories)))
        
        # Tag count
        tags = storage.list_tags()
        info_table.add_row("Tags:", str(len(tags)))
        
        console.print(info_table)
        console.print()
        
        # Table statistics
        table_stats = storage.get_table_statistics()
        if table_stats:
            console.print("[bold]Table Statistics[/bold]")
            
            stats_table = Table(show_header=True)
            stats_table.add_column("Table", style="cyan")
            stats_table.add_column("Rows", justify="right")
            stats_table.add_column("Size", justify="right")
            
            for table_name, stats in table_stats.items():
                size_kb = stats.get('size', 0) / 1024
                stats_table.add_row(
                    table_name,
                    str(stats.get('rows', 0)),
                    f"{size_kb:.1f} KB"
                )
            
            console.print(stats_table)
            console.print()
        
        # Health checks
        console.print("[bold]Health Checks[/bold]")
        health_checks = storage.run_health_checks()
        
        for check, result in health_checks.items():
            if result['status'] == 'ok':
                console.print(f"  [green]✓[/green] {check}: {result.get('message', 'OK')}")
            elif result['status'] == 'warning':
                console.print(f"  [yellow]![/yellow] {check}: {result.get('message', 'Warning')}")
            else:
                console.print(f"  [red]✗[/red] {check}: {result.get('message', 'Failed')}")
        
    except Exception as e:
        logger.error(f"Failed to get database status: {e}")
        console.print(f"[red]Failed to get database status: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


@db_group.command(name='backup')
@click.option('--output', '-o', type=click.Path(), help='Backup file path')
@click.option('--compress', is_flag=True, help='Compress backup')
@click.pass_context
def backup_command(ctx, output, compress):
    """Create database backup
    
    Create a backup of the database. Supports compression
    and custom output paths.
    """
    config = ctx.obj.config
    
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"docscope_backup_{timestamp}.db"
        if compress:
            output += ".gz"
    
    output_path = Path(output)
    
    console.print(f"[blue]Creating backup to: {output_path}[/blue]")
    
    try:
        storage = DocumentStore(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Creating backup...", total=None)
            
            # Create backup
            storage.create_backup(output_path, compress=compress)
            
        console.print(f"[green]✓ Backup created successfully[/green]")
        
        # Show backup info
        size = output_path.stat().st_size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        
        console.print(f"  File: {output_path}")
        console.print(f"  Size: {size_str}")
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        console.print(f"[red]Backup failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


@db_group.command(name='restore')
@click.argument('backup_file', type=click.Path(exists=True))
@click.option('--force', is_flag=True, help='Force restore (will overwrite existing data)')
@click.pass_context
def restore_command(ctx, backup_file, force):
    """Restore database from backup
    
    Restore the database from a backup file. Use --force to
    overwrite existing data without confirmation.
    """
    config = ctx.obj.config
    backup_path = Path(backup_file)
    
    if not force:
        if not click.confirm("[yellow]This will replace existing data. Continue?[/yellow]"):
            console.print("[yellow]Restore cancelled[/yellow]")
            return
    
    console.print(f"[blue]Restoring from: {backup_path}[/blue]")
    
    try:
        storage = DocumentStore(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Restoring backup...", total=None)
            
            # Restore backup
            storage.restore_backup(backup_path)
            
            progress.update(task, description="Verifying restore...")
            storage.verify_database()
            
        console.print("[green]✓ Backup restored successfully[/green]")
        
        # Show restored data stats
        total_docs = storage.count_documents()
        console.print(f"  Documents restored: {total_docs}")
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        console.print(f"[red]Restore failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


@db_group.command(name='migrate')
@click.option('--target-version', help='Target migration version')
@click.option('--dry-run', is_flag=True, help='Show what would be migrated')
@click.pass_context
def migrate_command(ctx, target_version, dry_run):
    """Run database migrations
    
    Apply database schema migrations to update the database
    to the latest version or a specific target version.
    """
    config = ctx.obj.config
    
    console.print("[blue]Checking for migrations...[/blue]")
    
    try:
        storage = DocumentStore(config)
        
        # Get migration info
        current_version = storage.get_schema_version()
        available_migrations = storage.get_available_migrations()
        
        console.print(f"Current version: {current_version}")
        
        if not available_migrations:
            console.print("[green]Database is up to date[/green]")
            return
        
        console.print(f"Available migrations: {len(available_migrations)}")
        
        if dry_run:
            console.print("\n[yellow]Dry run - showing migrations that would be applied:[/yellow]")
            for migration in available_migrations:
                console.print(f"  • {migration['version']}: {migration['description']}")
            return
        
        # Apply migrations
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task(
                "Applying migrations...",
                total=len(available_migrations)
            )
            
            for migration in available_migrations:
                if target_version and migration['version'] > target_version:
                    break
                
                progress.update(
                    task,
                    description=f"Applying {migration['version']}..."
                )
                
                storage.apply_migration(migration)
                progress.update(task, advance=1)
            
        console.print("[green]✓ Migrations applied successfully[/green]")
        console.print(f"New version: {storage.get_schema_version()}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        console.print(f"[red]Migration failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


@db_group.command(name='optimize')
@click.option('--vacuum', is_flag=True, help='Run VACUUM to reclaim space')
@click.option('--analyze', is_flag=True, help='Update query optimizer statistics')
@click.option('--reindex', is_flag=True, help='Rebuild all indexes')
@click.pass_context
def optimize_command(ctx, vacuum, analyze, reindex):
    """Optimize database performance
    
    Run various optimization tasks to improve database performance
    including vacuum, analyze, and reindex operations.
    """
    config = ctx.obj.config
    
    # Default to all operations if none specified
    if not any([vacuum, analyze, reindex]):
        vacuum = analyze = reindex = True
    
    console.print("[blue]Optimizing database...[/blue]")
    
    try:
        storage = DocumentStore(config)
        search_engine = SearchEngine(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False
        ) as progress:
            
            tasks = []
            if vacuum:
                tasks.append(("Vacuuming database...", storage.vacuum_database))
            if analyze:
                tasks.append(("Analyzing database...", storage.analyze_database))
            if reindex:
                tasks.append(("Rebuilding indexes...", storage.rebuild_indexes))
                tasks.append(("Optimizing search index...", search_engine.optimize_index))
            
            task = progress.add_task("Optimizing...", total=len(tasks))
            
            for description, operation in tasks:
                progress.update(task, description=description)
                operation()
                progress.update(task, advance=1)
            
        console.print("[green]✓ Database optimized successfully[/green]")
        
        # Show optimization results
        console.print("\n[bold]Optimization Results[/bold]")
        
        results_table = Table(show_header=False, box=None)
        results_table.add_column(style="cyan")
        results_table.add_column()
        
        if vacuum:
            results_table.add_row("Vacuum:", "Completed")
        if analyze:
            results_table.add_row("Analyze:", "Completed")
        if reindex:
            results_table.add_row("Reindex:", "Completed")
        
        # Get new database size
        size = storage.get_database_size()
        size_mb = size / (1024 * 1024)
        results_table.add_row("Database size:", f"{size_mb:.1f} MB")
        
        console.print(results_table)
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        console.print(f"[red]Optimization failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())