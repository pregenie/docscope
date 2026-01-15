"""File system watcher for DocScope"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from ..scanner import Scanner
from ..storage import StorageManager
from ..search import SearchIndex

logger = logging.getLogger(__name__)


class WatchEventType(Enum):
    """Types of file system events"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class WatchEvent:
    """File system watch event"""
    type: WatchEventType
    path: Path
    old_path: Optional[Path] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class DocScopeEventHandler(FileSystemEventHandler):
    """Handle file system events for DocScope"""
    
    def __init__(self, watcher: 'FileWatcher'):
        self.watcher = watcher
        
    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        if not event.is_directory:
            path = Path(event.src_path)
            if self.watcher.should_process(path):
                watch_event = WatchEvent(
                    type=WatchEventType.CREATED,
                    path=path
                )
                self.watcher.handle_event(watch_event)
                
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if not event.is_directory:
            path = Path(event.src_path)
            if self.watcher.should_process(path):
                watch_event = WatchEvent(
                    type=WatchEventType.MODIFIED,
                    path=path
                )
                self.watcher.handle_event(watch_event)
                
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion"""
        if not event.is_directory:
            path = Path(event.src_path)
            watch_event = WatchEvent(
                type=WatchEventType.DELETED,
                path=path
            )
            self.watcher.handle_event(watch_event)
            
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename"""
        if not event.is_directory:
            old_path = Path(event.src_path)
            new_path = Path(event.dest_path)
            
            if self.watcher.should_process(new_path):
                watch_event = WatchEvent(
                    type=WatchEventType.MOVED,
                    path=new_path,
                    old_path=old_path
                )
                self.watcher.handle_event(watch_event)


