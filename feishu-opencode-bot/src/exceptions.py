"""opencode 客户端异常层级。"""
from __future__ import annotations


class OpencodeError(Exception):
    """opencode 客户端基础异常。"""


class OpencodeAuthError(OpencodeError):
    """401 Unauthorized — 用户名/密码错误。"""


class OpencodeNotFoundError(OpencodeError):
    """404 Not Found — session/agent 不存在。"""


class OpencodeTimeoutError(OpencodeError):
    """请求超时（httpx.TimeoutException）。"""


class OpencodeServerError(OpencodeError):
    """5xx 服务端错误。"""

    def __init__(self, status_code: int, message: str = "") -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class OpencodeClientError(OpencodeError):
    """其他 4xx 客户端错误（非 401/404）。"""

    def __init__(self, status_code: int, message: str = "") -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
