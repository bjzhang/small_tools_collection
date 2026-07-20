"""命令解析与路由。

支持命令：
- /list                              — 列出所有 sessions（Task 5 实现）
- /help                              — 显示帮助（Task 5 实现）
- /status <session_id>               — 查看特定 session（Task 6 实现）
- /send <session_id> <message>       — 向 session 发送消息（Task 6 实现）
- /switch_agent <session_id> <agent> — 切换 agent（Task 7 实现）

Phase 1 简单解析：空格分隔，不支持引号。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from src.opencode_client import OpencodeClient

logger = logging.getLogger(__name__)


@dataclass
class Command:
    """解析后的命令对象。

    Attributes:
        name: 小写命令名（无 / 前缀），如 "list"
        raw_name: 原始命令名（保留用户输入大小写）
        args: 参数列表（已 split）
        raw_text: 原始输入文本
    """
    name: str
    raw_name: str
    args: list[str]
    raw_text: str

    @property
    def is_valid(self) -> bool:
        """命令名是否合法（非空，以字母开头）。"""
        return bool(self.name) and self.name[0].isalpha()


# Handler 类型：接收 router 和 command，返回响应文本
CommandHandler = Callable[["CommandRouter", "Command"], Awaitable[str]]


class CommandParser:
    """命令解析器（空格分隔，Phase 1 简单版本）。

    支持格式：
    - /list
    - /status ses_xxx
    - /send ses_xxx hello world
    - /switch_agent ses_xxx prometheus

    Phase 1 不支持：引号参数、转义字符、管道。
    """

    @staticmethod
    def parse(text: str) -> Optional[Command]:
        """解析文本为 Command，无法解析时返回 None。

        Args:
            text: 原始用户输入

        Returns:
            Command 对象，或 None（不是命令）
        """
        if not text:
            return None
        stripped = text.strip()
        if not stripped:
            return None
        if not stripped.startswith("/"):
            return None

        # 简单空格分隔（不解析引号，Phase 1）
        parts = stripped.split()
        raw_name = parts[0][1:]  # 去掉 /
        if not raw_name:
            return None

        return Command(
            name=raw_name.lower(),
            raw_name=raw_name,
            args=parts[1:],
            raw_text=stripped,
        )


class CommandRouter:
    """命令路由器。

    注册命令 handler，根据命令名分发。
    后续 Task 6/7 会通过 register() 注册 /status, /send, /switch_agent。

    Usage:
        router = CommandRouter(opencode_client)
        response = await router.handle_text("/list")
    """

    def __init__(self, opencode_client: OpencodeClient) -> None:
        self.opencode = opencode_client
        self._handlers: dict[str, CommandHandler] = {}
        # 注册内置命令
        self.register("list", self._handle_list)
        self.register("help", self._handle_help)

    def register(self, name: str, handler: CommandHandler) -> None:
        """注册命令 handler（后续 task 用此方法注册新命令）。

        Args:
            name: 命令名（大小写不敏感，存储为小写）
            handler: async 函数 (router, command) -> str
        """
        self._handlers[name.lower()] = handler
        logger.info("注册命令：/%s", name)

    def list_commands(self) -> list[str]:
        """返回所有已注册命令名（小写，排序）。"""
        return sorted(self._handlers.keys())

    async def dispatch(self, command: Command) -> str:
        """分发命令到对应 handler。

        Args:
            command: 已解析的 Command 对象

        Returns:
            响应文本
        """
        if not command.is_valid:
            return f"❌ 无效命令：{command.raw_text!r}"

        if command.name not in self._handlers:
            return self._unknown_command_response(command)

        handler = self._handlers[command.name]
        try:
            return await handler(self, command)
        except Exception as e:
            logger.exception("命令 /%s 执行失败：%s", command.name, e)
            return f"❌ 命令执行失败：{e}"

    async def handle_text(self, text: str) -> Optional[str]:
        """便捷方法：解析 + 分发。

        Args:
            text: 原始用户输入

        Returns:
            响应文本，或 None（输入不是命令）
        """
        command = CommandParser.parse(text)
        if command is None:
            return None
        return await self.dispatch(command)

    # ===== 内置 handlers =====

    async def _handle_list(
        self, router: "CommandRouter", command: "Command"
    ) -> str:
        """处理 /list：返回所有 opencode sessions。

        格式：
            📋 opencode sessions（N 个）：

            1. `ses_xxx` [agent] — title
            2. ...
        """
        try:
            sessions = await self.opencode.list_sessions()
        except Exception as e:
            logger.exception("/list 调用 opencode 失败")
            return f"❌ 获取 session 列表失败：{e}"

        if not sessions:
            return "📭 当前没有 opencode session"

        lines = [f"📋 opencode sessions（{len(sessions)} 个）：", ""]
        for i, s in enumerate(sessions, 1):
            sid = s.get("id", "?")
            agent = s.get("agent", "?")
            title = s.get("title", "")
            title_str = f" — {title}" if title else ""
            lines.append(f"{i}. `{sid}` [{agent}]{title_str}")
        return "\n".join(lines)

    async def _handle_help(
        self, router: "CommandRouter", command: "Command"
    ) -> str:
        """处理 /help：返回所有命令的帮助文本。"""
        # 动态生成已实现命令列表
        implemented = []
        for name in self.list_commands():
            implemented.append(f"- `/{name}`")

        lines = [
            "📖 飞书 opencode bot 命令：",
            "",
            "**已实现**：",
        ]
        lines.extend(implemented)

        lines.extend([
            "",
            "**Phase 1 计划实现（Task 6-7）**：",
            "- `/status <session_id>` — 查看 session 详情",
            "- `/send <session_id> <message>` — 向 session 发送消息",
            "- `/switch_agent <session_id> <agent>` — 切换 agent（如 prometheus/atlas）",
            "",
            "**示例**：",
            "```",
            "/list",
            "/status ses_abc123",
            "/send ses_abc123 重启服务",
            "/switch_agent ses_abc123 prometheus",
            "```",
        ])
        return "\n".join(lines)

    def _unknown_command_response(self, command: Command) -> str:
        """未知命令的友好响应。"""
        known = ", ".join(f"/{n}" for n in self.list_commands())
        return (
            f"❓ 未知命令：/{command.raw_name}\n\n"
            f"已知命令：{known}\n"
            f"输入 `/help` 查看完整帮助"
        )
