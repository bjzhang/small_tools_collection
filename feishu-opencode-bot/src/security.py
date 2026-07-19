"""用户/群白名单安全控制。

Phase 1 Task 4 将实现：
- 用户白名单校验
- 群白名单校验
"""
from __future__ import annotations


class SecurityGuard:
    """白名单守卫（Task 4 实现）。"""

    def __init__(self, allowed_users: list[str], allowed_chats: list[str]) -> None:
        self.allowed_users = set(allowed_users)
        self.allowed_chats = set(allowed_chats)

    def is_user_allowed(self, user_id: str) -> bool:
        """Task 4 实现。"""
        raise NotImplementedError("Task 4 将实现")

    def is_chat_allowed(self, chat_id: str) -> bool:
        """Task 4 实现。"""
        raise NotImplementedError("Task 4 将实现")