class FileWatcher:
    """Watch file system for changes and auto-index"""
    
    def __init__(
        self,
        scanner: Scanner = None,
        storage: StorageManager = None,
        search_index: SearchIndex = None,
        debounce_seconds: float = 1.0
    ):
        """Initialize file watcher"""
        self.scanner = scanner
        self.storage = storage
        self.search_index = search_index
        self.debounce_seconds = debounce_seconds
        
        self.observer = Observer()
        self.watched_paths: Dict[str, Any] = {}
        self.event_queue: List[WatchEvent] = []
        self.event_handlers: Dict[WatchEventType, List[Callable]] = {
            WatchEventType.CREATED: [],
            WatchEventType.MODIFIED: [],
            WatchEventType.DELETED: [],
            WatchEventType.MOVED: []
        }
        
        self.ignore_patterns: Set[str] = {
            '*.pyc', '__pycache__', '.git', '.svn',
            'node_modules', '.DS_Store', 'Thumbs.db'
        }
        
        self.running = False
        self.process_thread = None
        self.process_lock = threading.Lock()
        self.pending_events: Dict[Path, WatchEvent] = {}
        
    def watch(self, path: Path, recursive: bool = True) -> bool:
        """Add a path to watch"""
        try:
            path = Path(path).resolve()
            
            if not path.exists():
                logger.error(f"Path does not exist: {path}")
                return False
                
            handler = DocScopeEventHandler(self)
            self.observer.schedule(handler, str(path), recursive=recursive)
            
            self.watched_paths[str(path)] = {
                'recursive': recursive,
                'handler': handler
            }
            
            logger.info(f"Watching path: {path} (recursive={recursive})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to watch path {path}: {e}")
            return False
            
    def unwatch(self, path: Path) -> bool:
        """Remove a path from watching"""
        try:
            path_str = str(Path(path).resolve())
            
            if path_str in self.watched_paths:
                # Remove from observer
                self.observer.unschedule_all()
                del self.watched_paths[path_str]
                
                # Re-add remaining paths
                for watched_path, info in self.watched_paths.items():
                    self.observer.schedule(
                        info['handler'],
                        watched_path,
                        recursive=info['recursive']
                    )
                    
                logger.info(f"Stopped watching: {path}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to unwatch path {path}: {e}")
            return False
            
    def start(self) -> bool:
        """Start watching"""
        if self.running:
            logger.warning("Watcher already running")
            return False
            
        try:
            self.running = True
            self.observer.start()
            
            # Start event processing thread
            self.process_thread = threading.Thread(
                target=self._process_events,
                daemon=True
            )
            self.process_thread.start()
            
            logger.info("File watcher started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start watcher: {e}")
            self.running = False
            return False
            
    def stop(self):
        """Stop watching"""
        if not self.running:
            return
            
        self.running = False
        self.observer.stop()
        self.observer.join(timeout=5)
        
        if self.process_thread:
            self.process_thread.join(timeout=5)
            
        logger.info("File watcher stopped")
        
    def should_process(self, path: Path) -> bool:
        """Check if a file should be processed"""
        # Check ignore patterns
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return False
                
        # Check file extension
        if self.scanner:
            # Use scanner's format detection
            return self.scanner.detect_format(path) is not None
            
        # Default: process all files
        return True
        
    def handle_event(self, event: WatchEvent):
        """Handle a watch event"""
        with self.process_lock:
            # Debounce events - only keep the latest for each path
            self.pending_events[event.path] = event
            
    def _process_events(self):
        """Process pending events (runs in separate thread)"""
        while self.running:
            time.sleep(self.debounce_seconds)
            
            with self.process_lock:
                if not self.pending_events:
                    continue
                    
                # Process all pending events
                events = list(self.pending_events.values())
                self.pending_events.clear()
                
            for event in events:
                try:
                    self._process_single_event(event)
                except Exception as e:
                    logger.error(f"Error processing event {event}: {e}")
                    
    def _process_single_event(self, event: WatchEvent):
        """Process a single watch event"""
        logger.debug(f"Processing event: {event.type} for {event.path}")
        
        # Call registered handlers
        for handler in self.event_handlers[event.type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                
        # Auto-index if components are available
        if event.type == WatchEventType.CREATED:
            self._handle_created(event)
        elif event.type == WatchEventType.MODIFIED:
            self._handle_modified(event)
        elif event.type == WatchEventType.DELETED:
            self._handle_deleted(event)
        elif event.type == WatchEventType.MOVED:
            self._handle_moved(event)
            
    def _handle_created(self, event: WatchEvent):
        """Handle file creation"""
        if not self.scanner or not self.storage:
            return
            
        try:
            # Scan the new file
            result = self.scanner.scan_file(event.path)
            
            if result:
                # Store in database
                document = self.storage.create_document(result)
                
                # Index for search
                if self.search_index and document:
                    self.search_index.index_document(document)
                    
                logger.info(f"Auto-indexed new file: {event.path}")
                
        except Exception as e:
            logger.error(f"Failed to index new file {event.path}: {e}")
            
    def _handle_modified(self, event: WatchEvent):
        """Handle file modification"""
        if not self.scanner or not self.storage:
            return
            
        try:
            # Re-scan the file
            result = self.scanner.scan_file(event.path)
            
            if result:
                # Update in database
                existing = self.storage.get_document_by_path(str(event.path))
                
                if existing:
                    # Update existing document
                    self.storage.update_document(existing.id, result)
                    
                    # Re-index for search
                    if self.search_index:
                        self.search_index.update_document(existing.id, result)
                else:
                    # Create new document
                    document = self.storage.create_document(result)
                    
                    if self.search_index and document:
                        self.search_index.index_document(document)
                        
                logger.info(f"Auto-indexed modified file: {event.path}")
                
        except Exception as e:
            logger.error(f"Failed to index modified file {event.path}: {e}")
            
    def _handle_deleted(self, event: WatchEvent):
        """Handle file deletion"""
        if not self.storage:
            return
            
        try:
            # Find document in database
            document = self.storage.get_document_by_path(str(event.path))
            
            if document:
                # Remove from search index
                if self.search_index:
                    self.search_index.delete_document(document.id)
                    
                # Remove from database
                self.storage.delete_document(document.id)
                
                logger.info(f"Removed deleted file from index: {event.path}")
                
        except Exception as e:
            logger.error(f"Failed to remove deleted file {event.path}: {e}")
            
    def _handle_moved(self, event: WatchEvent):
        """Handle file move/rename"""
        if not self.storage:
            return
            
        try:
            # Find document by old path
            document = self.storage.get_document_by_path(str(event.old_path))
            
            if document:
                # Update path
                update_data = {'path': str(event.path)}
                
                # Re-scan if scanner available
                if self.scanner:
                    result = self.scanner.scan_file(event.path)
                    if result:
                        update_data.update(result)
                        
                # Update in database
                self.storage.update_document(document.id, update_data)
                
                # Update in search index
                if self.search_index:
                    self.search_index.update_document(document.id, update_data)
                    
                logger.info(f"Updated moved file: {event.old_path} -> {event.path}")
                
        except Exception as e:
            logger.error(f"Failed to update moved file: {e}")
            
    def add_handler(self, event_type: WatchEventType, handler: Callable):
        """Add an event handler"""
        self.event_handlers[event_type].append(handler)
        
    def remove_handler(self, event_type: WatchEventType, handler: Callable):
        """Remove an event handler"""
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            
    def set_ignore_patterns(self, patterns: Set[str]):
        """Set ignore patterns"""
        self.ignore_patterns = patterns
        
    def get_status(self) -> Dict[str, Any]:
        """Get watcher status"""
        return {
            'running': self.running,
            'watched_paths': list(self.watched_paths.keys()),
            'pending_events': len(self.pending_events),
            'ignore_patterns': list(self.ignore_patterns)
        }