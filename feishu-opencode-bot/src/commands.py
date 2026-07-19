"""命令解析和处理。

Phase 1 Task 5-7 将实现 4 个核心命令：
- /list — 列出 sessions
- /status <session_id> — 查看 session 状态
- /send <session_id> <message> — 发送消息
- /switch_agent <session_id> <agent> — 切换 agent
"""
from __future__ import annotations


class CommandRouter:
    """命令路由（Task 5-7 实现）。"""

    async def handle(self, user_id: str, text: str) -> str:
        """处理用户命令，返回响应文本（Task 5 实现）。"""
        raise NotImplementedError("Task 5 将实现")