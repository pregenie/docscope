"""Performance monitoring and health checks for DocScope"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Performance metric"""
    name: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """Health check status"""
    name: str
    healthy: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        """Initialize performance monitor"""
        self.metrics: Dict[str, deque] = {}
        self.max_history = max_history
        self.start_time = time.time()
        self.counters: Dict[str, int] = {}
        self.lock = threading.Lock()
        
        # Start system metrics collection
        self._init_system_metrics()
        
    def _init_system_metrics(self):
        """Initialize system metrics tracking"""
        self.process = psutil.Process()
        
    def record_metric(self, name: str, value: float, unit: str = "", tags: Dict[str, str] = None):
        """Record a performance metric"""
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.max_history)
            self.metrics[name].append(metric)
            
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric"""
        with self.lock:
            if name not in self.counters:
                self.counters[name] = 0
            self.counters[name] += value
            
    def get_counter(self, name: str) -> int:
        """Get counter value"""
        return self.counters.get(name, 0)
        
    def measure_time(self, name: str):
        """Context manager to measure execution time"""
        class TimeMeasure:
            def __init__(self, monitor, metric_name):
                self.monitor = monitor
                self.metric_name = metric_name
                self.start_time = None
                
            def __enter__(self):
                self.start_time = time.time()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start_time
                self.monitor.record_metric(self.metric_name, elapsed * 1000, "ms")
                
        return TimeMeasure(self, name)
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = self.process.cpu_percent()
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # Disk I/O (if available)
            try:
                io_counters = self.process.io_counters()
                disk_io = {
                    'read_bytes': io_counters.read_bytes,
                    'write_bytes': io_counters.write_bytes,
                    'read_count': io_counters.read_count,
                    'write_count': io_counters.write_count
                }
            except (AttributeError, psutil.AccessDenied):
                disk_io = {}
                
            # Network connections
            try:
                connections = len(self.process.connections())
            except (AttributeError, psutil.AccessDenied):
                connections = 0
                
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'percent': memory_percent,
                    'available': psutil.virtual_memory().available
                },
                'disk_io': disk_io,
                'connections': connections,
                'threads': self.process.num_threads(),
                'uptime': time.time() - self.start_time
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
            
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        with self.lock:
            app_metrics = {
                'counters': dict(self.counters),
                'metrics': {}
            }
            
            # Calculate statistics for each metric
            for name, values in self.metrics.items():
                if values:
                    recent_values = [m.value for m in list(values)[-100:]]
                    app_metrics['metrics'][name] = {
                        'count': len(values),
                        'latest': values[-1].value,
                        'min': min(recent_values),
                        'max': max(recent_values),
                        'avg': sum(recent_values) / len(recent_values),
                        'unit': values[-1].unit
                    }
                    
            return app_metrics
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get complete metrics summary"""
        return {
            'system': self.get_system_metrics(),
            'application': self.get_application_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        
    def reset_counter(self, name: str):
        """Reset a counter to zero"""
        with self.lock:
            if name in self.counters:
                self.counters[name] = 0
                
    def clear_metrics(self, name: str = None):
        """Clear metric history"""
        with self.lock:
            if name:
                if name in self.metrics:
                    self.metrics[name].clear()
            else:
                for metric_list in self.metrics.values():
                    metric_list.clear()


class HealthChecker:
    """Perform health checks on DocScope components"""
    
    def __init__(self):
        """Initialize health checker"""
        self.checks: Dict[str, Callable] = {}
        self.check_results: Dict[str, HealthStatus] = {}
        self.lock = threading.Lock()
        
        # Register default checks
        self._register_default_checks()
        
    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check("system", self._check_system)
        self.register_check("disk_space", self._check_disk_space)
        self.register_check("memory", self._check_memory)
        
    def register_check(self, name: str, check_func: Callable[[], HealthStatus]):
        """Register a health check"""
        self.checks[name] = check_func
        
    def unregister_check(self, name: str):
        """Unregister a health check"""
        if name in self.checks:
            del self.checks[name]
            
    def run_check(self, name: str) -> Optional[HealthStatus]:
        """Run a specific health check"""
        if name not in self.checks:
            return None
            
        try:
            status = self.checks[name]()
            with self.lock:
                self.check_results[name] = status
            return status
            
        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}")
            status = HealthStatus(
                name=name,
                healthy=False,
                message=f"Check failed: {str(e)}"
            )
            with self.lock:
                self.check_results[name] = status
            return status
            
    def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run all registered health checks"""
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results
        
    def get_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        with self.lock:
            all_healthy = all(
                status.healthy 
                for status in self.check_results.values()
            )
            
            return {
                'healthy': all_healthy,
                'checks': {
                    name: {
                        'healthy': status.healthy,
                        'message': status.message,
                        'details': status.details,
                        'timestamp': status.timestamp
                    }
                    for name, status in self.check_results.items()
                },
                'timestamp': datetime.now().isoformat()
            }
            
    def _check_system(self) -> HealthStatus:
        """Check basic system health"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Check if CPU is overloaded
            if cpu_percent > 90:
                return HealthStatus(
                    name="system",
                    healthy=False,
                    message=f"High CPU usage: {cpu_percent}%",
                    details={'cpu_percent': cpu_percent}
                )
                
            return HealthStatus(
                name="system",
                healthy=True,
                message="System resources OK",
                details={'cpu_percent': cpu_percent}
            )
            
        except Exception as e:
            return HealthStatus(
                name="system",
                healthy=False,
                message=f"System check failed: {e}"
            )
            
    def _check_disk_space(self) -> HealthStatus:
        """Check available disk space"""
        try:
            usage = psutil.disk_usage('/')
            percent_used = usage.percent
            free_gb = usage.free / (1024**3)
            
            if percent_used > 90:
                return HealthStatus(
                    name="disk_space",
                    healthy=False,
                    message=f"Low disk space: {free_gb:.1f}GB free ({percent_used}% used)",
                    details={
                        'percent_used': percent_used,
                        'free_gb': free_gb
                    }
                )
                
            return HealthStatus(
                name="disk_space",
                healthy=True,
                message=f"Disk space OK: {free_gb:.1f}GB free",
                details={
                    'percent_used': percent_used,
                    'free_gb': free_gb
                }
            )
            
        except Exception as e:
            return HealthStatus(
                name="disk_space",
                healthy=False,
                message=f"Disk check failed: {e}"
            )
            
    def _check_memory(self) -> HealthStatus:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            available_gb = memory.available / (1024**3)
            
            if percent_used > 90:
                return HealthStatus(
                    name="memory",
                    healthy=False,
                    message=f"High memory usage: {percent_used}% ({available_gb:.1f}GB available)",
                    details={
                        'percent_used': percent_used,
                        'available_gb': available_gb
                    }
                )
                
            return HealthStatus(
                name="memory",
                healthy=True,
                message=f"Memory OK: {available_gb:.1f}GB available",
                details={
                    'percent_used': percent_used,
                    'available_gb': available_gb
                }
            )
            
        except Exception as e:
            return HealthStatus(
                name="memory",
                healthy=False,
                message=f"Memory check failed: {e}"
            )
            
    def add_database_check(self, storage_manager):
        """Add database health check"""
        def check_database():
            try:
                # Try to query database
                count = storage_manager.get_document_count()
                return HealthStatus(
                    name="database",
                    healthy=True,
                    message=f"Database OK: {count} documents",
                    details={'document_count': count}
                )
            except Exception as e:
                return HealthStatus(
                    name="database",
                    healthy=False,
                    message=f"Database error: {e}"
                )
                
        self.register_check("database", check_database)
        
    def add_search_index_check(self, search_index):
        """Add search index health check"""
        def check_search():
            try:
                # Try to get index stats
                stats = search_index.get_stats()
                return HealthStatus(
                    name="search_index",
                    healthy=True,
                    message=f"Search index OK: {stats.get('document_count', 0)} documents",
                    details=stats
                )
            except Exception as e:
                return HealthStatus(
                    name="search_index",
                    healthy=False,
                    message=f"Search index error: {e}"
                )
                
        self.register_check("search_index", check_search)