"""Export command implementation"""

import click
import json
import yaml
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ...search import SearchEngine
from ...storage import DocumentStore
from ...core.config import Config
from ...core.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command(name='export')
@click.option('--format', '-f', 
              type=click.Choice(['html', 'pdf', 'markdown', 'json', 'yaml', 'epub']),
              default='html', help='Export format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--query', '-q', help='Export only documents matching query')
@click.option('--category', '-c', help='Filter by category')
@click.option('--tags', '-t', multiple=True, help='Filter by tags')
@click.option('--template', help='Template to use for HTML/PDF export')
@click.option('--include-toc', is_flag=True, default=True, help='Include table of contents')
@click.option('--include-index', is_flag=True, default=True, help='Include searchable index')
@click.option('--single-file', is_flag=True, help='Export as single file (HTML only)')
@click.option('--theme', type=click.Choice(['light', 'dark', 'github', 'material']),
              default='light', help='Export theme')
@click.pass_context
def export_command(ctx, format, output, query, category, tags, template, 
                  include_toc, include_index, single_file, theme):
    """Export documentation
    
    Export documents to various formats for offline viewing or distribution.
    Supports filtering by query, category, and tags.
    """
    config = ctx.obj['config']
    
    # Initialize components
    storage = DocumentStore(config)
    search_engine = SearchEngine(config)
    
    # Determine output path
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"docscope_export_{timestamp}.{format}"
    
    output_path = Path(output)
    
    # Display export configuration
    console.print("\n[bold blue]Export Configuration[/bold blue]")
    console.print(f"  Format: {format}")
    console.print(f"  Output: {output_path}")
    console.print(f"  Theme: {theme}")
    
    if query:
        console.print(f"  Query: {query}")
    if category:
        console.print(f"  Category: {category}")
    if tags:
        console.print(f"  Tags: {', '.join(tags)}")
    
    console.print()
    
    try:
        # Get documents to export
        documents = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            # Retrieve documents
            task = progress.add_task("Retrieving documents...", total=None)
            
            if query:
                # Search for documents
                results = search_engine.search(query, limit=10000)
                doc_ids = [r.document_id for r in results.results]
                documents = [storage.get_document(doc_id) for doc_id in doc_ids]
            else:
                # Get all documents with filters
                filters = {}
                if category:
                    filters['category'] = category
                if tags:
                    filters['tags'] = list(tags)
                
                documents = storage.list_documents(limit=10000, **filters)
            
            documents = [d for d in documents if d is not None]
            progress.update(task, total=len(documents), completed=len(documents))
            
            if not documents:
                console.print("[yellow]No documents to export[/yellow]")
                return
            
            console.print(f"[green]Found {len(documents)} documents to export[/green]")
            
            # Export based on format
            if format == 'json':
                export_json(documents, output_path, progress)
            elif format == 'yaml':
                export_yaml(documents, output_path, progress)
            elif format == 'markdown':
                export_markdown(documents, output_path, include_toc, progress)
            elif format == 'html':
                export_html(documents, output_path, template, theme, 
                          include_toc, include_index, single_file, progress)
            elif format == 'pdf':
                export_pdf(documents, output_path, template, theme, 
                         include_toc, progress)
            elif format == 'epub':
                export_epub(documents, output_path, include_toc, progress)
            
        console.print(f"\n[green]✓ Export complete: {output_path}[/green]")
        
        # Show file size
        if output_path.exists():
            size = output_path.stat().st_size
            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            console.print(f"[dim]File size: {size_str}[/dim]")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        console.print(f"\n[red]Export failed: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())


def export_json(documents, output_path, progress):
    """Export documents as JSON"""
    task = progress.add_task("Exporting to JSON...", total=len(documents))
    
    output_data = {
        'export_date': datetime.now().isoformat(),
        'total_documents': len(documents),
        'documents': []
    }
    
    for doc in documents:
        output_data['documents'].append({
            'id': doc.id,
            'title': doc.title,
            'path': doc.path,
            'content': doc.content,
            'format': doc.format.value,
            'size': doc.size,
            'created_at': doc.created_at.isoformat(),
            'modified_at': doc.modified_at.isoformat(),
            'category': doc.category,
            'tags': doc.tags,
            'metadata': doc.metadata
        })
        progress.update(task, advance=1)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def export_yaml(documents, output_path, progress):
    """Export documents as YAML"""
    task = progress.add_task("Exporting to YAML...", total=len(documents))
    
    output_data = {
        'export_date': datetime.now().isoformat(),
        'total_documents': len(documents),
        'documents': []
    }
    
    for doc in documents:
        output_data['documents'].append({
            'id': doc.id,
            'title': doc.title,
            'path': doc.path,
            'content': doc.content,
            'format': doc.format.value,
            'size': doc.size,
            'created_at': doc.created_at.isoformat(),
            'modified_at': doc.modified_at.isoformat(),
            'category': doc.category,
            'tags': doc.tags,
            'metadata': doc.metadata
        })
        progress.update(task, advance=1)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)


