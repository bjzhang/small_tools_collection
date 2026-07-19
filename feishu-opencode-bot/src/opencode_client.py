"""opencode serve HTTP API 客户端。

Phase 1 Task 2 将实现：
- HTTP Basic Auth
- GET /api/session（session 列表）
- POST /api/session/{id}/prompt（发送消息，待 curl 验证路径）
- POST /api/session/{id}/agent（切换 agent，待 curl 验证路径）
- GET /api/event（SSE 事件流）
"""
from __future__ import annotations


class OpencodeClient:
    """opencode serve HTTP API 客户端（Task 2 实现）。"""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        # TODO: Task 2 初始化 httpx.AsyncClient + Basic Auth

    async def list_sessions(self) -> list[dict]:
        """GET /api/session（Task 2 实现）。"""
        raise NotImplementedError("Task 2 将实现")

    async def send_prompt(self, session_id: str, message: str) -> dict:
        """POST /api/session/{id}/prompt（Task 2 实现，路径待 curl 验证）。"""
        raise NotImplementedError("Task 2 将实现")

    async def switch_agent(self, session_id: str, agent: str) -> dict:
        """POST /api/session/{id}/agent（Task 2 实现，路径待 curl 验证）。"""
        raise NotImplementedError("Task 2 将实现")
