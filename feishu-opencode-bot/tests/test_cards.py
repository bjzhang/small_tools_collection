"""卡片模块单元测试。"""
from __future__ import annotations

import pytest

from src.cards import (
    ACTION_TEMPLATES,
    Action,
    build_agent_selection_card,
    build_error_card,
    build_session_detail_card,
    build_session_list_card,
    build_simple_card,
    count_buttons,
    parse_action,
    validate_card,
)


# ===== Action 解析测试 =====


def test_parse_action_view_session():
    """解析 view_session 按钮 → /status 命令。"""
    action = parse_action({"action": "view_session", "session_id": "ses_001"})
    assert action.is_valid
    assert action.command == "/status ses_001"
    assert action.action_type == "view_session"
    assert action.params == {"session_id": "ses_001"}


def test_parse_action_switch_agent():
    """解析 switch_agent 按钮 → /switch_agent 命令。"""
    action = parse_action({
        "action": "switch_agent",
        "session_id": "ses_001",
        "agent": "atlas",
    })
    assert action.command == "/switch_agent ses_001 atlas"
    assert action.action_type == "switch_agent"


def test_parse_action_list_sessions():
    """解析 list_sessions 按钮 → /list。"""
    action = parse_action({"action": "list_sessions"})
    assert action.command == "/list"


def test_parse_action_list_agents():
    """解析 list_agents 按钮 → /agents。"""
    action = parse_action({"action": "list_agents"})
    assert action.command == "/agents"


def test_parse_action_view_session_messages():
    """解析 view_session_messages → /status sid 20。"""
    action = parse_action({
        "action": "view_session_messages",
        "session_id": "ses_001",
    })
    assert action.command == "/status ses_001 20"


def test_parse_action_empty():
    """空 dict 返回无效 Action。"""
    action = parse_action({})
    assert not action.is_valid
    assert action.command == ""


def test_parse_action_missing_action_key():
    """缺 action 字段返回无效 Action。"""
    action = parse_action({"session_id": "ses_001"})
    assert not action.is_valid


def test_parse_action_unknown_action_type():
    """未知 action_type 返回无效 Action（但保留原始参数）。"""
    action = parse_action({"action": "foobar", "session_id": "ses_001"})
    assert not action.is_valid
    assert action.action_type == "foobar"


def test_parse_action_missing_params():
    """action 模板需要参数但参数缺失返回无效 Action。"""
    action = parse_action({"action": "view_session"})
    assert not action.is_valid


def test_parse_action_non_dict():
    """非 dict 输入返回无效 Action。"""
    assert not parse_action(None).is_valid  # type: ignore[arg-type]
    assert not parse_action("string").is_valid  # type: ignore[arg-type]
    assert not parse_action([]).is_valid  # type: ignore[arg-type]


def test_action_templates_completeness():
    """ACTION_TEMPLATES 覆盖所有声明的 action。"""
    expected = {
        "view_session",
        "view_session_messages",
        "switch_agent",
        "send_message_prompt",
        "list_sessions",
        "list_agents",
        "refresh",
    }
    assert expected.issubset(set(ACTION_TEMPLATES.keys()))


# ===== Session 列表卡片测试 =====


def test_session_list_card_empty():
    """空列表生成"暂无"卡片。"""
    card = build_session_list_card([])
    assert validate_card(card)
    assert "暂无" in card["header"]["title"]["content"]
    assert card["header"]["template"] == "yellow"


def test_session_list_card_with_sessions():
    """有 sessions 的卡片。"""
    sessions = [
        {"id": "ses_001", "agent": "prometheus", "title": "Plan A", "model": "glm-5.2"},
        {"id": "ses_002", "agent": "atlas", "title": "Execute B"},
    ]
    card = build_session_list_card(sessions)
    assert validate_card(card)
    assert "2" in card["header"]["title"]["content"]
    elements_str = str(card["elements"])
    assert "ses_001" in elements_str
    assert "ses_002" in elements_str
    assert "prometheus" in elements_str
    assert "atlas" in elements_str
    assert count_buttons(card) >= 4  # 每个 session 至少 2 个按钮


