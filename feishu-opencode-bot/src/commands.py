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
        self.register("status", self._handle_status)
        self.register("send", self._handle_send)

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
            "**Phase 1 计划实现（Task 7）**：",
            "- `/switch_agent <session_id> <agent>` — 切换 agent（如 prometheus/atlas）",
            "- `/agents` — 列出所有可用 agent",
            "",
            "**示例**：",
            "```",
            "/list",
            "/status ses_abc123",
            "/status ses_abc123 10",
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

    # ===== Task 6: /status + /send =====

    async def _handle_status(
        self, router: "CommandRouter", command: "Command"
    ) -> str:
        """处理 /status <session_id>：查看 session 详情 + 最近消息。

        用法：
            /status ses_001         — 默认显示 5 条最近消息
            /status ses_001 10      — 显示 10 条最近消息
        """
        if not command.args:
            return (
                "❌ 用法：/status <session_id> [消息条数]\n\n"
                "示例：\n"
                "- `/status ses_001` — 显示最近 5 条消息\n"
                "- `/status ses_001 10` — 显示最近 10 条消息"
            )

        session_id = command.args[0]
        message_count = 5
        if len(command.args) >= 2:
            try:
                message_count = int(command.args[1])
                if message_count < 0 or message_count > 50:
                    return "❌ 消息条数必须在 0-50 之间"
            except ValueError:
                return f"❌ 无效的消息条数：{command.args[1]!r}（应为整数）"

        try:
            session = await self.opencode.get_session(session_id)
        except Exception as e:
            logger.exception("/status get_session 失败")
            return self._format_session_error(session_id, e)

        messages_text = ""
        if message_count > 0:
            try:
                messages = await self.opencode.get_messages(session_id)
                recent = messages[-message_count:] if messages else []
                messages_text = self._format_messages(recent)
            except Exception as e:
                logger.exception("/status get_messages 失败")
                messages_text = f"\n\n⚠️ 获取消息历史失败：{e}"

        return self._format_session_detail(session) + messages_text

    async def _handle_send(
        self, router: "CommandRouter", command: "Command"
    ) -> str:
        """处理 /send <session_id> <message>：向 session 发送消息。

        安全：消息内容会被 SecurityGuard.sanitize_input() 清理（如果 router 上有 guard）。
        Phase 1 不支持引号参数。
        """
        if len(command.args) < 2:
            return (
                "❌ 用法：/send <session_id> <message>\n\n"
                "示例：`/send ses_001 重启服务`"
            )

        session_id = command.args[0]
        # join args[1:] 重建消息以保留多词之间的空格（raw_text 不会处理多余空白）
        message = " ".join(command.args[1:])

        if not message.strip():
            return "❌ 消息内容不能为空"

        guard = getattr(self, "_security_guard", None)
        if guard is not None:
            message = guard.sanitize_input(message)
            if not message:
                return "❌ 消息清理后为空（可能包含危险字符）"

        try:
            result = await self.opencode.send_message(session_id, message)
        except Exception as e:
            logger.exception("/send send_message 失败")
            return self._format_session_error(session_id, e)

        msg_id = result.get("id", "?") if isinstance(result, dict) else "?"
        return (
            f"✅ 消息已发送到 session `{session_id}`\n\n"
            f"消息 ID: `{msg_id}`\n"
            f"内容预览: {message[:50]}{'...' if len(message) > 50 else ''}"
        )

    def _format_session_detail(self, session: dict) -> str:
        """格式化 session 详情。"""
        sid = session.get("id", "?")
        agent = session.get("agent", "?")
        title = session.get("title", "")
        created = session.get("createdAt", "?")
        updated = session.get("updatedAt", "?")
        model = session.get("model", "")

        lines = [
            f"📊 **Session**: `{sid}`",
            f"**Agent**: `{agent}`",
        ]
        if title:
            lines.append(f"**Title**: {title}")
        if model:
            lines.append(f"**Model**: `{model}`")
        lines.append(f"**Created**: {created}")
        lines.append(f"**Updated**: {updated}")
        return "\n".join(lines)

    def _format_messages(self, messages: list) -> str:
        """格式化消息列表。"""
        if not messages:
            return "\n\n💤 暂无消息历史"
        lines = [f"\n\n💬 **最近消息**（{len(messages)} 条）：", ""]
        for msg in messages:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            # 魔数 200 字符截断防止飞书消息过长
            if len(content) > 200:
                content = content[:200] + "..."
            icon = "👤" if role == "user" else "🤖"
            lines.append(f"{icon} `[{role}]` {content}")
        return "\n".join(lines)

    def _format_session_error(self, session_id: str, error: Exception) -> str:
        """格式化 session 操作错误（区分 404 与一般错误）。"""
        error_msg = str(error)
        error_lower = error_msg.lower()
        if "404" in error_lower or "not found" in error_lower or "不存在" in error_msg:
            return (
                f"❌ Session `{session_id}` 不存在\n\n"
                f"输入 `/list` 查看所有可用 session"
            )
        return f"❌ 操作 session `{session_id}` 失败：{error_msg}"
