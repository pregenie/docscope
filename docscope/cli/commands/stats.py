"""Stats command implementation"""

import click
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.chart import Chart
from rich.panel import Panel

from ...storage import DocumentStore
from ...search import SearchEngine
from ...core.config import Config
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command(name='stats')
@click.option('--format', '-f', 
              type=click.Choice(['table', 'json', 'detailed']),
              default='table', help='Output format')
@click.option('--period', '-p',
              type=click.Choice(['today', 'week', 'month', 'all']),
              default='all', help='Time period for statistics')
@click.pass_context
def stats_command(ctx, format, period):
    """Show DocScope statistics
    
    Display statistics about indexed documents, search performance,
    and system usage.
    """
    config = ctx.obj['config']
    
    # Initialize components
    storage = DocumentStore(config)
    search_engine = SearchEngine(config)
    
    try:
        # Gather statistics
        stats = gather_statistics(storage, search_engine, period)
        
        # Display based on format
        if format == 'json':
            import json
            click.echo(json.dumps(stats, indent=2, default=str))
        elif format == 'detailed':
            display_detailed_stats(stats)
        else:
            display_table_stats(stats)
            
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        console.print(f"[red]Failed to get statistics: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


def gather_statistics(storage, search_engine, period):
    """Gather system statistics"""
    stats = {}
    
    # Calculate date range
    now = datetime.now()
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    else:
        start_date = None
    
    # Document statistics
    total_docs = storage.count_documents()
    stats['documents'] = {
        'total': total_docs,
        'by_format': {},
        'by_category': {},
        'by_status': {}
    }
    
    # Format distribution
    for format_type in ['markdown', 'text', 'json', 'yaml', 'code', 'html']:
        count = storage.count_documents(format=format_type)
        if count > 0:
            stats['documents']['by_format'][format_type] = count
    
    # Category distribution
    categories = storage.list_categories()
    for category in categories:
        stats['documents']['by_category'][category.get('name')] = category.get('document_count', 0)
    
    # Status distribution
    for status in ['pending', 'indexed', 'failed']:
        count = storage.count_documents(status=status)
        if count > 0:
            stats['documents']['by_status'][status] = count
    
    # Tag statistics
    tags = storage.list_tags()
    stats['tags'] = {
        'total': len(tags),
        'most_used': sorted(tags, key=lambda t: t.get('document_count', 0), reverse=True)[:10]
    }
    
    # Search statistics
    search_stats = search_engine.get_index_stats()
    stats['search'] = search_stats
    
    # Storage statistics
    stats['storage'] = {
        'database_size': storage.get_database_size(),
        'index_size': search_engine.get_index_size(),
        'total_size': 0
    }
    stats['storage']['total_size'] = (
        stats['storage']['database_size'] + 
        stats['storage']['index_size']
    )
    
    # Recent activity
    if start_date:
        stats['recent'] = {
            'documents_added': storage.count_documents_since(start_date),
            'searches_performed': search_engine.get_search_count_since(start_date)
        }
    
    # Scan statistics
    scan_stats = storage.get_scan_stats()
    if scan_stats:
        stats['scans'] = {
            'total': len(scan_stats),
            'last_scan': scan_stats[-1] if scan_stats else None,
            'total_scanned': sum(s.get('total', 0) for s in scan_stats),
            'total_duration': sum(s.get('duration', 0) for s in scan_stats)
        }
    
    return stats


def display_table_stats(stats):
    """Display statistics in table format"""
    console.print("\n[bold blue]DocScope Statistics[/bold blue]\n")
    
    # Document Statistics
    doc_table = Table(title="Document Statistics", show_header=False)
    doc_table.add_column(style="cyan")
    doc_table.add_column(justify="right", style="bold")
    
    doc_table.add_row("Total Documents", str(stats['documents']['total']))
    
    if stats['documents']['by_format']:
        doc_table.add_row("", "")
        doc_table.add_row("[bold]By Format[/bold]", "")
        for fmt, count in stats['documents']['by_format'].items():
            doc_table.add_row(f"  {fmt}", str(count))
    
    if stats['documents']['by_category']:
        doc_table.add_row("", "")
        doc_table.add_row("[bold]By Category[/bold]", "")
        for cat, count in list(stats['documents']['by_category'].items())[:5]:
            doc_table.add_row(f"  {cat}", str(count))
    
    if stats['documents']['by_status']:
        doc_table.add_row("", "")
        doc_table.add_row("[bold]By Status[/bold]", "")
        for status, count in stats['documents']['by_status'].items():
            doc_table.add_row(f"  {status}", str(count))
    
    console.print(doc_table)
    console.print()
    
    # Tag Statistics
    if stats.get('tags'):
        tag_table = Table(title="Tag Statistics", show_header=True)
        tag_table.add_column("Tag", style="cyan")
        tag_table.add_column("Documents", justify="right")
        
        for tag in stats['tags']['most_used'][:5]:
            tag_table.add_row(tag['name'], str(tag.get('document_count', 0)))
        
        console.print(tag_table)
        console.print()
    
    # Search Statistics
    if stats.get('search'):
        search_table = Table(title="Search Index", show_header=False)
        search_table.add_column(style="cyan")
        search_table.add_column(justify="right", style="bold")
        
        if 'document_count' in stats['search']:
            search_table.add_row("Indexed Documents", str(stats['search']['document_count']))
        if 'term_count' in stats['search']:
            search_table.add_row("Unique Terms", str(stats['search']['term_count']))
        if 'index_size' in stats['search']:
            size_mb = stats['search']['index_size'] / (1024 * 1024)
            search_table.add_row("Index Size", f"{size_mb:.1f} MB")
        
        console.print(search_table)
        console.print()
    
    # Storage Statistics
    if stats.get('storage'):
        storage_table = Table(title="Storage Usage", show_header=False)
        storage_table.add_column(style="cyan")
        storage_table.add_column(justify="right", style="bold")
        
        db_size_mb = stats['storage']['database_size'] / (1024 * 1024)
        idx_size_mb = stats['storage']['index_size'] / (1024 * 1024)
        total_size_mb = stats['storage']['total_size'] / (1024 * 1024)
        
        storage_table.add_row("Database Size", f"{db_size_mb:.1f} MB")
        storage_table.add_row("Index Size", f"{idx_size_mb:.1f} MB")
        storage_table.add_row("Total Size", f"{total_size_mb:.1f} MB")
        
        console.print(storage_table)
        console.print()
    
    # Scan Statistics
    if stats.get('scans'):
        scan_table = Table(title="Scan History", show_header=False)
        scan_table.add_column(style="cyan")
        scan_table.add_column(justify="right", style="bold")
        
        scan_table.add_row("Total Scans", str(stats['scans']['total']))
        scan_table.add_row("Documents Scanned", str(stats['scans']['total_scanned']))
        
        if stats['scans']['last_scan']:
            last_scan = stats['scans']['last_scan']
            scan_date = last_scan.get('timestamp', 'Unknown')
            if isinstance(scan_date, datetime):
                scan_date = scan_date.strftime("%Y-%m-%d %H:%M")
            scan_table.add_row("Last Scan", scan_date)
        
        if stats['scans']['total_duration'] > 0:
            scan_table.add_row("Total Scan Time", f"{stats['scans']['total_duration']:.1f}s")
        
        console.print(scan_table)


def display_detailed_stats(stats):
    """Display detailed statistics with visualizations"""
    console.print("\n[bold blue]DocScope Detailed Statistics[/bold blue]\n")
    
    # Overview Panel
    overview = f"""
[bold]Documents:[/bold] {stats['documents']['total']}
[bold]Categories:[/bold] {len(stats['documents'].get('by_category', {}))}
[bold]Tags:[/bold] {stats['tags']['total']}
[bold]Index Size:[/bold] {stats['storage']['total_size'] / (1024 * 1024):.1f} MB
    """
    console.print(Panel(overview.strip(), title="Overview", expand=False))
    console.print()
    
    # Format Distribution Chart
    if stats['documents']['by_format']:
        console.print("[bold]Document Format Distribution[/bold]")
        
        max_count = max(stats['documents']['by_format'].values())
        for fmt, count in sorted(stats['documents']['by_format'].items(), 
                                key=lambda x: x[1], reverse=True):
            bar_length = int((count / max_count) * 40)
            bar = "█" * bar_length
            percentage = (count / stats['documents']['total']) * 100
            console.print(f"  {fmt:10} {bar} {count:4} ({percentage:.1f}%)")
        console.print()
    
    # Top Categories
    if stats['documents']['by_category']:
        console.print("[bold]Top Categories[/bold]")
        categories = sorted(stats['documents']['by_category'].items(),
                          key=lambda x: x[1], reverse=True)[:10]
        
        for cat, count in categories:
            console.print(f"  • {cat}: {count} documents")
        console.print()
    
    # Search Performance
    if stats.get('search'):
        perf_panel = f"""
[cyan]Indexed Documents:[/cyan] {stats['search'].get('document_count', 0)}
[cyan]Unique Terms:[/cyan] {stats['search'].get('term_count', 0)}
[cyan]Average Query Time:[/cyan] {stats['search'].get('avg_query_time', 0):.3f}s
[cyan]Cache Hit Rate:[/cyan] {stats['search'].get('cache_hit_rate', 0):.1%}
        """
        console.print(Panel(perf_panel.strip(), title="Search Performance", expand=False))
        console.print()
    
    # Recent Activity
    if stats.get('recent'):
        activity_panel = f"""
[green]Documents Added:[/green] {stats['recent'].get('documents_added', 0)}
[blue]Searches Performed:[/blue] {stats['recent'].get('searches_performed', 0)}
        """
        console.print(Panel(activity_panel.strip(), title="Recent Activity", expand=False))
        console.print()
    
    # System Health
    health_indicators = []
    
    # Check index freshness
    if stats.get('search', {}).get('last_indexed'):
        last_indexed = stats['search']['last_indexed']
        if isinstance(last_indexed, str):
            last_indexed = datetime.fromisoformat(last_indexed)
        age = (datetime.now() - last_indexed).days
        
        if age == 0:
            health_indicators.append("[green]✓[/green] Index is up to date")
        elif age < 7:
            health_indicators.append(f"[yellow]![/yellow] Index is {age} days old")
        else:
            health_indicators.append(f"[red]✗[/red] Index is {age} days old")
    
    # Check document/index ratio
    doc_count = stats['documents']['total']
    indexed_count = stats.get('search', {}).get('document_count', 0)
    if doc_count > 0:
        index_ratio = indexed_count / doc_count
        if index_ratio >= 0.95:
            health_indicators.append(f"[green]✓[/green] {index_ratio:.0%} documents indexed")
        elif index_ratio >= 0.8:
            health_indicators.append(f"[yellow]![/yellow] {index_ratio:.0%} documents indexed")
        else:
            health_indicators.append(f"[red]✗[/red] Only {index_ratio:.0%} documents indexed")
    
    if health_indicators:
        console.print("[bold]System Health[/bold]")
        for indicator in health_indicators:
            console.print(f"  {indicator}")
        console.print()