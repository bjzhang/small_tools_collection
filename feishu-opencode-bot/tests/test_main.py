"""BotApp 集成测试（不依赖真实飞书/opencode 连接）。"""
from __future__ import annotations

import signal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import main
from main import BotApp


@pytest.fixture
def app_config():
    return {
        "feishu": {
            "app_id": "cli_test",
            "app_secret": "secret",
        },
        "opencode": {
            "base_url": "http://127.0.0.1:4096",
            "username": "opencode",
            "password": "test-pass",
        },
        "security": {
            "allowed_users": ["ou_alice", "ou_bob"],
            "allowed_chats": ["oc_test_group"],
        },
        "logging": {
            "level": "INFO",
            "file": None,
        },
    }


@pytest.fixture
def app(app_config):
    return BotApp(app_config)


def _build_mock_ctx(
    user_id="ou_alice",
    chat_type="p2p",
    text="hello",
    is_at_bot=False,
    message_type="text",
):
    ctx = MagicMock()
    ctx.user_id = user_id
    ctx.chat_type = chat_type
    ctx.text = text
    ctx.is_at_bot = is_at_bot
    ctx.message_type = message_type
    ctx.message_id = "om_test001"
    ctx.chat_id = "oc_test_chat"
    return ctx


def _build_mock_card_ctx(value=None, operator_open_id="ou_alice"):
    ctx = MagicMock()
    ctx.value = value if value is not None else {}
    ctx.operator_open_id = operator_open_id
    ctx.user_id = operator_open_id
    ctx.tag = "button"
    return ctx


# ===== 组件初始化测试 =====


def test_app_initialization(app):
    assert app.security is not None
    assert app.opencode is not None
    assert app.router is not None
    assert app.bot is not None


def test_app_registers_handlers(app):
    assert app.bot.on_message is not None
    assert app.bot.on_card_action is not None


def test_app_security_whitelist_loaded(app):
    assert "ou_alice" in app.security.allowed_users
    assert "ou_bob" in app.security.allowed_users
    assert "oc_test_group" in app.security.allowed_chats


def test_app_opencode_client_configured(app):
    assert app.opencode.base_url == "http://127.0.0.1:4096"
    assert app.opencode.username == "opencode"
    assert app.opencode.password == "test-pass"


def test_app_router_has_all_commands(app):
    commands = app.router.list_commands()
    expected = {"agents", "help", "list", "send", "status", "switch_agent"}
    assert expected.issubset(set(commands))


# ===== _handle_message 测试 =====


async def test_handle_message_p2p_allowed(app):
    ctx = _build_mock_ctx(user_id="ou_alice", text="/list")
    app.bot.reply_text = AsyncMock()

    with patch.object(app.router, "handle_text", new=AsyncMock(return_value="📋 sessions")):
        await app._handle_message(ctx)

    app.bot.reply_text.assert_called_once()
    args = app.bot.reply_text.call_args.args
    assert args[0] == ctx
    assert "📋" in args[1]


async def test_handle_message_rejected_user(app):
    ctx = _build_mock_ctx(user_id="ou_hacker", text="/list")
    app.bot.reply_text = AsyncMock()

    await app._handle_message(ctx)

    app.bot.reply_text.assert_not_called()


async def test_handle_message_group_no_at_ignored(app):
    ctx = _build_mock_ctx(
        user_id="ou_alice", chat_type="group", text="/list", is_at_bot=False
    )
    app.bot.reply_text = AsyncMock()

    await app._handle_message(ctx)

    app.bot.reply_text.assert_not_called()


async def test_handle_message_group_at_bot_processed(app):
    ctx = _build_mock_ctx(
        user_id="ou_alice", chat_type="group", text="/list", is_at_bot=True
    )
    app.bot.reply_text = AsyncMock()

    with patch.object(app.router, "handle_text", new=AsyncMock(return_value="📋 sessions")):
        await app._handle_message(ctx)

    app.bot.reply_text.assert_called_once()


async def test_handle_message_non_text(app):
    ctx = _build_mock_ctx(message_type="image", text="")
    app.bot.reply_text = AsyncMock()

    await app._handle_message(ctx)

    app.bot.reply_text.assert_called_once()
    args = app.bot.reply_text.call_args.args
    assert "不支持" in args[1]


async def test_handle_message_non_command(app):
    ctx = _build_mock_ctx(user_id="ou_alice", text="hello world")
    app.bot.reply_text = AsyncMock()

    with patch.object(app.router, "handle_text", new=AsyncMock(return_value=None)):
        await app._handle_message(ctx)

    app.bot.reply_text.assert_called_once()
    args = app.bot.reply_text.call_args.args
    assert "/help" in args[1]


