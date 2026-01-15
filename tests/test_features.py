"""Tests for Advanced Features"""

import pytest
import json
import yaml
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from docscope.features import (
    Exporter,
    ExportFormat,
    FileWatcher,
    WatchEvent,
    WatchEventType,
    PerformanceMonitor,
    HealthChecker
)
from docscope.core.models import Document, SearchResult, SearchHit


class TestExporter:
    """Test export functionality"""
    
    @pytest.fixture
    def exporter(self):
        """Create exporter instance"""
        return Exporter()
    
    @pytest.fixture
    def sample_document(self):
        """Create sample document"""
        return {
            'id': '1',
            'title': 'Test Document',
            'content': 'This is test content',
            'path': '/test/doc.md',
            'format': 'markdown',
            'size': 100,
            'metadata': {'author': 'Test'}
        }
    
    def test_export_json(self, exporter, sample_document):
        """Test JSON export"""
        result = exporter.export_document(sample_document, ExportFormat.JSON)
        
        # Parse JSON to verify
        data = json.loads(result)
        assert data[0]['title'] == 'Test Document'
        assert data[0]['content'] == 'This is test content'
    
    def test_export_yaml(self, exporter, sample_document):
        """Test YAML export"""
        result = exporter.export_document(sample_document, ExportFormat.YAML)
        
        # Parse YAML to verify
        data = yaml.safe_load(result)
        assert data[0]['title'] == 'Test Document'
        assert data[0]['format'] == 'markdown'
    
    def test_export_markdown(self, exporter, sample_document):
        """Test Markdown export"""
        result = exporter.export_document(sample_document, ExportFormat.MARKDOWN)
        
        assert '# Exported Documents' in result
        assert 'Test Document' in result
        assert '/test/doc.md' in result
    
    def test_export_html(self, exporter, sample_document):
        """Test HTML export"""
        result = exporter.export_document(sample_document, ExportFormat.HTML)
        
        assert '<html>' in result
        assert 'Test Document' in result
        assert 'DocScope Export' in result
    
    def test_export_csv(self, exporter, sample_document):
        """Test CSV export"""
        result = exporter.export_document(sample_document, ExportFormat.CSV)
        
        lines = result.strip().split('\n')
        assert len(lines) == 2  # Header + 1 row
        assert 'title' in lines[0]
        assert 'Test Document' in lines[1]
    
    def test_export_multiple_documents(self, exporter):
        """Test exporting multiple documents"""
        documents = [
            {'id': '1', 'title': 'Doc 1', 'content': 'Content 1'},
            {'id': '2', 'title': 'Doc 2', 'content': 'Content 2'}
        ]
        
        result = exporter.export_documents(documents, ExportFormat.JSON)
        data = json.loads(result)
        
        assert len(data) == 2
        assert data[0]['title'] == 'Doc 1'
        assert data[1]['title'] == 'Doc 2'
    
    def test_export_search_results(self, exporter):
        """Test exporting search results"""
        # Create mock search results
        hits = [
            SearchHit(
                doc_id='1',
                title='Result 1',
                path='/test1.md',
                score=0.95,
                snippet='Test snippet 1'
            ),
            SearchHit(
                doc_id='2',
                title='Result 2',
                path='/test2.md',
                score=0.85,
                snippet='Test snippet 2'
            )
        ]
        
        results = SearchResult(
            query='test query',
            hits=hits,
            total=2,
            page=1,
            per_page=10,
            search_time=0.123
        )
        
        # Export as JSON
        json_result = exporter.export_search_results(results, ExportFormat.JSON)
        data = json.loads(json_result)
        
        assert data['query'] == 'test query'
        assert data['total'] == 2
        assert len(data['documents']) == 2
        assert data['documents'][0]['title'] == 'Result 1'
    
    def test_export_to_file(self, exporter, sample_document):
        """Test exporting to file"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Export to file
            exporter.export_document(sample_document, ExportFormat.JSON, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify content
            data = json.loads(output_path.read_text())
            assert data[0]['title'] == 'Test Document'
            
        finally:
            output_path.unlink()


class TestFileWatcher:
    """Test file system watcher"""
    
    @pytest.fixture
    def watcher(self):
        """Create watcher instance"""
        return FileWatcher()
    
    def test_watch_path(self, watcher):
        """Test adding path to watch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            
            # Add path to watch
            result = watcher.watch(path)
            assert result == True
            assert str(path.resolve()) in watcher.watched_paths
    
    def test_unwatch_path(self, watcher):
        """Test removing path from watch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            
            # Add and remove path
            watcher.watch(path)
            result = watcher.unwatch(path)
            
            assert result == True
            assert str(path.resolve()) not in watcher.watched_paths
    
    def test_should_process(self, watcher):
        """Test file processing filter"""
        # Set ignore patterns
        watcher.ignore_patterns = {'*.pyc', '__pycache__', '.git'}
        
        # Test ignored files
        assert watcher.should_process(Path('test.pyc')) == False
        assert watcher.should_process(Path('__pycache__/file.py')) == False
        assert watcher.should_process(Path('.git/config')) == False
        
        # Test allowed files
        assert watcher.should_process(Path('test.py')) == True
        assert watcher.should_process(Path('doc.md')) == True
    
    def test_event_handling(self, watcher):
        """Test event handling"""
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        # Add handler
        watcher.add_handler(WatchEventType.CREATED, handler)
        
        # Create event
        event = WatchEvent(
            type=WatchEventType.CREATED,
            path=Path('/test/file.txt')
        )
        
        # Process event
        watcher._process_single_event(event)
        
        # Verify handler was called
        assert len(events_received) == 1
        assert events_received[0] == event
    
    def test_event_debouncing(self, watcher):
        """Test event debouncing"""
        watcher.debounce_seconds = 0.1
        
        path = Path('/test/file.txt')
        
        # Add multiple events for same path
        event1 = WatchEvent(type=WatchEventType.MODIFIED, path=path)
        event2 = WatchEvent(type=WatchEventType.MODIFIED, path=path)
        event3 = WatchEvent(type=WatchEventType.MODIFIED, path=path)
        
        watcher.handle_event(event1)
        watcher.handle_event(event2)
        watcher.handle_event(event3)
        
        # Should only keep the last event
        assert len(watcher.pending_events) == 1
        assert watcher.pending_events[path] == event3
    
    @patch('docscope.features.watcher.Observer')
    def test_start_stop(self, mock_observer, watcher):
        """Test starting and stopping watcher"""
        # Start watcher
        result = watcher.start()
        assert result == True
        assert watcher.running == True
        
        # Stop watcher
        watcher.stop()
        assert watcher.running == False
    
    def test_auto_index_created(self, watcher):
        """Test auto-indexing on file creation"""
        # Create mocks
        mock_scanner = Mock()
        mock_storage = Mock()
        mock_search = Mock()
        
        watcher.scanner = mock_scanner
        watcher.storage = mock_storage
        watcher.search_index = mock_search
        
        # Mock scan result
        scan_result = {'title': 'New File', 'content': 'Content'}
        mock_scanner.scan_file.return_value = scan_result
        
        # Mock storage
        mock_document = Mock(id='123')
        mock_storage.create_document.return_value = mock_document
        
        # Create event
        event = WatchEvent(
            type=WatchEventType.CREATED,
            path=Path('/test/new.md')
        )
        
        # Process event
        watcher._handle_created(event)
        
        # Verify calls
        mock_scanner.scan_file.assert_called_once_with(event.path)
        mock_storage.create_document.assert_called_once_with(scan_result)
        mock_search.index_document.assert_called_once_with(mock_document)
    
    def test_auto_index_modified(self, watcher):
        """Test auto-indexing on file modification"""
        # Create mocks
        mock_scanner = Mock()
        mock_storage = Mock()
        mock_search = Mock()
        
        watcher.scanner = mock_scanner
        watcher.storage = mock_storage
        watcher.search_index = mock_search
        
        # Mock existing document
        mock_document = Mock(id='123')
        mock_storage.get_document_by_path.return_value = mock_document
        
        # Mock scan result
        scan_result = {'title': 'Modified File', 'content': 'New Content'}
        mock_scanner.scan_file.return_value = scan_result
        
        # Create event
        event = WatchEvent(
            type=WatchEventType.MODIFIED,
            path=Path('/test/existing.md')
        )
        
        # Process event
        watcher._handle_modified(event)
        
        # Verify calls
        mock_scanner.scan_file.assert_called_once_with(event.path)
        mock_storage.update_document.assert_called_once_with('123', scan_result)
        mock_search.update_document.assert_called_once()
    
    def test_auto_index_deleted(self, watcher):
        """Test auto-indexing on file deletion"""
        # Create mocks
        mock_storage = Mock()
        mock_search = Mock()
        
        watcher.storage = mock_storage
        watcher.search_index = mock_search
        
        # Mock existing document
        mock_document = Mock(id='123')
        mock_storage.get_document_by_path.return_value = mock_document
        
        # Create event
        event = WatchEvent(
            type=WatchEventType.DELETED,
            path=Path('/test/deleted.md')
        )
        
        # Process event
        watcher._handle_deleted(event)
        
        # Verify calls
        mock_search.delete_document.assert_called_once_with('123')
        mock_storage.delete_document.assert_called_once_with('123')


class TestPerformanceMonitor:
    """Test performance monitoring"""
    
    @pytest.fixture
    def monitor(self):
        """Create monitor instance"""
        return PerformanceMonitor()
    
    def test_record_metric(self, monitor):
        """Test recording metrics"""
        monitor.record_metric('test_metric', 42.5, 'ms')
        
        assert 'test_metric' in monitor.metrics
        assert len(monitor.metrics['test_metric']) == 1
        assert monitor.metrics['test_metric'][0].value == 42.5
        assert monitor.metrics['test_metric'][0].unit == 'ms'
    
    def test_increment_counter(self, monitor):
        """Test counter metrics"""
        monitor.increment_counter('requests')
        monitor.increment_counter('requests')
        monitor.increment_counter('requests', 3)
        
        assert monitor.get_counter('requests') == 5
    
    def test_measure_time(self, monitor):
        """Test time measurement"""
        with monitor.measure_time('operation'):
            time.sleep(0.01)  # Simulate work
        
        assert 'operation' in monitor.metrics
        assert len(monitor.metrics['operation']) == 1
        # Should be at least 10ms
        assert monitor.metrics['operation'][0].value >= 10
    
    def test_get_system_metrics(self, monitor):
        """Test system metrics collection"""
        metrics = monitor.get_system_metrics()
        
        assert 'cpu' in metrics
        assert 'memory' in metrics
        assert 'threads' in metrics
        assert 'uptime' in metrics
        
        assert metrics['cpu']['percent'] >= 0
        assert metrics['memory']['rss'] > 0
        assert metrics['threads'] > 0
    
    def test_get_application_metrics(self, monitor):
        """Test application metrics"""
        # Record some metrics
        monitor.increment_counter('requests', 10)
        monitor.record_metric('response_time', 100, 'ms')
        monitor.record_metric('response_time', 150, 'ms')
        monitor.record_metric('response_time', 200, 'ms')
        
        metrics = monitor.get_application_metrics()
        
        assert metrics['counters']['requests'] == 10
        assert 'response_time' in metrics['metrics']
        
        response_metrics = metrics['metrics']['response_time']
        assert response_metrics['count'] == 3
        assert response_metrics['min'] == 100
        assert response_metrics['max'] == 200
        assert response_metrics['avg'] == 150
    
    def test_metrics_history_limit(self, monitor):
        """Test metrics history limit"""
        monitor = PerformanceMonitor(max_history=5)
        
        # Record more than max_history
        for i in range(10):
            monitor.record_metric('test', i)
        
        # Should only keep last 5
        assert len(monitor.metrics['test']) == 5
        values = [m.value for m in monitor.metrics['test']]
        assert values == [5, 6, 7, 8, 9]
    
    def test_reset_counter(self, monitor):
        """Test resetting counter"""
        monitor.increment_counter('test_counter', 5)
        monitor.reset_counter('test_counter')
        
        assert monitor.get_counter('test_counter') == 0
    
    def test_clear_metrics(self, monitor):
        """Test clearing metrics"""
        monitor.record_metric('metric1', 1)
        monitor.record_metric('metric2', 2)
        
        # Clear specific metric
        monitor.clear_metrics('metric1')
        assert len(monitor.metrics['metric1']) == 0
        assert len(monitor.metrics['metric2']) == 1
        
        # Clear all metrics
        monitor.clear_metrics()
        assert len(monitor.metrics['metric2']) == 0


class TestHealthChecker:
    """Test health checking"""
    
    @pytest.fixture
    def checker(self):
        """Create health checker instance"""
        return HealthChecker()
    
    def test_register_check(self, checker):
        """Test registering health check"""
        def custom_check():
            from docscope.features.monitor import HealthStatus
            return HealthStatus(
                name='custom',
                healthy=True,
                message='Custom check OK'
            )
        
        checker.register_check('custom', custom_check)
        assert 'custom' in checker.checks
    
    def test_run_check(self, checker):
        """Test running health check"""
        def test_check():
            from docscope.features.monitor import HealthStatus
            return HealthStatus(
                name='test',
                healthy=True,
                message='Test passed'
            )
        
        checker.register_check('test', test_check)
        result = checker.run_check('test')
        
        assert result is not None
        assert result.healthy == True
        assert result.message == 'Test passed'
    
    def test_run_all_checks(self, checker):
        """Test running all health checks"""
        results = checker.run_all_checks()
        
        # Should have default checks
        assert 'system' in results
        assert 'disk_space' in results
        assert 'memory' in results
    
    def test_check_failure(self, checker):
        """Test health check failure"""
        def failing_check():
            raise Exception("Check failed")
        
        checker.register_check('failing', failing_check)
        result = checker.run_check('failing')
        
        assert result.healthy == False
        assert 'Check failed' in result.message
    
    def test_get_status(self, checker):
        """Test getting overall status"""
        # Run checks first
        checker.run_all_checks()
        
        status = checker.get_status()
        
        assert 'healthy' in status
        assert 'checks' in status
        assert 'timestamp' in status
    
    @patch('psutil.cpu_percent')
    def test_system_check_high_cpu(self, mock_cpu, checker):
        """Test system check with high CPU"""
        mock_cpu.return_value = 95  # High CPU usage
        
        result = checker._check_system()
        
        assert result.healthy == False
        assert 'High CPU usage' in result.message
    
    @patch('psutil.disk_usage')
    def test_disk_check_low_space(self, mock_disk, checker):
        """Test disk check with low space"""
        mock_usage = Mock()
        mock_usage.percent = 95  # High disk usage
        mock_usage.free = 1 * 1024**3  # 1GB free
        mock_disk.return_value = mock_usage
        
        result = checker._check_disk_space()
        
        assert result.healthy == False
        assert 'Low disk space' in result.message
    
    @patch('psutil.virtual_memory')
    def test_memory_check_high_usage(self, mock_memory, checker):
        """Test memory check with high usage"""
        mock_mem = Mock()
        mock_mem.percent = 95  # High memory usage
        mock_mem.available = 0.5 * 1024**3  # 0.5GB available
        mock_memory.return_value = mock_mem
        
        result = checker._check_memory()
        
        assert result.healthy == False
        assert 'High memory usage' in result.message
    
    def test_add_database_check(self, checker):
        """Test adding database health check"""
        mock_storage = Mock()
        mock_storage.get_document_count.return_value = 100
        
        checker.add_database_check(mock_storage)
        result = checker.run_check('database')
        
        assert result.healthy == True
        assert '100 documents' in result.message
    
    def test_add_search_check(self, checker):
        """Test adding search index health check"""
        mock_search = Mock()
        mock_search.get_stats.return_value = {'document_count': 50}
        
        checker.add_search_index_check(mock_search)
        result = checker.run_check('search_index')
        
        assert result.healthy == True
        assert '50 documents' in result.message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])