"""opencode serve HTTP API 客户端。

依赖：httpx (async), 通过 respx 进行单元测试。

API 端点（来自 T217 计划调研）：
- GET    /api/session                    → {data: [Session]}
- GET    /api/session/{id}               → Session
- POST   /api/session/{id}/prompt        body: {prompt: {text}} → {data: {id, sessionID}}
- POST   /api/session/{id}/agent         body: {agent: "prometheus"} → 204
- GET    /api/agent                      → {data: [Agent]}
- GET    /api/session/{id}/message       → {data: [Message]}

认证：HTTP Basic Auth (username, password)
错误映射：
  401 → OpencodeAuthError
  404 → OpencodeNotFoundError
  5xx → OpencodeServerError
  其他 4xx → OpencodeClientError
  httpx.TimeoutException → OpencodeTimeoutError
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from src.exceptions import (
    OpencodeAuthError,
    OpencodeClientError,
    OpencodeError,
    OpencodeNotFoundError,
    OpencodeServerError,
    OpencodeTimeoutError,
)
from src.types import Agent, Message, PromptResponse, Session

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class OpencodeClient:
    """opencode serve HTTP API 异步客户端。

    Usage:
        client = OpencodeClient(
            base_url="http://127.0.0.1:4096",
            username="opencode",
            password="secret",
        )
        async with client:
            sessions = await client.list_sessions()
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._timeout = timeout or DEFAULT_TIMEOUT
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """惰性初始化 httpx.AsyncClient。"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.username, self.password),
                timeout=self._timeout,
            )
        return self._client

    async def __aenter__(self) -> "OpencodeClient":
        _ = self.client
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        """关闭底层 httpx 连接池。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """统一请求封装 + 错误映射。

        Args:
            method: HTTP 方法（GET/POST/DELETE/...）
            path: 相对 base_url 的路径（如 /api/session）
            json: 可选 JSON body

        Returns:
            httpx.Response（成功响应）

        Raises:
            OpencodeAuthError: 401
            OpencodeNotFoundError: 404
            OpencodeServerError: 5xx
            OpencodeClientError: 其他 4xx
            OpencodeTimeoutError: 请求超时
        """
        try:
            response = await self.client.request(method, path, json=json)
        except httpx.TimeoutException as e:
            raise OpencodeTimeoutError(f"请求超时: {method} {path}") from e
        except httpx.HTTPError as e:
            raise OpencodeError(f"HTTP 错误: {e}") from e

        if response.status_code == 401:
            raise OpencodeAuthError(
                f"认证失败（{self.username}）：检查 username/password"
            )
        if response.status_code == 404:
            raise OpencodeNotFoundError(f"资源不存在: {method} {path}")
        if 500 <= response.status_code < 600:
            raise OpencodeServerError(
                response.status_code,
                f"服务端错误: {method} {path} — {response.text[:200]}",
            )
        if 400 <= response.status_code < 500:
            raise OpencodeClientError(
                response.status_code,
                f"客户端错误: {method} {path} — {response.text[:200]}",
            )
        return response

    async def list_sessions(self) -> list[Session]:
        """GET /api/session — 列出所有 sessions。"""
        resp = await self._request("GET", "/api/session")
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def get_session(self, session_id: str) -> Session:
        """GET /api/session/{id} — 获取 session 详情。"""
        resp = await self._request("GET", f"/api/session/{session_id}")
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def send_message(self, session_id: str, text: str) -> PromptResponse:
        """POST /api/session/{id}/prompt — 发送消息到 session。"""
        resp = await self._request(
            "POST",
            f"/api/session/{session_id}/prompt",
            json={"prompt": {"text": text}},
        )
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def switch_agent(self, session_id: str, agent_name: str) -> None:
        """POST /api/session/{id}/agent — 切换 session 的 agent。

        Returns:
            None（成功响应是 204 No Content）

        Raises:
            OpencodeNotFoundError: agent 名不存在
        """
        await self._request(
            "POST",
            f"/api/session/{session_id}/agent",
            json={"agent": agent_name},
        )

    async def list_agents(self) -> list[Agent]:
        """GET /api/agent — 列出所有可用 agents。"""
        resp = await self._request("GET", "/api/agent")
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def get_messages(self, session_id: str) -> list[Message]:
        """GET /api/session/{id}/message — 获取 session 消息历史。"""
        resp = await self._request(
            "GET",
            f"/api/session/{session_id}/message",
        )
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data
