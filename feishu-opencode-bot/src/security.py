"""白名单守卫 + 输入安全。

提供：
- 用户白名单（飞书 open_id）
- 群白名单（飞书 chat_id）
- 命令注入防护（清理 shell 特殊字符）
- 审计日志（拒绝/通过/清理事件）

设计原则：
- 白名单从配置加载（config.yaml 的 security 段），不硬编码
- 群白名单为空时保守拒绝所有群（避免误开放）
- 输入清理日志告警（便于审计）
"""
from __future__ import annotations

import logging
import re
from typing import Iterable

logger = logging.getLogger(__name__)


# Shell 注入危险字符：; $ ` | & > < \n \r
# 注意：保留空格、引号、字母数字、常见标点（命令参数可能需要）
SHELL_INJECTION_PATTERN = re.compile(r"[;$`|&><\n\r]")

# 危险命令关键字（黑名单，作为额外防护）
DANGEROUS_COMMAND_PREFIXES = (
    "rm -rf",
    "sudo ",
    "sh -c",
    "bash -c",
    "curl ",
    "wget ",
    "eval ",
    "exec ",
)


class SecurityError(Exception):
    """安全违规（命令被拒绝）。"""


class SecurityGuard:
    """白名单 + 输入清理守卫。

    Usage:
        guard = SecurityGuard(
            allowed_users=["ou_xxx", "ou_yyy"],
            allowed_chats=["oc_zzz"],
        )
        if guard.is_user_allowed(user_open_id):
            safe_text = guard.sanitize_input(user_input)
            # ... 处理 safe_text
    """

    def __init__(
        self,
        allowed_users: Iterable[str],
        allowed_chats: Iterable[str] | None = None,
    ) -> None:
        # 复制为 set，防止外部修改
        self.allowed_users: set[str] = set(allowed_users)
        self.allowed_chats: set[str] = set(allowed_chats or [])

    def is_user_allowed(self, user_id: str) -> bool:
        """检查 user_id（飞书 open_id）是否在白名单。

        Args:
            user_id: 飞书 open_id（ou_xxx 格式）

        Returns:
            True = 允许，False = 拒绝
        """
        if not user_id:
            logger.warning("空 user_id 被拒绝")
            return False
        allowed = user_id in self.allowed_users
        if allowed:
            logger.info("用户 %s 通过白名单", user_id)
        else:
            logger.warning("用户 %s 不在白名单（拒绝）", user_id)
        return allowed

    def is_chat_allowed(self, chat_id: str) -> bool:
        """检查 chat_id（飞书 chat_id）是否在群白名单。

        保守策略：白名单为空时拒绝所有群（避免误开放）。

        Args:
            chat_id: 飞书 chat_id（oc_xxx 格式）

        Returns:
            True = 允许，False = 拒绝
        """
        if not chat_id:
            logger.warning("空 chat_id 被拒绝")
            return False
        if not self.allowed_chats:
            logger.warning(
                "未配置群白名单，拒绝群 %s（保守策略）", chat_id
            )
            return False
        allowed = chat_id in self.allowed_chats
        if allowed:
            logger.info("群 %s 通过白名单", chat_id)
        else:
            logger.warning("群 %s 不在白名单", chat_id)
        return allowed

    def sanitize_input(self, text: str) -> str:
        """清理用户输入，移除 shell 注入危险字符。

        移除的字符：; $ ` | & > < \\n \\r

        Args:
            text: 原始输入

        Returns:
            清理后的字符串（可能短于输入）
        """
        if text is None:
            return ""
        cleaned = SHELL_INJECTION_PATTERN.sub("", str(text))
        if cleaned != text:
            logger.warning(
                "输入被清理：%r → %r（移除了 %d 字符）",
                text,
                cleaned,
                len(text) - len(cleaned),
            )
        return cleaned

    def validate_command(self, command: str) -> str:
        """验证并清理命令字符串。

        流程：
        1. 清理 shell 注入字符
        2. 检查危险命令前缀（rm -rf / sudo / curl 等）

        Args:
            command: 用户输入的命令

        Returns:
            清理后的安全命令

        Raises:
            SecurityError: 命令包含危险前缀
        """
        safe = self.sanitize_input(command)
        lowered = safe.lower().lstrip()
        for prefix in DANGEROUS_COMMAND_PREFIXES:
            if lowered.startswith(prefix):
                logger.error(
                    "拒绝危险命令：%r（匹配黑名单 %r）", command, prefix
                )
                raise SecurityError(
                    f"命令被拒绝：包含危险前缀 {prefix!r}"
                )
        return safe

    def add_user(self, user_id: str) -> None:
        """运行时添加白名单用户（便于测试和动态扩展）。"""
        self.allowed_users.add(user_id)
        logger.info("添加白名单用户：%s", user_id)

    def remove_user(self, user_id: str) -> None:
        """运行时移除白名单用户。"""
        self.allowed_users.discard(user_id)
        logger.info("移除白名单用户：%s", user_id)