"""飞书交互式卡片生成 + 按钮回调处理。

卡片类型：
- Session 列表卡片（带"查看详情"按钮）
- Session 详情卡片（带"切换 agent"select、"发送消息"按钮）
- Agent 选择卡片（按钮列表）
- 错误/成功/帮助 简单卡片

回调处理：
- parse_action(value: dict) -> Action：解析按钮/select 的 value 字段
- Action 包含命令和参数，可直接传给 CommandRouter.handle_text()

飞书卡片 JSON 规范 v2：
https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/feishu-cards/card-json-structure
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ===== Action 解析（按钮回调 → 命令） =====


@dataclass
class Action:
    """按钮/select 回调解析后的动作。

    Attributes:
        command: 等价的命令文本（如 "/list", "/status ses_001"）
        action_type: 原始 action 类型（view_session, switch_agent 等）
        params: 原始参数字典
    """

    command: str
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """动作是否合法（command 非空）。"""
        return bool(self.command)


# action_type 到命令模板的映射
ACTION_TEMPLATES = {
    "view_session": "/status {session_id}",
    "view_session_messages": "/status {session_id} 20",
    "switch_agent": "/switch_agent {session_id} {agent}",
    "send_message_prompt": "/send {session_id} ",  # 用户需要补全消息
    "list_sessions": "/list",
    "list_agents": "/agents",
    "refresh": "/list",  # 刷新 = 重新 list
}


def parse_action(value: dict[str, Any]) -> Action:
    """解析卡片按钮/select 回调的 value 字段。

    Args:
        value: 飞书回调 value，至少包含 {"action": "...", ...参数}

    Returns:
        Action 对象（command 字段可直接传给 CommandRouter）
        无效时返回 Action(command="", action_type="", params={})

    Examples:
        >>> parse_action({"action": "view_session", "session_id": "ses_001"})
        Action(command="/status ses_001", action_type="view_session", params={"session_id": "ses_001"})

        >>> parse_action({"action": "switch_agent", "session_id": "ses_001", "agent": "atlas"})
        Action(command="/switch_agent ses_001 atlas", ...)
    """
    if not isinstance(value, dict):
        logger.warning("parse_action 收到非 dict 输入：%r", value)
        return Action(command="", action_type="", params={})

    action_type = value.get("action", "")
    if not action_type:
        logger.warning("value 缺少 action 字段：%r", value)
        return Action(command="", action_type="", params=value)

    template = ACTION_TEMPLATES.get(action_type)
    if template is None:
        logger.warning("未知 action_type：%s（value=%r）", action_type, value)
        return Action(command="", action_type=action_type, params=value)

    try:
        # 用 value 中的字段填充模板
        # 排除 action 字段本身
        params = {k: v for k, v in value.items() if k != "action"}
        command = template.format(**params)
    except KeyError as e:
        logger.warning("action %s 缺少参数 %s（value=%r）", action_type, e, value)
        return Action(command="", action_type=action_type, params=value)
    except Exception as e:
        logger.exception("action 解析异常：%s", e)
        return Action(command="", action_type=action_type, params=value)

    return Action(command=command, action_type=action_type, params=params)


# ===== 卡片构建函数 =====


def _wrap_card(
    title: str,
    elements: list[dict],
    template: str = "blue",
    wide_screen: bool = True,
) -> dict:
    """包装卡片 JSON 外壳。"""
    return {
        "config": {
            "wide_screen_mode": wide_screen,
            "enable_forward": False,
        },
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": template,
        },
        "elements": elements,
    }


def _button(
    text: str,
    action: str,
    params: Optional[dict] = None,
    btn_type: str = "default",
    confirm: Optional[str] = None,
) -> dict:
    """构建按钮元素。

    Args:
        text: 按钮文字
        action: action_type（view_session, switch_agent 等）
        params: value 中的附加参数（session_id, agent 等）
        btn_type: primary / default / danger
        confirm: 确认对话框文字（None 表示无确认）
    """
    value = {"action": action, **(params or {})}
    button: dict[str, Any] = {
        "tag": "button",
        "text": {"tag": "plain_text", "content": text},
        "value": value,
        "type": btn_type,
    }
    if confirm:
        button["confirm"] = {
            "title": {"tag": "plain_text", "content": "确认"},
            "text": {"tag": "plain_text", "content": confirm},
        }
    return button


def _md_text(content: str) -> dict:
    """构建 markdown 文本元素。"""
    return {"tag": "div", "text": {"tag": "lark_md", "content": content}}


def _divider() -> dict:
    """构建分隔线元素。"""
    return {"tag": "hr"}


def _note(content: str) -> dict:
    """构建备注元素（卡片底部）。"""
    return {
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": content}],
    }


def _action_row(*buttons: dict) -> dict:
    """构建 action 行（包含多个按钮）。"""
    return {"tag": "action", "actions": list(buttons)}


def build_session_list_card(
    sessions: list[dict],
    show_buttons: bool = True,
    max_sessions: int = 20,
) -> dict:
    """构建 Session 列表卡片。

    Args:
        sessions: OpencodeClient.list_sessions() 返回的 session 列表
        show_buttons: 是否为每个 session 添加"查看"按钮
        max_sessions: 最大显示数（避免卡片过长）

    Returns:
        飞书卡片 JSON
    """
    total = len(sessions)
    truncated = sessions[:max_sessions]
    truncated_count = total - len(truncated)

    if total == 0:
        return _wrap_card(
            "📭 暂无 opencode session",
            [
                _md_text("当前没有正在运行的 session"),
                _md_text("💡 提示：opencode serve 应至少有 1 个活跃 session"),
            ],
            template="yellow",
        )

    elements: list[dict] = [_md_text(f"**共 {total} 个 session**：")]
    elements.append(_divider())

    for s in truncated:
        sid = s.get("id", "?")
        agent = s.get("agent", "?")
        title = s.get("title", "")
        model = s.get("model", "")

        # 文本行
        title_str = f" — {title}" if title else ""
        model_str = f" `{model}`" if model else ""
        elements.append(_md_text(
            f"🔹 `{sid}` **[{agent}]**{model_str}{title_str}"
        ))

        # 按钮行（可选）
        if show_buttons:
            elements.append(_action_row(
                _button(
                    text=f"查看 {sid[:8]}…",
                    action="view_session",
                    params={"session_id": sid},
                    btn_type="primary",
                ),
                _button(
                    text="切换 agent",
                    action="switch_agent",
                    params={"session_id": sid, "agent": ""},  # 触发 agent 选择
                    btn_type="default",
                ),
            ))

    if truncated_count > 0:
        elements.append(_note(f"（仅显示前 {max_sessions} 个，共 {total} 个 session）"))
    else:
        elements.append(_note("点击按钮查看详情，或发送 `/help` 查看命令"))

    return _wrap_card(
        f"📋 opencode sessions（{total}）",
        elements,
        template="blue",
    )


def build_session_detail_card(
    session: dict,
    messages: Optional[list[dict]] = None,
    agents: Optional[list[dict]] = None,
    message_count: int = 5,
) -> dict:
    """构建 Session 详情卡片（带切换 agent + 发送消息按钮）。

    Args:
        session: get_session() 返回的 session 详情
        messages: get_messages() 返回的消息历史（可选，None 不显示）
        agents: list_agents() 返回的 agent 列表（用于 select 下拉）
        message_count: 显示的消息条数

    Returns:
        飞书卡片 JSON
    """
    sid = session.get("id", "?")
    agent = session.get("agent", "?")
    title = session.get("title", "")
    model = session.get("model", "")
    created = session.get("createdAt", "?")
    updated = session.get("updatedAt", "?")

    elements: list[dict] = [
        _md_text(
            f"**Session ID**：`{sid}`\n"
            f"**Agent**：`{agent}`\n"
            + (f"**Title**：{title}\n" if title else "")
            + (f"**Model**：`{model}`\n" if model else "")
            + f"**Created**：{created}\n"
            f"**Updated**：{updated}"
        ),
    ]

    # 消息历史
    if messages is not None:
        elements.append(_divider())
        if not messages:
            elements.append(_md_text("💤 暂无消息历史"))
        else:
            recent = messages[-message_count:] if message_count > 0 else []
            if recent:
                elements.append(_md_text(f"**💬 最近 {len(recent)} 条消息**："))
                for msg in recent:
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    if len(content) > 150:
                        content = content[:150] + "..."
                    icon = "👤" if role == "user" else "🤖"
                    elements.append(_md_text(f"{icon} `[{role}]` {content}"))

    # 切换 agent（select 下拉）
    if agents:
        elements.append(_divider())
        elements.append(_md_text("**切换 agent**："))
        options = [
            {
                "text": {"tag": "plain_text", "content": f"{a.get('id', '?')} — {a.get('name', '')}"},
                "value": a.get("id", ""),
            }
            for a in agents
            if a.get("id")
        ]
        elements.append({
            "tag": "select",
            "placeholder": {"tag": "plain_text", "content": "选择新 agent"},
            "value": {"action": "switch_agent_select", "session_id": sid},
            "options": options,
        })

    # 操作按钮
    elements.append(_divider())
    elements.append(_action_row(
        _button(
            text="🔄 刷新",
            action="view_session",
            params={"session_id": sid},
            btn_type="default",
        ),
        _button(
            text="📋 全部 session",
            action="list_sessions",
            btn_type="default",
        ),
        _button(
            text="🤖 可用 agent",
            action="list_agents",
            btn_type="default",
        ),
    ))

    elements.append(_note(f"session: {sid}"))

    return _wrap_card(
        f"📊 Session: {sid[:16]}…",
        elements,
        template="green",
    )


def build_agent_selection_card(
    session_id: str,
    agents: list[dict],
    current_agent: str = "",
) -> dict:
    """构建 Agent 选择卡片（按钮列表）。

    用于 /switch_agent 命令的视觉化操作。

    Args:
        session_id: 目标 session
        agents: 可用 agent 列表
        current_agent: 当前 agent（标记当前选项）

    Returns:
        飞书卡片 JSON
    """
    if not agents:
        return _wrap_card(
            "📭 无可用 agent",
            [
                _md_text("opencode serve 未配置任何 agent"),
                _md_text("检查 `~/.config/opencode/oh-my-openagent.json`"),
            ],
            template="red",
        )

    elements: list[dict] = [
        _md_text(f"为 session `{session_id}` 选择新 agent："),
        _divider(),
    ]

    # 每个 agent 一个按钮（一行 1 个，便于点击）
    for a in agents:
        aid = a.get("id", "?")
        name = a.get("name", "")
        desc = a.get("description", "")
        model = a.get("model", "")

        # 当前 agent 高亮（disabled 风格）
        is_current = aid.lower() == current_agent.lower()

        # 文本
        title = f"**`{aid}`**"
        if name:
            title += f" — {name}"
        if model:
            title += f" `{model}`"
        if is_current:
            title += " ✓（当前）"
        elements.append(_md_text(title))

        if desc:
            desc_preview = desc[:100] + ("..." if len(desc) > 100 else "")
            elements.append(_md_text(f"  {desc_preview}"))

        # 按钮（不是当前 agent 才可点）
        if not is_current:
            elements.append(_action_row(
                _button(
                    text=f"切换到 {aid}",
                    action="switch_agent",
                    params={"session_id": session_id, "agent": aid},
                    btn_type="primary",
                    confirm=f"确认将 session {session_id} 切换到 agent {aid}？",
                ),
            ))

    elements.append(_divider())
    elements.append(_note(f"session: {session_id} | 共 {len(agents)} 个 agent"))

    return _wrap_card(
        "🤖 选择 Agent",
        elements,
        template="violet",
    )


def build_simple_card(
    title: str,
    body: str,
    template: str = "blue",
    footer: Optional[str] = None,
) -> dict:
    """构建简单卡片（标题 + markdown 正文 + 可选 footer）。

    用于 /help, /unknown command, 错误提示等。

    Args:
        title: 卡片标题
        body: markdown 正文
        template: 颜色模板（blue/green/yellow/red/grey/turquoise/indigo/violet）
        footer: 底部备注（可选）
    """
    elements = [_md_text(body)]
    if footer:
        elements.append(_note(footer))
    return _wrap_card(title, elements, template=template)


def build_error_card(
    title: str,
    error_message: str,
    hint: Optional[str] = None,
) -> dict:
    """构建错误卡片。

    Args:
        title: 错误标题（如"获取 session 失败"）
        error_message: 错误详情
        hint: 用户可执行的提示（如"输入 /list 查看"）
    """
    elements = [
        _md_text(f"**错误详情**：\n```\n{error_message}\n```"),
    ]
    if hint:
        elements.append(_divider())
        elements.append(_md_text(f"💡 **建议**：{hint}"))

    return _wrap_card(
        f"❌ {title}",
        elements,
        template="red",
    )


# ===== 工具函数 =====


def validate_card(card: dict) -> bool:
    """校验卡片 JSON 是否基本合规（用于测试）。

    Args:
        card: 待校验的卡片 JSON

    Returns:
        True = 合规（有 config/header/elements），False = 不合规
    """
    if not isinstance(card, dict):
        return False
    if "elements" not in card or not isinstance(card["elements"], list):
        return False
    if "header" not in card:
        return False
    header = card["header"]
    if not isinstance(header, dict):
        return False
    if "title" not in header:
        return False
    return True


def count_buttons(card: dict) -> int:
    """统计卡片中的按钮总数。"""
    if not isinstance(card, dict):
        return 0
    count = 0
    for element in card.get("elements", []):
        if element.get("tag") == "action":
            for action in element.get("actions", []):
                if action.get("tag") == "button":
                    count += 1
    return count
