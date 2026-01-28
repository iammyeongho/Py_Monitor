"""
WebSocket 엔드포인트

실시간 모니터링 상태 업데이트를 제공합니다.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.project import Project
from app.models.monitoring import MonitoringLog

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # project_id -> Set[WebSocket] (프로젝트별 구독)
        self.project_subscriptions: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """연결 수락"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: user_id={user_id}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """연결 해제"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # 프로젝트 구독에서도 제거
        for project_id in list(self.project_subscriptions.keys()):
            self.project_subscriptions[project_id].discard(websocket)
            if not self.project_subscriptions[project_id]:
                del self.project_subscriptions[project_id]

        logger.info(f"WebSocket disconnected: user_id={user_id}")

    def subscribe_project(self, websocket: WebSocket, project_id: int):
        """프로젝트 구독"""
        if project_id not in self.project_subscriptions:
            self.project_subscriptions[project_id] = set()
        self.project_subscriptions[project_id].add(websocket)

    def unsubscribe_project(self, websocket: WebSocket, project_id: int):
        """프로젝트 구독 해제"""
        if project_id in self.project_subscriptions:
            self.project_subscriptions[project_id].discard(websocket)

    async def send_personal(self, user_id: int, message: dict):
        """특정 사용자에게 메시지 전송"""
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")

    async def broadcast_project_update(self, project_id: int, message: dict):
        """프로젝트 구독자들에게 업데이트 전송"""
        if project_id in self.project_subscriptions:
            for websocket in self.project_subscriptions[project_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast: {e}")

    async def broadcast_to_user(self, user_id: int, message: dict):
        """사용자의 모든 연결에 브로드캐스트"""
        await self.send_personal(user_id, message)


# 전역 연결 관리자
manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int
):
    """
    WebSocket 연결 엔드포인트

    클라이언트 메시지 형식:
    - {"type": "subscribe", "project_id": 123}
    - {"type": "unsubscribe", "project_id": 123}
    - {"type": "ping"}

    서버 메시지 형식:
    - {"type": "status", "project_id": 123, "data": {...}}
    - {"type": "alert", "project_id": 123, "data": {...}}
    - {"type": "pong"}
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe":
                project_id = message.get("project_id")
                if project_id:
                    manager.subscribe_project(websocket, project_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "project_id": project_id
                    })

            elif message.get("type") == "unsubscribe":
                project_id = message.get("project_id")
                if project_id:
                    manager.unsubscribe_project(websocket, project_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "project_id": project_id
                    })

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


async def notify_monitoring_update(
    user_id: int,
    project_id: int,
    log: MonitoringLog
):
    """모니터링 업데이트 알림 전송"""
    message = {
        "type": "status",
        "project_id": project_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "is_available": log.is_available,
            "response_time": log.response_time,
            "status_code": log.status_code,
            "status_text": log.status_text,
            "performance_grade": log.get_performance_grade(),
        }
    }

    # 사용자에게 전송
    await manager.send_personal(user_id, message)
    # 프로젝트 구독자들에게 전송
    await manager.broadcast_project_update(project_id, message)


async def notify_alert(
    user_id: int,
    project_id: int,
    alert_type: str,
    message: str
):
    """알림 전송"""
    alert_message = {
        "type": "alert",
        "project_id": project_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "alert_type": alert_type,
            "message": message,
        }
    }

    await manager.send_personal(user_id, alert_message)
    await manager.broadcast_project_update(project_id, alert_message)


def get_connection_manager() -> ConnectionManager:
    """ConnectionManager 인스턴스 반환"""
    return manager
