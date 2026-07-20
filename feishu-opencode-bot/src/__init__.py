"""feishu-opencode-bot 内部模块。

子模块：
- feishu_client: 飞书 lark-oapi SDK 封装（FeishuBot, MessageContext, CardActionContext）
- opencode_client: opencode HTTP API 客户端（OpencodeClient）
- security: 用户/群白名单 + 注入防护（SecurityGuard, SecurityError）
- commands: 命令解析与路由（CommandRouter, CommandParser, Command）
- cards: 飞书交互式卡片（build_session_list_card 等 + parse_action）
- types: 数据类型（Session, Agent, Message, PromptResponse）
- exceptions: OpencodeError 异常层级
"""
from src.cards import (
    Action,
    build_agent_selection_card,
    build_error_card,
    build_session_detail_card,
    build_session_list_card,
    build_simple_card,
    parse_action,
)
from src.commands import Command, CommandParser, CommandRouter
from src.exceptions import (
    OpencodeAuthError,
    OpencodeClientError,
    OpencodeError,
    OpencodeNotFoundError,
    OpencodeServerError,
    OpencodeTimeoutError,
)
from src.feishu_client import CardActionContext, FeishuBot, MessageContext
from src.opencode_client import OpencodeClient
from src.security import SecurityError, SecurityGuard
from src.types import Agent, Message, PromptResponse, Session

__version__ = "0.1.0"

__all__ = [
    "FeishuBot",
    "MessageContext",
    "CardActionContext",
    "OpencodeClient",
    "Session",
    "Agent",
    "Message",
    "PromptResponse",
    "OpencodeError",
    "OpencodeAuthError",
    "OpencodeNotFoundError",
    "OpencodeServerError",
    "OpencodeClientError",
    "OpencodeTimeoutError",
    "SecurityGuard",
    "SecurityError",
    "CommandRouter",
    "CommandParser",
    "Command",
    "parse_action",
    "Action",
    "build_session_list_card",
    "build_session_detail_card",
    "build_agent_selection_card",
    "build_simple_card",
    "build_error_card",
]