def test_session_list_card_no_buttons():
    """show_buttons=False 时不生成按钮。"""
    sessions = [{"id": "ses_001", "agent": "build"}]
    card = build_session_list_card(sessions, show_buttons=False)
    assert validate_card(card)
    assert count_buttons(card) == 0


def test_session_list_card_truncation():
    """超过 max_sessions 时截断。"""
    sessions = [{"id": f"ses_{i:03d}", "agent": "build"} for i in range(30)]
    card = build_session_list_card(sessions, max_sessions=10)
    assert validate_card(card)
    elements_str = str(card["elements"])
    assert "仅显示前 10" in elements_str
    assert "共 30" in elements_str


def test_session_list_card_button_actions():
    """按钮 value 包含正确 action。"""
    sessions = [{"id": "ses_001", "agent": "build"}]
    card = build_session_list_card(sessions)
    actions_found = []
    for el in card["elements"]:
        if el.get("tag") == "action":
            for action in el.get("actions", []):
                if action.get("tag") == "button":
                    actions_found.append(action["value"])

    view_actions = [a for a in actions_found if a.get("action") == "view_session"]
    assert len(view_actions) >= 1
    assert view_actions[0]["session_id"] == "ses_001"


# ===== Session 详情卡片测试 =====


def test_session_detail_card_basic():
    """基本详情卡片。"""
    session = {
        "id": "ses_001",
        "agent": "prometheus",
        "title": "Plan A",
        "model": "glm-5.2",
        "createdAt": "2026-07-19",
        "updatedAt": "2026-07-20",
    }
    card = build_session_detail_card(session)
    assert validate_card(card)
    assert card["header"]["template"] == "green"
    elements_str = str(card["elements"])
    assert "ses_001" in elements_str
    assert "prometheus" in elements_str
    assert "Plan A" in elements_str


def test_session_detail_card_with_messages():
    """详情卡片含消息历史。"""
    session = {"id": "ses_001", "agent": "build"}
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]
    card = build_session_detail_card(session, messages=messages)
    elements_str = str(card["elements"])
    assert "hello" in elements_str
    assert "hi there" in elements_str


def test_session_detail_card_empty_messages():
    """空消息历史显示"暂无"。"""
    session = {"id": "ses_001", "agent": "build"}
    card = build_session_detail_card(session, messages=[])
    elements_str = str(card["elements"])
    assert "暂无消息" in elements_str


def test_session_detail_card_with_agent_select():
    """详情卡片含 agent select 下拉。"""
    session = {"id": "ses_001", "agent": "prometheus"}
    agents = [
        {"id": "prometheus", "name": "Plan Builder"},
        {"id": "atlas", "name": "Executor"},
    ]
    card = build_session_detail_card(session, agents=agents)
    elements_str = str(card["elements"])
    assert "select" in elements_str
    assert "prometheus" in elements_str
    assert "atlas" in elements_str


def test_session_detail_card_action_buttons():
    """详情卡片有刷新/列表/agents 按钮。"""
    session = {"id": "ses_001", "agent": "build"}
    card = build_session_detail_card(session)
    assert count_buttons(card) >= 3


def test_session_detail_card_message_truncation():
    """长消息（>150 字符）被截断。"""
    session = {"id": "ses_001", "agent": "build"}
    long_msg = "x" * 200
    messages = [{"role": "user", "content": long_msg}]
    card = build_session_detail_card(session, messages=messages)
    elements_str = str(card["elements"])
    assert "..." in elements_str
    assert long_msg not in elements_str


# ===== Agent 选择卡片测试 =====


def test_agent_selection_card_basic():
    """基本 agent 选择卡片。"""
    agents = [
        {"id": "prometheus", "name": "Plan Builder", "description": "战略规划"},
        {"id": "atlas", "name": "Executor"},
    ]
    card = build_agent_selection_card("ses_001", agents)
    assert validate_card(card)
    assert card["header"]["template"] == "violet"
    elements_str = str(card["elements"])
    assert "ses_001" in elements_str
    assert "prometheus" in elements_str
    assert "atlas" in elements_str


