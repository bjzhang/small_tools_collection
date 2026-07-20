"""命令解析器和路由器的单元测试。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.commands import Command, CommandParser, CommandRouter


# ===== CommandParser 测试 =====


def test_parse_simple():
    """解析简单命令 /list。"""
    cmd = CommandParser.parse("/list")
    assert cmd is not None
    assert cmd.name == "list"
    assert cmd.raw_name == "list"
    assert cmd.args == []
    assert cmd.raw_text == "/list"


def test_parse_with_args():
    """解析带参数命令。"""
    cmd = CommandParser.parse("/status ses_001")
    assert cmd is not None
    assert cmd.name == "status"
    assert cmd.args == ["ses_001"]


def test_parse_multiple_args():
    """多参数命令（send 消息）。"""
    cmd = CommandParser.parse("/send ses_001 hello world")
    assert cmd is not None
    assert cmd.name == "send"
    assert cmd.args == ["ses_001", "hello", "world"]


def test_parse_case_insensitive():
    """命令名大小写不敏感。"""
    cmd = CommandParser.parse("/LIST")
    assert cmd is not None
    assert cmd.name == "list"
    assert cmd.raw_name == "LIST"


def test_parse_mixed_case():
    """混合大小写。"""
    cmd = CommandParser.parse("/List")
    assert cmd is not None
    assert cmd.name == "list"
    assert cmd.raw_name == "List"


def test_parse_empty():
    """空输入返回 None。"""
    assert CommandParser.parse("") is None
    assert CommandParser.parse("   ") is None
    assert CommandParser.parse(None) is None  # type: ignore[arg-type]


def test_parse_non_command():
    """非 / 开头不是命令。"""
    assert CommandParser.parse("hello") is None
    assert CommandParser.parse("list") is None  # 缺 / 前缀
    assert CommandParser.parse("# comment") is None


def test_parse_only_slash():
    """只有 / 不是命令。"""
    assert CommandParser.parse("/") is None


def test_parse_strips_whitespace():
    """前后空格被去除。"""
    cmd = CommandParser.parse("  /list  ")
    assert cmd is not None
    assert cmd.raw_text == "/list"


# ===== Command 数据类测试 =====


def test_command_is_valid():
    """命令名以字母开头时 is_valid 为 True。"""
    assert Command(name="list", raw_name="list", args=[], raw_text="/list").is_valid
    assert Command(name="switch_agent", raw_name="switch_agent", args=[], raw_text="/x").is_valid


def test_command_is_invalid_empty():
    """空命令名无效。"""
    assert not Command(name="", raw_name="", args=[], raw_text="").is_valid


def test_command_is_invalid_numeric():
    """数字开头的命令名无效。"""
    assert not Command(name="123", raw_name="123", args=[], raw_text="/123").is_valid


# ===== CommandRouter /list 测试 =====


@pytest.fixture
def mock_opencode():
    """Mock OpencodeClient。"""
    client = MagicMock()
    client.list_sessions = AsyncMock()
    client.get_session = AsyncMock()
    client.get_messages = AsyncMock()
    client.send_message = AsyncMock()
    return client


@pytest.fixture
def router(mock_opencode):
    return CommandRouter(mock_opencode)


async def test_list_command_empty(router: CommandRouter, mock_opencode):
    """空 session 列表返回友好提示。"""
    mock_opencode.list_sessions.return_value = []
    response = await router.handle_text("/list")
    assert "📭" in response
    assert "没有" in response


async def test_list_command_with_sessions(router: CommandRouter, mock_opencode):
    """/list 返回格式化的 session 列表。"""
    mock_opencode.list_sessions.return_value = [
        {"id": "ses_001", "agent": "prometheus", "title": "Plan A"},
        {"id": "ses_002", "agent": "atlas", "title": "Execute B"},
    ]
    response = await router.handle_text("/list")
    assert "📋" in response
    assert "2 个" in response
    assert "ses_001" in response
    assert "ses_002" in response
    assert "prometheus" in response
    assert "atlas" in response
    assert "Plan A" in response


async def test_list_command_without_title(router: CommandRouter, mock_opencode):
    """session 无 title 时不显示 —。"""
    mock_opencode.list_sessions.return_value = [
        {"id": "ses_x", "agent": "build"},
    ]
    response = await router.handle_text("/list")
    assert "ses_x" in response
    assert "build" in response
    assert " — " not in response


async def test_list_command_opencode_error(router: CommandRouter, mock_opencode):
    """opencode_client 抛错时返回错误提示。"""
    mock_opencode.list_sessions.side_effect = RuntimeError("connection refused")
    response = await router.handle_text("/list")
    assert "❌" in response
    assert "connection refused" in response


# ===== /help 测试 =====


async def test_help_command(router: CommandRouter):
    """/help 返回完整帮助文本。"""
    response = await router.handle_text("/help")
    assert "📖" in response
    assert "/list" in response
    assert "/help" in response
    # 计划中的命令（Task 6-7）也应在帮助中
    assert "/status" in response
    assert "/send" in response
    assert "/switch_agent" in response
    # 示例
    assert "示例" in response


async def test_help_command_lists_implemented(router: CommandRouter):
    """/help 列出已实现的命令。"""
    response = await router.handle_text("/help")
    # 已实现：list, help
    assert "/list" in response
    assert "/help" in response


# ===== 未知命令测试 =====


async def test_unknown_command(router: CommandRouter):
    """未知命令返回友好提示。"""
    response = await router.handle_text("/foobar")
    assert "❓" in response
    assert "未知命令" in response
    assert "/foobar" in response
    # 提示已知命令
    assert "/list" in response
    assert "/help" in response
    # 提示用 /help
    assert "/help" in response


async def test_invalid_command_numeric(router: CommandRouter):
    """数字开头的命令无效。"""
    response = await router.handle_text("/123abc")
    assert "❌" in response or "❓" in response


# ===== dispatch / handle_text 测试 =====


async def test_handle_text_non_command_returns_none(router: CommandRouter):
    """非命令文本返回 None。"""
    assert await router.handle_text("hello") is None
    assert await router.handle_text("") is None
    assert await router.handle_text("   ") is None


async def test_dispatch_routes_to_correct_handler(router: CommandRouter, mock_opencode):
    """dispatch 把命令分发到正确 handler。"""
    mock_opencode.list_sessions.return_value = []
    cmd = Command(name="list", raw_name="list", args=[], raw_text="/list")
    response = await router.dispatch(cmd)
    assert "📭" in response or "📋" in response


async def test_register_custom_command(router: CommandRouter):
    """自定义命令可以通过 register 注册。"""
    custom_handler = AsyncMock(return_value="custom response")
    router.register("custom", custom_handler)

    response = await router.handle_text("/custom")
    assert response == "custom response"
    custom_handler.assert_called_once()


async def test_handler_exception_returns_error(router: CommandRouter, mock_opencode):
    """handler 抛错时返回错误提示，不传播异常。"""
    mock_opencode.list_sessions.side_effect = ValueError("test error")
    response = await router.handle_text("/list")
    assert "❌" in response
    assert "test error" in response


# ===== list_commands 测试 =====


def test_list_commands_default(router: CommandRouter):
    """默认注册 list 和 help。"""
    commands = router.list_commands()
    assert "list" in commands
    assert "help" in commands
    assert len(commands) >= 2


def test_list_commands_after_register(router: CommandRouter):
    """register 后 list_commands 包含新命令。"""
    router.register("custom", AsyncMock())
    commands = router.list_commands()
    assert "custom" in commands


def test_list_commands_sorted(router: CommandRouter):
    """list_commands 返回排序后的命令。"""
    router.register("zebra", AsyncMock())
    router.register("alpha", AsyncMock())
    commands = router.list_commands()
    # 排序后 alpha 应该在 zebra 前
    assert commands.index("alpha") < commands.index("zebra")


# ===== Task 6: /status 测试 =====


async def test_status_no_args(router: CommandRouter):
    """/status 无参数返回用法提示。"""
    response = await router.handle_text("/status")
    assert "❌" in response
    assert "用法" in response


async def test_status_success(router: CommandRouter, mock_opencode):
    """/status 成功返回详情 + 最近消息。"""
    mock_opencode.get_session.return_value = {
        "id": "ses_001",
        "agent": "prometheus",
        "title": "Plan A",
        "createdAt": "2026-07-19",
        "updatedAt": "2026-07-20",
        "model": "glm-5.2",
    }
    mock_opencode.get_messages.return_value = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
    ]
    response = await router.handle_text("/status ses_001")
    assert "📊" in response
    assert "ses_001" in response
    assert "prometheus" in response
    assert "Plan A" in response
    assert "💬" in response
    assert "你好" in response


async def test_status_with_message_count(router: CommandRouter, mock_opencode):
    """/status ses_001 10 指定消息条数。"""
    mock_opencode.get_session.return_value = {"id": "ses_001", "agent": "build"}
    mock_opencode.get_messages.return_value = [
        {"role": "user", "content": f"msg {i}"} for i in range(15)
    ]
    response = await router.handle_text("/status ses_001 10")
    assert "msg 14" in response
    assert "msg 0" not in response


async def test_status_invalid_count(router: CommandRouter, mock_opencode):
    """/status ses_001 abc 非法消息条数。"""
    response = await router.handle_text("/status ses_001 abc")
    assert "❌" in response
    assert "无效的消息条数" in response


async def test_status_count_out_of_range(router: CommandRouter, mock_opencode):
    """/status ses_001 100 超出范围。"""
    response = await router.handle_text("/status ses_001 100")
    assert "❌" in response
    assert "0-50" in response


async def test_status_not_found(router: CommandRouter, mock_opencode):
    """/status 不存在的 session 友好提示。"""
    mock_opencode.get_session.side_effect = RuntimeError("404 Not Found")
    response = await router.handle_text("/status ses_unknown")
    assert "❌" in response
    assert "不存在" in response
    assert "/list" in response


async def test_status_zero_messages(router: CommandRouter, mock_opencode):
    """/status ses_001 0 不显示消息。"""
    mock_opencode.get_session.return_value = {"id": "ses_001", "agent": "build"}
    mock_opencode.get_messages.return_value = [
        {"role": "user", "content": "should not appear"}
    ]
    response = await router.handle_text("/status ses_001 0")
    assert "📊" in response
    assert "should not appear" not in response
    mock_opencode.get_messages.assert_not_called()


async def test_status_opencode_error(router: CommandRouter, mock_opencode):
    """/status opencode_client 抛错时返回错误。"""
    mock_opencode.get_session.side_effect = ConnectionError("network down")
    response = await router.handle_text("/status ses_001")
    assert "❌" in response
    assert "network down" in response


async def test_status_truncates_long_message(router: CommandRouter, mock_opencode):
    """/status 截断超长消息（>200 字符）。"""
    mock_opencode.get_session.return_value = {"id": "ses_001", "agent": "build"}
    long_msg = "x" * 300
    mock_opencode.get_messages.return_value = [
        {"role": "user", "content": long_msg}
    ]
    response = await router.handle_text("/status ses_001")
    assert "..." in response
    assert long_msg not in response


# ===== Task 6: /send 测试 =====


async def test_send_no_args(router: CommandRouter):
    """/send 无参数返回用法提示。"""
    response = await router.handle_text("/send")
    assert "❌" in response
    assert "用法" in response


async def test_send_only_session_id(router: CommandRouter):
    """/send ses_001（无消息）返回用法提示。"""
    response = await router.handle_text("/send ses_001")
    assert "❌" in response


async def test_send_success(router: CommandRouter, mock_opencode):
    """/send 成功发送消息。"""
    mock_opencode.send_message.return_value = {"id": "msg_001", "sessionID": "ses_001"}
    response = await router.handle_text("/send ses_001 重启服务")
    assert "✅" in response
    assert "ses_001" in response
    assert "msg_001" in response
    assert "重启服务" in response
    mock_opencode.send_message.assert_called_once_with("ses_001", "重启服务")


async def test_send_multi_word_message(router: CommandRouter, mock_opencode):
    """/send 多词消息保留空格。"""
    mock_opencode.send_message.return_value = {"id": "msg_x"}
    response = await router.handle_text("/send ses_001 hello world from bot")
    assert "✅" in response
    mock_opencode.send_message.assert_called_once_with(
        "ses_001", "hello world from bot"
    )


async def test_send_with_security_guard(router: CommandRouter, mock_opencode):
    """/send 如果 router 有 _security_guard，消息被清理。"""
    guard = MagicMock()
    guard.sanitize_input = lambda x: x.replace(";", "")
    router._security_guard = guard

    mock_opencode.send_message.return_value = {"id": "msg_x"}
    response = await router.handle_text("/send ses_001 hello;rm -rf /")
    assert "✅" in response
    mock_opencode.send_message.assert_called_once_with("ses_001", "hellorm -rf /")


async def test_send_empty_message_after_sanitize(router: CommandRouter, mock_opencode):
    """/send 消息清理后为空时报错。"""
    guard = MagicMock()
    guard.sanitize_input = lambda x: ""
    router._security_guard = guard

    response = await router.handle_text("/send ses_001 ;;;")
    assert "❌" in response
    assert "清理后为空" in response
    mock_opencode.send_message.assert_not_called()


async def test_send_opencode_error(router: CommandRouter, mock_opencode):
    """/send opencode_client 抛错时返回错误。"""
    mock_opencode.send_message.side_effect = RuntimeError("session closed")
    response = await router.handle_text("/send ses_001 hello")
    assert "❌" in response
    assert "session closed" in response


async def test_send_not_found(router: CommandRouter, mock_opencode):
    """/send 不存在的 session 友好提示。"""
    mock_opencode.send_message.side_effect = RuntimeError("404 Not Found")
    response = await router.handle_text("/send ses_unknown hello")
    assert "❌" in response
    assert "不存在" in response


async def test_send_long_message_preview(router: CommandRouter, mock_opencode):
    """/send 长消息预览只显示前 50 字符。"""
    mock_opencode.send_message.return_value = {"id": "msg_x"}
    long_msg = "a" * 100
    response = await router.handle_text(f"/send ses_001 {long_msg}")
    assert "✅" in response
    assert "..." in response


# ===== 注册验证 =====


def test_router_registers_status_and_send(router: CommandRouter):
    """CommandRouter 默认注册 status 和 send。"""
    commands = router.list_commands()
    assert "status" in commands
    assert "send" in commands
