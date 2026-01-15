"""Search command implementation"""

import click
import json
import yaml
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text

from ...search import SearchEngine
from ...storage import DocumentStore
from ...core.config import Config
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command(name='search')
@click.argument('query')
@click.option('--limit', '-l', default=20, type=int, help='Maximum number of results')
@click.option('--offset', default=0, type=int, help='Result offset for pagination')
@click.option('--format', '-f', 
              type=click.Choice(['table', 'json', 'yaml', 'detailed']), 
              default='table', help='Output format')
@click.option('--category', '-c', help='Filter by category')
@click.option('--tags', '-t', multiple=True, help='Filter by tags')
@click.option('--file-type', help='Filter by file type (e.g., md, py, yaml)')
@click.option('--sort', type=click.Choice(['score', 'date', 'title', 'path']), 
              default='score', help='Sort results by')
@click.option('--highlight', is_flag=True, default=True, help='Highlight search terms')
@click.option('--show-snippet', is_flag=True, default=True, help='Show content snippets')
@click.option('--interactive', '-i', is_flag=True, help='Interactive result selection')
@click.option('--open', '-o', is_flag=True, help='Open selected result')
@click.pass_context
def search_command(ctx, query, limit, offset, format, category, tags, file_type, 
                  sort, highlight, show_snippet, interactive, open):
    """Search documents
    
    Search for documents matching the query. Supports advanced query syntax:
    - Boolean: term1 AND term2, term1 OR term2, NOT term
    - Phrase: "exact phrase"
    - Wildcard: term* or ter?m
    - Field: title:term, content:term, tags:term
    - Fuzzy: term~2 (edit distance)
    """
    config = ctx.obj['config']
    
    # Initialize components
    search_engine = SearchEngine(config)
    storage = DocumentStore(config)
    
    # Build filters
    filters = {}
    if category:
        filters['category'] = category
    if tags:
        filters['tags'] = list(tags)
    if file_type:
        filters['format'] = file_type
    
    # Display search query
    console.print(f"\n[bold blue]Searching for:[/bold blue] {query}")
    if filters:
        console.print(f"[dim]Filters: {filters}[/dim]")
    
    try:
        # Perform search
        results = search_engine.search(
            query=query,
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort,
            highlight=highlight
        )
        
        if not results.results:
            console.print("\n[yellow]No results found[/yellow]")
            
            # Show suggestions if available
            if results.suggestions:
                console.print("\n[bold]Did you mean:[/bold]")
                for suggestion in results.suggestions:
                    console.print(f"  • {suggestion}")
            
            return
        
        # Format and display results
        if format == 'json':
            output = {
                'query': query,
                'total': results.total,
                'results': [
                    {
                        'id': r.document_id,
                        'title': r.title,
                        'path': r.path,
                        'score': r.score,
                        'snippet': r.snippet,
                        'format': r.format,
                        'category': r.category,
                        'tags': r.tags
                    }
                    for r in results.results
                ]
            }
            click.echo(json.dumps(output, indent=2))
            
        elif format == 'yaml':
            output = {
                'query': query,
                'total': results.total,
                'results': [
                    {
                        'id': r.document_id,
                        'title': r.title,
                        'path': r.path,
                        'score': r.score,
                        'snippet': r.snippet,
                        'format': r.format,
                        'category': r.category,
                        'tags': r.tags
                    }
                    for r in results.results
                ]
            }
            click.echo(yaml.dump(output, default_flow_style=False))
            
        elif format == 'detailed':
            # Detailed view with snippets and highlights
            console.print(f"\n[bold]Found {results.total} results[/bold]")
            console.print(f"[dim]Showing {len(results.results)} results (offset: {offset})[/dim]\n")
            
            for i, result in enumerate(results.results, 1):
                # Title and path
                title_text = Text(f"{i}. {result.title}", style="bold cyan")
                console.print(title_text)
                console.print(f"   [green]{result.path}[/green]")
                
                # Metadata
                meta_parts = []
                if result.score:
                    meta_parts.append(f"Score: {result.score:.2f}")
                if result.format:
                    meta_parts.append(f"Format: {result.format}")
                if result.category:
                    meta_parts.append(f"Category: {result.category}")
                if result.tags:
                    meta_parts.append(f"Tags: {', '.join(result.tags)}")
                
                if meta_parts:
                    console.print(f"   [dim]{' | '.join(meta_parts)}[/dim]")
                
                # Snippet with highlights
                if show_snippet and result.snippet:
                    snippet = result.snippet
                    if highlight and result.highlights:
                        for term in result.highlights:
                            snippet = snippet.replace(term, f"[bold yellow]{term}[/bold yellow]")
                    
                    console.print(Panel(snippet, box=None, padding=(0, 3)))
                
                console.print()
            
        else:  # table format
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", style="cyan", no_wrap=False)
            table.add_column("Path", style="green")
            table.add_column("Score", style="yellow", justify="right")
            if show_snippet:
                table.add_column("Snippet", style="dim", no_wrap=False, max_width=40)
            
            for i, result in enumerate(results.results, 1):
                row = [
                    str(i),
                    result.title,
                    result.path,
                    f"{result.score:.2f}" if result.score else "-"
                ]
                
                if show_snippet:
                    snippet = result.snippet[:100] + "..." if len(result.snippet) > 100 else result.snippet
                    row.append(snippet)
                
                table.add_row(*row)
            
            console.print(table)
            console.print(f"\n[dim]Showing {len(results.results)} of {results.total} results[/dim]")
        
        # Interactive mode
        if interactive and results.results:
            console.print("\n[bold]Select a result to open (1-{}, q to quit):[/bold]".format(
                len(results.results)
            ))
            
            while True:
                try:
                    choice = console.input("> ").strip().lower()
                    
                    if choice == 'q':
                        break
                    
                    index = int(choice) - 1
                    if 0 <= index < len(results.results):
                        selected = results.results[index]
                        
                        if open:
                            # Open the document
                            open_document(selected.document_id, storage)
                        else:
                            # Show document details
                            show_document_details(selected.document_id, storage)
                        break
                    else:
                        console.print("[red]Invalid selection[/red]")
                        
                except (ValueError, KeyboardInterrupt):
                    break
        
        # Show facets if available
        if results.facets:
            console.print("\n[bold]Facets:[/bold]")
            for field, values in results.facets.items():
                console.print(f"\n  [cyan]{field}:[/cyan]")
                for value, count in values.items():
                    console.print(f"    • {value}: {count}")
        
        # Show search duration
        if results.duration:
            console.print(f"\n[dim]Search completed in {results.duration:.3f}s[/dim]")
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        console.print(f"\n[red]Search failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


def show_document_details(document_id: str, storage: DocumentStore):
    """Show detailed document information"""
    doc = storage.get_document(document_id)
    if not doc:
        console.print(f"[red]Document {document_id} not found[/red]")
        return
    
    console.print("\n[bold]Document Details[/bold]")
    
    table = Table(show_header=False, box=None)
    table.add_column(style="cyan")
    table.add_column()
    
    table.add_row("ID:", doc.id)
    table.add_row("Title:", doc.title)
    table.add_row("Path:", doc.path)
    table.add_row("Format:", doc.format.value)
    table.add_row("Size:", f"{doc.size:,} bytes")
    table.add_row("Created:", doc.created_at.strftime("%Y-%m-%d %H:%M"))
    table.add_row("Modified:", doc.modified_at.strftime("%Y-%m-%d %H:%M"))
    
    if doc.category:
        table.add_row("Category:", doc.category)
    if doc.tags:
        table.add_row("Tags:", ", ".join(doc.tags))
    if doc.metadata:
        table.add_row("Metadata:", str(doc.metadata))
    
    console.print(table)
    
    # Show content preview
    if doc.content:
        console.print("\n[bold]Content Preview:[/bold]")
        preview = doc.content[:500]
        if len(doc.content) > 500:
            preview += "..."
        
        # Syntax highlighting for code
        if doc.format.value in ['code', 'python', 'javascript', 'yaml', 'json']:
            syntax = Syntax(preview, doc.format.value, theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            console.print(Panel(preview, box=None))


def open_document(document_id: str, storage: DocumentStore):
    """Open document in default editor"""
    import subprocess
    import tempfile
    
    doc = storage.get_document(document_id)
    if not doc:
        console.print(f"[red]Document {document_id} not found[/red]")
        return
    
    # Check if original file exists
    from pathlib import Path
    if Path(doc.path).exists():
        file_to_open = doc.path
    else:
        # Create temporary file with content
        suffix = Path(doc.path).suffix
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(doc.content)
            file_to_open = f.name
    
    # Open file
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', file_to_open])
        elif sys.platform.startswith('linux'):
            subprocess.run(['xdg-open', file_to_open])
        elif sys.platform == 'win32':
            subprocess.run(['start', file_to_open], shell=True)
        
        console.print(f"[green]Opened: {doc.title}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to open document: {e}[/red]")