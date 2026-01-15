"""PDF Scanner Plugin for DocScope"""

from pathlib import Path
from typing import Dict, Any
import logging

from ..base import ScannerPlugin, PluginMetadata, PluginCapability

logger = logging.getLogger(__name__)


class PDFScannerPlugin(ScannerPlugin):
    """Plugin for scanning PDF documents"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_formats = ['.pdf']
        self.extract_images = config.get('extract_images', False) if config else False
        self.extract_metadata = config.get('extract_metadata', True) if config else True
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="pdf_scanner",
            version="1.0.0",
            author="DocScope Team",
            description="Scan and extract text from PDF documents",
            website="https://github.com/docscope/pdf-scanner",
            license="MIT",
            dependencies=["pip:PyPDF2"],
            capabilities=[PluginCapability.SCANNER],
            tags=["pdf", "scanner", "document"],
            config_schema={
                'extract_images': {
                    'type': bool,
                    'default': False,
                    'description': 'Extract images from PDFs'
                },
                'extract_metadata': {
                    'type': bool,
                    'default': True,
                    'description': 'Extract PDF metadata'
                }
            }
        )
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            # Try to import PyPDF2
            import PyPDF2
            self.PyPDF2 = PyPDF2
            logger.info("PDF Scanner plugin initialized successfully")
            return True
        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return False
    
    def shutdown(self) -> None:
        """Cleanup when plugin is disabled"""
        logger.info("PDF Scanner plugin shutdown")
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this plugin can handle the given file"""
        return file_path.suffix.lower() == '.pdf'
    
    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Scan a PDF file and extract text"""
        if not self.can_handle(file_path):
            raise ValueError(f"Cannot handle file: {file_path}")
        
        try:
            import PyPDF2
            
            text_content = []
            metadata = {}
            
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract metadata
                if self.extract_metadata:
                    pdf_metadata = pdf_reader.metadata
                    if pdf_metadata:
                        metadata = {
                            'title': pdf_metadata.get('/Title', ''),
                            'author': pdf_metadata.get('/Author', ''),
                            'subject': pdf_metadata.get('/Subject', ''),
                            'creator': pdf_metadata.get('/Creator', ''),
                            'producer': pdf_metadata.get('/Producer', ''),
                            'creation_date': str(pdf_metadata.get('/CreationDate', '')),
                            'modification_date': str(pdf_metadata.get('/ModDate', ''))
                        }
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- Page {page_num} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
            
            # Prepare result
            full_text = "\n\n".join(text_content)
            
            result = {
                'title': metadata.get('title') or file_path.stem,
                'content': full_text,
                'format': 'pdf',
                'metadata': {
                    **metadata,
                    'page_count': len(pdf_reader.pages),
                    'plugin': 'pdf_scanner'
                }
            }
            
            logger.info(f"Successfully scanned PDF: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to scan PDF file {file_path}: {e}")
            raise