"""Custom exceptions for DocScope"""


class DocscopeException(Exception):
    """Base exception for DocScope"""
    pass


class ConfigurationError(DocscopeException):
    """Configuration related errors"""
    pass


class ScannerError(DocscopeException):
    """Scanner related errors"""
    pass


class StorageError(DocscopeException):
    """Storage related errors"""
    pass


class SearchError(DocscopeException):
    """Search related errors"""
    pass


class PluginError(DocscopeException):
    """Plugin related errors"""
    pass


class ValidationError(DocscopeException):
    """Validation errors"""
    pass


class NotFoundError(DocscopeException):
    """Resource not found errors"""
    pass


class PermissionError(DocscopeException):
    """Permission related errors"""
    pass