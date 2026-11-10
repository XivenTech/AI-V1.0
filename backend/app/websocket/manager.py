import json
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """全局 WebSocket 连接与多播广播管理器"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """向所有前端大屏广播统一格式的实时事件"""
        if not self.active_connections:
            return

        message = {
            "type": event_type,
            "data": data
        }
        payload = json.dumps(message, default=str)
        dead_connections = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


websocket_manager = WebSocketManager()
