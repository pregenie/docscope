"""Export functionality for DocScope"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime
import logging
import markdown
from jinja2 import Template, Environment, FileSystemLoader

from ..core.models import Document, SearchResult
from ..storage import StorageManager

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats"""
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"


class Exporter:
    """Export documents in various formats"""
    
    def __init__(self, storage_manager: StorageManager = None):
        """Initialize exporter"""
        self.storage = storage_manager
        self.templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        
    def export_document(
        self, 
        document: Union[Document, Dict[str, Any]], 
        format: ExportFormat,
        output_path: Optional[Path] = None
    ) -> Union[str, bytes]:
        """Export a single document"""
        if isinstance(document, Document):
            doc_dict = self._document_to_dict(document)
        else:
            doc_dict = document
            
        if format == ExportFormat.JSON:
            return self._export_json([doc_dict], output_path)
        elif format == ExportFormat.YAML:
            return self._export_yaml([doc_dict], output_path)
        elif format == ExportFormat.MARKDOWN:
            return self._export_markdown([doc_dict], output_path)
        elif format == ExportFormat.HTML:
            return self._export_html([doc_dict], output_path)
        elif format == ExportFormat.PDF:
            return self._export_pdf([doc_dict], output_path)
        elif format == ExportFormat.CSV:
            return self._export_csv([doc_dict], output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def export_documents(
        self,
        documents: List[Union[Document, Dict[str, Any]]],
        format: ExportFormat,
        output_path: Optional[Path] = None
    ) -> Union[str, bytes]:
        """Export multiple documents"""
        doc_dicts = []
        for doc in documents:
            if isinstance(doc, Document):
                doc_dicts.append(self._document_to_dict(doc))
            else:
                doc_dicts.append(doc)
                
        if format == ExportFormat.JSON:
            return self._export_json(doc_dicts, output_path)
        elif format == ExportFormat.YAML:
            return self._export_yaml(doc_dicts, output_path)
        elif format == ExportFormat.MARKDOWN:
            return self._export_markdown(doc_dicts, output_path)
        elif format == ExportFormat.HTML:
            return self._export_html(doc_dicts, output_path)
        elif format == ExportFormat.PDF:
            return self._export_pdf(doc_dicts, output_path)
        elif format == ExportFormat.CSV:
            return self._export_csv(doc_dicts, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def export_search_results(
        self,
        results: SearchResult,
        format: ExportFormat,
        output_path: Optional[Path] = None
    ) -> Union[str, bytes]:
        """Export search results"""
        # Convert search results to document list
        documents = []
        for hit in results.hits:
            doc_dict = {
                'id': hit.doc_id,
                'title': hit.title,
                'path': hit.path,
                'score': hit.score,
                'snippet': hit.snippet,
                'highlights': hit.highlights,
                'metadata': hit.metadata
            }
            documents.append(doc_dict)
            
        # Add search metadata
        export_data = {
            'query': results.query,
            'total': results.total,
            'page': results.page,
            'per_page': results.per_page,
            'search_time': results.search_time,
            'documents': documents,
            'facets': results.facets,
            'suggestions': results.suggestions
        }
        
        if format == ExportFormat.JSON:
            return self._export_json(export_data, output_path)
        elif format == ExportFormat.YAML:
            return self._export_yaml(export_data, output_path)
        elif format == ExportFormat.MARKDOWN:
            return self._export_search_markdown(export_data, output_path)
        elif format == ExportFormat.HTML:
            return self._export_search_html(export_data, output_path)
        else:
            return self.export_documents(documents, format, output_path)
            
    def _document_to_dict(self, document: Document) -> Dict[str, Any]:
        """Convert document model to dictionary"""
        return {
            'id': document.id,
            'title': document.title,
            'content': document.content,
            'path': document.path,
            'format': document.format,
            'size': document.size,
            'hash': document.hash,
            'metadata': document.metadata,
            'created_at': document.created_at.isoformat() if document.created_at else None,
            'updated_at': document.updated_at.isoformat() if document.updated_at else None,
            'scanned_at': document.scanned_at.isoformat() if document.scanned_at else None
        }
        
    def _export_json(self, data: Any, output_path: Optional[Path]) -> str:
        """Export as JSON"""
        json_str = json.dumps(data, indent=2, default=str)
        
        if output_path:
            output_path.write_text(json_str)
            logger.info(f"Exported to JSON: {output_path}")
            
        return json_str
        
    def _export_yaml(self, data: Any, output_path: Optional[Path]) -> str:
        """Export as YAML"""
        yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        
        if output_path:
            output_path.write_text(yaml_str)
            logger.info(f"Exported to YAML: {output_path}")
            
        return yaml_str
        
    def _export_markdown(self, documents: List[Dict], output_path: Optional[Path]) -> str:
        """Export as Markdown"""
        md_lines = ["# Exported Documents\n"]
        md_lines.append(f"*Exported on {datetime.now().isoformat()}*\n")
        
        for doc in documents:
            md_lines.append(f"\n## {doc.get('title', 'Untitled')}\n")
            md_lines.append(f"- **Path**: `{doc.get('path', 'N/A')}`")
            md_lines.append(f"- **Format**: {doc.get('format', 'N/A')}")
            md_lines.append(f"- **Size**: {doc.get('size', 0)} bytes")
            
            if doc.get('metadata'):
                md_lines.append("\n### Metadata")
                for key, value in doc['metadata'].items():
                    md_lines.append(f"- **{key}**: {value}")
                    
            if doc.get('content'):
                md_lines.append("\n### Content")
                md_lines.append("```")
                md_lines.append(doc['content'][:1000])  # First 1000 chars
                if len(doc['content']) > 1000:
                    md_lines.append("... (truncated)")
                md_lines.append("```")
                
        md_str = "\n".join(md_lines)
        
        if output_path:
            output_path.write_text(md_str)
            logger.info(f"Exported to Markdown: {output_path}")
            
        return md_str
        
    def _export_html(self, documents: List[Dict], output_path: Optional[Path]) -> str:
        """Export as HTML"""
        # Create HTML template if not exists
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>DocScope Export</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .document { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
        .metadata { background: #f5f5f5; padding: 10px; margin: 10px 0; }
        pre { background: #f0f0f0; padding: 10px; overflow-x: auto; }
        h2 { color: #333; }
        .path { color: #666; font-family: monospace; }
    </style>
</head>
<body>
    <h1>DocScope Export</h1>
    <p><em>Exported on {{ export_date }}</em></p>
    {% for doc in documents %}
    <div class="document">
        <h2>{{ doc.title or 'Untitled' }}</h2>
        <div class="path">{{ doc.path }}</div>
        {% if doc.metadata %}
        <div class="metadata">
            <h3>Metadata</h3>
            <ul>
            {% for key, value in doc.metadata.items() %}
                <li><strong>{{ key }}:</strong> {{ value }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        {% if doc.content %}
        <h3>Content Preview</h3>
        <pre>{{ doc.content[:1000] }}{% if doc.content|length > 1000 %}... (truncated){% endif %}</pre>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
        """
        
        template = Template(html_template)
        html_str = template.render(
            documents=documents,
            export_date=datetime.now().isoformat()
        )
        
        if output_path:
            output_path.write_text(html_str)
            logger.info(f"Exported to HTML: {output_path}")
            
        return html_str
        
    def _export_pdf(self, documents: List[Dict], output_path: Optional[Path]) -> bytes:
        """Export as PDF"""
        # First convert to HTML
        html_str = self._export_html(documents, None)
        
        try:
            import weasyprint
            pdf_bytes = weasyprint.HTML(string=html_str).write_pdf()
            
            if output_path:
                output_path.write_bytes(pdf_bytes)
                logger.info(f"Exported to PDF: {output_path}")
                
            return pdf_bytes
            
        except ImportError:
            logger.error("PDF export requires weasyprint: pip install weasyprint")
            raise ImportError("PDF export requires weasyprint package")
            
    def _export_csv(self, documents: List[Dict], output_path: Optional[Path]) -> str:
        """Export as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        
        # Define CSV columns
        fieldnames = ['id', 'title', 'path', 'format', 'size', 'created_at', 'updated_at']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for doc in documents:
            row = {k: doc.get(k, '') for k in fieldnames}
            writer.writerow(row)
            
        csv_str = output.getvalue()
        
        if output_path:
            output_path.write_text(csv_str)
            logger.info(f"Exported to CSV: {output_path}")
            
        return csv_str
        
    def _export_search_markdown(self, data: Dict, output_path: Optional[Path]) -> str:
        """Export search results as Markdown"""
        md_lines = ["# Search Results\n"]
        md_lines.append(f"**Query**: `{data['query']}`")
        md_lines.append(f"**Total Results**: {data['total']}")
        md_lines.append(f"**Search Time**: {data['search_time']:.3f}s\n")
        
        if data.get('facets'):
            md_lines.append("## Facets\n")
            for facet_name, facet_values in data['facets'].items():
                md_lines.append(f"### {facet_name}")
                for value, count in facet_values.items():
                    md_lines.append(f"- {value}: {count}")
                md_lines.append("")
                
        md_lines.append("## Results\n")
        for doc in data['documents']:
            md_lines.append(f"### {doc.get('title', 'Untitled')} (Score: {doc.get('score', 0):.2f})")
            md_lines.append(f"- **Path**: `{doc.get('path', 'N/A')}`")
            
            if doc.get('snippet'):
                md_lines.append(f"\n{doc['snippet']}\n")
                
        md_str = "\n".join(md_lines)
        
        if output_path:
            output_path.write_text(md_str)
            logger.info(f"Exported search results to Markdown: {output_path}")
            
        return md_str
        
    def _export_search_html(self, data: Dict, output_path: Optional[Path]) -> str:
        """Export search results as HTML"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Search Results - {{ query }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .stats { background: #f0f0f0; padding: 10px; margin: 20px 0; }
        .result { border-left: 3px solid #007bff; padding: 10px; margin: 15px 0; }
        .score { color: #666; font-size: 0.9em; }
        .snippet { margin: 10px 0; color: #333; }
        .highlight { background: yellow; }
        .facets { background: #f8f9fa; padding: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Search Results</h1>
    <div class="stats">
        <strong>Query:</strong> {{ query }}<br>
        <strong>Total Results:</strong> {{ total }}<br>
        <strong>Search Time:</strong> {{ "%.3f"|format(search_time) }}s
    </div>
    
    {% if facets %}
    <div class="facets">
        <h2>Filters</h2>
        {% for facet_name, facet_values in facets.items() %}
        <h3>{{ facet_name }}</h3>
        <ul>
        {% for value, count in facet_values.items() %}
            <li>{{ value }} ({{ count }})</li>
        {% endfor %}
        </ul>
        {% endfor %}
    </div>
    {% endif %}
    
    <h2>Results</h2>
    {% for doc in documents %}
    <div class="result">
        <h3>{{ doc.title or 'Untitled' }} <span class="score">Score: {{ "%.2f"|format(doc.score) }}</span></h3>
        <div class="path">{{ doc.path }}</div>
        {% if doc.snippet %}
        <div class="snippet">{{ doc.snippet }}</div>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
        """
        
        template = Template(html_template)
        html_str = template.render(**data)
        
        if output_path:
            output_path.write_text(html_str)
            logger.info(f"Exported search results to HTML: {output_path}")
            
        return html_str