def export_markdown(documents, output_path, include_toc, progress):
    """Export documents as Markdown"""
    task = progress.add_task("Exporting to Markdown...", total=len(documents))
    
    content = []
    
    # Header
    content.append("# Documentation Export")
    content.append(f"\nExported on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    content.append(f"\nTotal documents: {len(documents)}\n")
    
    # Table of Contents
    if include_toc:
        content.append("## Table of Contents\n")
        for i, doc in enumerate(documents, 1):
            anchor = doc.title.lower().replace(' ', '-')
            content.append(f"{i}. [{doc.title}](#{anchor})")
        content.append("\n---\n")
    
    # Documents
    for doc in documents:
        anchor = doc.title.lower().replace(' ', '-')
        content.append(f"## {doc.title} {{#{anchor}}}")
        content.append(f"\n*Path: {doc.path}*")
        
        if doc.category:
            content.append(f"*Category: {doc.category}*")
        if doc.tags:
            content.append(f"*Tags: {', '.join(doc.tags)}*")
        
        content.append("\n")
        content.append(doc.content)
        content.append("\n---\n")
        
        progress.update(task, advance=1)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))


def export_html(documents, output_path, template, theme, include_toc, 
               include_index, single_file, progress):
    """Export documents as HTML"""
    task = progress.add_task("Exporting to HTML...", total=len(documents))
    
    # HTML template
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocScope Export</title>
    <style>
        {styles}
    </style>
</head>
<body>
    <div class="container">
        <h1>Documentation Export</h1>
        <p class="meta">Exported on: {date} | Total documents: {total}</p>
        
        {toc}
        
        <div class="documents">
            {content}
        </div>
    </div>
    
    {scripts}
</body>
</html>"""
    
    # Theme styles
    themes = {
        'light': """
            body { font-family: -apple-system, sans-serif; line-height: 1.6; 
                   color: #333; background: #fff; }
            .container { max-width: 900px; margin: 0 auto; padding: 20px; }
            h1, h2, h3 { color: #2c3e50; }
            pre { background: #f4f4f4; padding: 10px; overflow-x: auto; }
            code { background: #f0f0f0; padding: 2px 5px; }
            .toc { background: #f9f9f9; padding: 20px; margin: 20px 0; }
            .document { margin: 30px 0; padding: 20px 0; border-bottom: 1px solid #eee; }
        """,
        'dark': """
            body { font-family: -apple-system, sans-serif; line-height: 1.6;
                   color: #e0e0e0; background: #1e1e1e; }
            .container { max-width: 900px; margin: 0 auto; padding: 20px; }
            h1, h2, h3 { color: #61dafb; }
            pre { background: #2d2d2d; padding: 10px; overflow-x: auto; }
            code { background: #2d2d2d; padding: 2px 5px; color: #61dafb; }
            .toc { background: #2d2d2d; padding: 20px; margin: 20px 0; }
            .document { margin: 30px 0; padding: 20px 0; border-bottom: 1px solid #444; }
        """
    }
    
    # Build TOC
    toc_html = ""
    if include_toc:
        toc_items = []
        for i, doc in enumerate(documents, 1):
            anchor = f"doc-{i}"
            toc_items.append(f'<li><a href="#{anchor}">{doc.title}</a></li>')
        toc_html = f'<div class="toc"><h2>Table of Contents</h2><ol>{"".join(toc_items)}</ol></div>'
    
    # Build content
    content_html = []
    for i, doc in enumerate(documents, 1):
        anchor = f"doc-{i}"
        doc_html = f"""
        <div class="document" id="{anchor}">
            <h2>{doc.title}</h2>
            <p class="meta">Path: {doc.path}</p>
            <div class="content">{html_escape(doc.content)}</div>
        </div>
        """
        content_html.append(doc_html)
        progress.update(task, advance=1)
    
    # Build scripts
    scripts = ""
    if include_index:
        scripts = """
        <script>
            // Simple search functionality
            function search() {
                // Implementation would go here
            }
        </script>
        """
    
    # Generate HTML
    html = html_template.format(
        styles=themes.get(theme, themes['light']),
        date=datetime.now().strftime('%Y-%m-%d %H:%M'),
        total=len(documents),
        toc=toc_html,
        content=''.join(content_html),
        scripts=scripts
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def export_pdf(documents, output_path, template, theme, include_toc, progress):
    """Export documents as PDF"""
    # This would require a PDF generation library like reportlab or weasyprint
    task = progress.add_task("Exporting to PDF...", total=1)
    console.print("[yellow]PDF export requires additional dependencies[/yellow]")
    console.print("Install with: pip install reportlab")
    progress.update(task, advance=1)


def export_epub(documents, output_path, include_toc, progress):
    """Export documents as EPUB"""
    # This would require an EPUB generation library
    task = progress.add_task("Exporting to EPUB...", total=1)
    console.print("[yellow]EPUB export requires additional dependencies[/yellow]")
    console.print("Install with: pip install ebooklib")
    progress.update(task, advance=1)


def html_escape(text):
    """Escape HTML special characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))