def test_agent_selection_card_empty():
    """空 agent 列表显示错误卡片。"""
    card = build_agent_selection_card("ses_001", [])
    assert validate_card(card)
    assert card["header"]["template"] == "red"
    assert "无可用 agent" in card["header"]["title"]["content"]
    elements_str = str(card["elements"])
    assert "未配置任何 agent" in elements_str


def test_agent_selection_card_marks_current():
    """当前 agent 被标记。"""
    agents = [
        {"id": "prometheus", "name": "Plan"},
        {"id": "atlas", "name": "Exec"},
    ]
    card = build_agent_selection_card("ses_001", agents, current_agent="prometheus")
    elements_str = str(card["elements"])
    assert "当前" in elements_str


def test_agent_selection_card_buttons():
    """每个非当前 agent 有切换按钮。"""
    agents = [
        {"id": "prometheus"},
        {"id": "atlas"},
        {"id": "sisyphus"},
    ]
    card = build_agent_selection_card("ses_001", agents)
    assert count_buttons(card) == 3


def test_agent_selection_card_skips_current_button():
    """当前 agent 不生成按钮（已是当前）。"""
    agents = [
        {"id": "prometheus"},
        {"id": "atlas"},
    ]
    card = build_agent_selection_card("ses_001", agents, current_agent="atlas")
    assert count_buttons(card) == 1


def test_agent_selection_card_button_has_confirm():
    """切换按钮有确认对话框。"""
    agents = [{"id": "prometheus"}]
    card = build_agent_selection_card("ses_001", agents)
    for el in card["elements"]:
        if el.get("tag") == "action":
            for action in el.get("actions", []):
                if action.get("tag") == "button":
                    assert "confirm" in action
                    assert "切换" in action["confirm"]["text"]["content"]


# ===== 简单/错误卡片测试 =====


def test_simple_card():
    """简单卡片。"""
    card = build_simple_card("标题", "**body**", footer="备注")
    assert validate_card(card)
    elements_str = str(card["elements"])
    assert "body" in elements_str
    assert "备注" in elements_str


def test_simple_card_no_footer():
    """无 footer 的简单卡片。"""
    card = build_simple_card("标题", "body")
    assert validate_card(card)


def test_error_card():
    """错误卡片。"""
    card = build_error_card("获取失败", "connection refused", hint="检查 opencode serve")
    assert validate_card(card)
    assert card["header"]["template"] == "red"
    elements_str = str(card["elements"])
    assert "connection refused" in elements_str
    assert "检查 opencode serve" in elements_str


def test_error_card_no_hint():
    """无 hint 的错误卡片。"""
    card = build_error_card("错误", "details")
    assert validate_card(card)


# ===== 工具函数测试 =====


def test_validate_card_valid():
    """合规卡片返回 True。"""
    card = {
        "config": {},
        "header": {"title": {"tag": "plain_text", "content": "x"}, "template": "blue"},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "hi"}}],
    }
    assert validate_card(card) is True


def test_validate_card_invalid():
    """不合规卡片返回 False。"""
    assert validate_card(None) is False  # type: ignore[arg-type]
    assert validate_card("string") is False  # type: ignore[arg-type]
    assert validate_card({}) is False
    assert validate_card({"header": {}}) is False  # 缺 elements
    assert validate_card({"elements": []}) is False  # 缺 header


def test_count_buttons():
    """统计按钮数。"""
    card = {
        "elements": [
            {"tag": "action", "actions": [
                {"tag": "button"},
                {"tag": "button"},
            ]},
            {"tag": "action", "actions": [
                {"tag": "button"},
            ]},
            {"tag": "div"},
        ]
    }
    assert count_buttons(card) == 3


def test_count_buttons_empty():
    """空卡片 0 个按钮。"""
    assert count_buttons({}) == 0
    assert count_buttons({"elements": []}) == 0