async def test_handle_message_empty_text(app):
    ctx = _build_mock_ctx(user_id="ou_alice", text="")
    app.bot.reply_text = AsyncMock()

    await app._handle_message(ctx)

    app.bot.reply_text.assert_not_called()


async def test_handle_message_exception_handled(app):
    ctx = _build_mock_ctx(user_id="ou_alice", text="/list")
    app.bot.reply_text = AsyncMock()

    with patch.object(
        app.router, "handle_text", new=AsyncMock(side_effect=RuntimeError("test error"))
    ):
        await app._handle_message(ctx)

    assert app.bot.reply_text.call_count >= 1
    last_args = app.bot.reply_text.call_args.args
    assert "❌" in last_args[1]


# ===== _handle_card_action 测试 =====


async def test_handle_card_action_valid(app):
    ctx = _build_mock_card_ctx(value={"action": "list_sessions"})
    with patch.object(app.router, "handle_text", new=AsyncMock(return_value="📋 sessions")) as mock_handle:
        await app._handle_card_action(ctx)

    mock_handle.assert_called_once_with("/list")


async def test_handle_card_action_invalid_action_type(app):
    ctx = _build_mock_card_ctx(value={"action": "foobar"})
    with patch.object(app.router, "handle_text", new=AsyncMock()) as mock_handle:
        await app._handle_card_action(ctx)

    mock_handle.assert_not_called()


async def test_handle_card_action_empty_value(app):
    ctx = _build_mock_card_ctx(value={})
    with patch.object(app.router, "handle_text", new=AsyncMock()) as mock_handle:
        await app._handle_card_action(ctx)

    mock_handle.assert_not_called()


async def test_handle_card_action_rejected_operator(app):
    ctx = _build_mock_card_ctx(
        value={"action": "list_sessions"}, operator_open_id="ou_hacker"
    )
    with patch.object(app.router, "handle_text", new=AsyncMock()) as mock_handle:
        await app._handle_card_action(ctx)

    mock_handle.assert_not_called()


async def test_handle_card_action_with_chat_id_sends(app):
    ctx = _build_mock_card_ctx(
        value={"action": "list_sessions", "chat_id": "oc_target"}
    )
    app.bot.send_text = AsyncMock()
    with patch.object(app.router, "handle_text", new=AsyncMock(return_value="📋 ok")):
        await app._handle_card_action(ctx)

    app.bot.send_text.assert_called_once()
    args = app.bot.send_text.call_args.args
    assert args[0] == "oc_target"


# ===== run / signal handling 测试 =====


def test_app_run_signal_handlers_registered(app):
    with patch("main.signal.signal") as mock_signal:
        with patch.object(app.bot, "start", side_effect=KeyboardInterrupt):
            app.run()

    registered_signals = [call.args[0] for call in mock_signal.call_args_list]
    assert signal.SIGINT in registered_signals
    assert signal.SIGTERM in registered_signals


def test_app_run_bot_start_called(app):
    with patch.object(app.bot, "start") as mock_start:
        app.run()

    mock_start.assert_called_once()


def test_app_run_returns_zero_on_keyboard_interrupt(app):
    with patch.object(app.bot, "start", side_effect=KeyboardInterrupt):
        result = app.run()
    assert result == 0


def test_app_run_returns_zero_on_system_exit(app):
    with patch.object(app.bot, "start", side_effect=SystemExit(0)):
        result = app.run()
    assert result == 0


def test_app_run_returns_nonzero_on_error(app):
    with patch.object(app.bot, "start", side_effect=RuntimeError("startup failed")):
        result = app.run()
    assert result == 1


# ===== main() 入口测试 =====


def test_main_with_valid_config(monkeypatch):
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        pytest.skip("config.yaml 不存在，跳过 main() 测试")

    valid_config = {
        "feishu": {"app_id": "cli_x", "app_secret": "s"},
        "opencode": {
            "base_url": "http://127.0.0.1:4096",
            "username": "opencode",
            "password": "p",
        },
        "security": {"allowed_users": ["ou_x"]},
    }
    with patch("main.load_config", return_value=valid_config):
        with patch("main.BotApp.run", return_value=0):
            with patch("main.BotApp.__init__", return_value=None):
                result = main.main()
    assert result == 0


def test_main_missing_config_returns_nonzero(monkeypatch):
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        pytest.skip("config.yaml 存在，跳过缺失配置测试")

    result = main.main()
    assert result != 0
