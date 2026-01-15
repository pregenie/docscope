"""CLI commands module"""

from .scan import scan_command
from .search import search_command
from .serve import serve_command
from .export import export_command
from .database import db_group
from .plugins import plugins_group
from .watch import watch_command
from .stats import stats_command
from .config import config_group

__all__ = [
    'scan_command',
    'search_command',
    'serve_command',
    'export_command',
    'db_group',
    'plugins_group',
    'watch_command',
    'stats_command',
    'config_group'
]