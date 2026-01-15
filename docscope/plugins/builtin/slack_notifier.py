"""Slack Notifier Plugin for DocScope"""

import json
from typing import Dict, Any, List
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..base import NotificationPlugin, PluginMetadata, PluginCapability, PluginHook

logger = logging.getLogger(__name__)


class SlackNotifierPlugin(NotificationPlugin):
    """Plugin for sending notifications to Slack"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url') if config else None
        self.channel = config.get('channel', '#general') if config else '#general'
        self.username = config.get('username', 'DocScope') if config else 'DocScope'
        self.icon_emoji = config.get('icon_emoji', ':books:') if config else ':books:'
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="slack_notifier",
            version="1.0.0",
            author="DocScope Team",
            description="Send notifications to Slack channels",
            website="https://github.com/docscope/slack-notifier",
            license="MIT",
            capabilities=[PluginCapability.NOTIFICATION],
            hooks=[
                PluginHook.AFTER_SCAN,
                PluginHook.AFTER_INDEX,
                PluginHook.AFTER_DELETE
            ],
            tags=["slack", "notification", "webhook"],
            config_schema={
                'webhook_url': {
                    'type': str,
                    'required': True,
                    'description': 'Slack webhook URL'
                },
                'channel': {
                    'type': str,
                    'default': '#general',
                    'description': 'Slack channel to post to'
                },
                'username': {
                    'type': str,
                    'default': 'DocScope',
                    'description': 'Bot username'
                },
                'icon_emoji': {
                    'type': str,
                    'default': ':books:',
                    'description': 'Bot icon emoji'
                }
            }
        )
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        # Register hooks
        self.register_hook(PluginHook.AFTER_SCAN, self.notify_scan_complete)
        self.register_hook(PluginHook.AFTER_INDEX, self.notify_index_complete)
        self.register_hook(PluginHook.AFTER_DELETE, self.notify_document_deleted)
        
        logger.info("Slack Notifier plugin initialized")
        return True
    
    def shutdown(self) -> None:
        """Cleanup when plugin is disabled"""
        logger.info("Slack Notifier plugin shutdown")
    
    def send_notification(self, message: str, level: str = "info", **options) -> bool:
        """Send a notification to Slack"""
        if not self.webhook_url:
            logger.warning("Cannot send notification: webhook URL not configured")
            return False
        
        try:
            # Determine color based on level
            color_map = {
                'info': '#36a64f',     # Green
                'warning': '#ff9900',   # Orange
                'error': '#ff0000',     # Red
                'success': '#36a64f'    # Green
            }
            color = color_map.get(level, '#808080')
            
            # Build payload
            payload = {
                'channel': options.get('channel', self.channel),
                'username': options.get('username', self.username),
                'icon_emoji': options.get('icon_emoji', self.icon_emoji),
                'attachments': [
                    {
                        'color': color,
                        'text': message,
                        'fallback': message,
                        'footer': 'DocScope',
                        'ts': int(time.time()) if 'time' in locals() else None
                    }
                ]
            }
            
            # Add fields if provided
            if 'fields' in options:
                payload['attachments'][0]['fields'] = options['fields']
            
            # Send to Slack
            req = Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            response = urlopen(req)
            
            if response.status == 200:
                logger.debug(f"Successfully sent Slack notification: {message[:50]}...")
                return True
            else:
                logger.warning(f"Slack notification failed with status: {response.status}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def notify_scan_complete(self, scan_result: Dict[str, Any]) -> None:
        """Hook handler for scan completion"""
        if not self.enabled:
            return
        
        message = f"Document scan completed:\n"
        message += f"• Total: {scan_result.get('total', 0)} documents\n"
        message += f"• Successful: {scan_result.get('successful', 0)}\n"
        message += f"• Failed: {scan_result.get('failed', 0)}"
        
        fields = [
            {
                'title': 'Total Documents',
                'value': str(scan_result.get('total', 0)),
                'short': True
            },
            {
                'title': 'Duration',
                'value': f"{scan_result.get('duration', 0):.1f}s",
                'short': True
            }
        ]
        
        level = 'success' if scan_result.get('failed', 0) == 0 else 'warning'
        self.send_notification(message, level=level, fields=fields)
    
    def notify_index_complete(self, index_result: Dict[str, Any]) -> None:
        """Hook handler for index completion"""
        if not self.enabled:
            return
        
        count = index_result.get('indexed', 0)
        message = f"Successfully indexed {count} document(s)"
        self.send_notification(message, level='info')
    
    def notify_document_deleted(self, document: Dict[str, Any]) -> None:
        """Hook handler for document deletion"""
        if not self.enabled:
            return
        
        title = document.get('title', 'Unknown')
        doc_id = document.get('id', 'unknown')
        message = f"Document deleted: {title} (ID: {doc_id})"
        self.send_notification(message, level='warning')
    
    def get_notification_types(self) -> List[str]:
        """Get supported notification types"""
        return ["info", "warning", "error", "success"]