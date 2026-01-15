"""WebSocket API router for real-time updates"""

import json
from typing import Dict, Any, Set
from datetime import datetime
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from ..dependencies import get_storage, get_search_engine, verify_websocket_token
from ...storage import DocumentStore
from ...search import SearchEngine
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept and track new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection and clean up subscriptions"""
        self.active_connections.discard(websocket)
        
        # Remove from all subscriptions
        for topic in list(self.subscriptions.keys()):
            self.subscriptions[topic].discard(websocket)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe connection to a topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(websocket)
        
        await self.send_personal_message(
            {"type": "subscribed", "topic": topic},
            websocket
        )
    
    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe connection from a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(websocket)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        await self.send_personal_message(
            {"type": "unsubscribed", "topic": topic},
            websocket
        )
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific connection"""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send personal message: {e}")
    
    async def broadcast(self, message: Dict[str, Any], topic: str = None):
        """Broadcast message to all connections or topic subscribers"""
        targets = self.subscriptions.get(topic, self.active_connections) if topic else self.active_connections
        
        for connection in list(targets):
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast: {e}")


manager = ConnectionManager()


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """Main WebSocket endpoint for real-time updates"""
    # Verify token if provided
    if token:
        try:
            verify_websocket_token(token)
        except Exception as e:
            await websocket.close(code=1008, reason="Invalid token")
            return
    
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()},
                    websocket
                )
            
            elif message_type == "subscribe":
                topic = data.get("topic")
                if topic:
                    await manager.subscribe(websocket, topic)
            
            elif message_type == "unsubscribe":
                topic = data.get("topic")
                if topic:
                    await manager.unsubscribe(websocket, topic)
            
            elif message_type == "search":
                # Handle search request
                query = data.get("query")
                if query:
                    await handle_search_request(websocket, query, data.get("filters"))
            
            else:
                await manager.send_personal_message(
                    {"type": "error", "message": f"Unknown message type: {message_type}"},
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/notifications")
async def notifications_endpoint(websocket: WebSocket):
    """Dedicated endpoint for system notifications"""
    await manager.connect(websocket)
    
    # Auto-subscribe to system notifications
    await manager.subscribe(websocket, "system")
    
    try:
        # Send initial notification
        await manager.send_personal_message(
            {
                "type": "notification",
                "level": "info",
                "message": "Connected to notification stream",
                "timestamp": datetime.now().isoformat()
            },
            websocket
        )
        
        # Keep connection alive
        while True:
            # Send heartbeat every 30 seconds
            await asyncio.sleep(30)
            await manager.send_personal_message(
                {"type": "heartbeat", "timestamp": datetime.now().isoformat()},
                websocket
            )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/live-search")
async def live_search_endpoint(
    websocket: WebSocket,
    search_engine: SearchEngine = Depends(get_search_engine)
):
    """Live search with instant results"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive search query
            data = await websocket.receive_json()
            query = data.get("query", "")
            
            if len(query) < 2:
                await manager.send_personal_message(
                    {"type": "results", "results": [], "total": 0},
                    websocket
                )
                continue
            
            # Perform search
            try:
                results = search_engine.search(
                    query=query,
                    limit=data.get("limit", 10),
                    filters=data.get("filters")
                )
                
                # Send results
                await manager.send_personal_message(
                    {
                        "type": "results",
                        "query": query,
                        "results": [
                            {
                                "id": r.document_id,
                                "title": r.title,
                                "snippet": r.snippet,
                                "score": r.score
                            }
                            for r in results.results
                        ],
                        "total": results.total,
                        "duration": results.duration
                    },
                    websocket
                )
            except Exception as e:
                await manager.send_personal_message(
                    {"type": "error", "message": f"Search failed: {e}"},
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Live search error: {e}")
        manager.disconnect(websocket)


async def handle_search_request(
    websocket: WebSocket,
    query: str,
    filters: Dict[str, Any] = None
):
    """Handle search request from WebSocket"""
    # This would integrate with the search engine
    # For now, send a placeholder response
    await manager.send_personal_message(
        {
            "type": "search_results",
            "query": query,
            "results": [],
            "message": "Search functionality pending implementation"
        },
        websocket
    )


async def broadcast_document_update(document_id: str, action: str):
    """Broadcast document update to all subscribed clients"""
    await manager.broadcast(
        {
            "type": "document_update",
            "document_id": document_id,
            "action": action,
            "timestamp": datetime.now().isoformat()
        },
        topic="documents"
    )


async def broadcast_scan_progress(progress: float, message: str):
    """Broadcast scan progress to all subscribed clients"""
    await manager.broadcast(
        {
            "type": "scan_progress",
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        },
        topic="scanner"
    )