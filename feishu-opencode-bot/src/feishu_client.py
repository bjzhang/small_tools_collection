"""飞书 lark-oapi SDK 封装。

Phase 1 Task 3 将实现：
- WebSocket 长连接接入
- 消息接收回调
- 消息发送 API
- 交互卡片发送 API
"""
from __future__ import annotations


class FeishuClient:
    """飞书客户端封装（Task 3 实现）。"""

    def __init__(self, app_id: str, app_secret: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        # TODO: Task 3 初始化 lark-oapi client

    async def start_websocket(self) -> None:
        """启动 WebSocket 长连接（Task 3 实现）。"""
        raise NotImplementedError("Task 3 将实现")

    async def send_message(self, user_id: str, text: str) -> None:
        """发送单聊消息（Task 3 实现）。"""
        raise NotImplementedError("Task 3 将实现")