"""共享 pytest fixtures（跨所有 test_*.py 可用）.

本文件提供通用 mock 对象与样例数据，避免各测试模块重复构造。
设计原则：
- 所有 mock 仅模拟接口契约，不触碰真实凭据/网络
- 命名加 `mock_`/`sample_` 前缀，避免与 test_main.py/test_security.py 等已有的
  本地 fixture（如 `app`/`guard`/`client`/`app_config`）冲突
- 异步方法用 AsyncMock，同步方法用 MagicMock，保持调用断言可用
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


# ===== Mock 客户端 =====


@pytest.fixture
def mock_feishu_client() -> MagicMock:
    """FeishuBot 的 mock 对象（不连接飞书 WebSocket）。

    覆盖 FeishuBot 的公开异步接口（见 src.feishu_client）：
    - reply_text(ctx, text) -> dict
    - send_text(chat_id, text) -> dict
    - reply_card(ctx, card) -> dict
    - send_card(chat_id, card) -> dict
    - send_message(...) -> dict
    - start_async() -> None

    所有方法默认返回空 dict；测试可按需重写 return_value / side_effect。

    Example::

        async def test_reply(mock_feishu_client):
            mock_feishu_client.reply_text.return_value = {"code": 0}
            ...
            mock_feishu_client.reply_text.assert_awaited_once()
    """
    bot = MagicMock(name="mock_feishu_bot")
    # 属性
    bot.app_id = "cli_test_app"
    bot.app_secret = "test_secret"  # noqa: S105 - 测试占位，非真实凭据
    bot.bot_open_id = "ou_mock_bot"
    bot.on_message = None
    bot.on_card_action = None
    # 异步方法（AsyncMock 支持 assert_awaited_*）
    bot.reply_text = AsyncMock(return_value={"code": 0, "msg": "ok"})
    bot.send_text = AsyncMock(return_value={"code": 0, "msg": "ok"})
    bot.reply_card = AsyncMock(return_value={"code": 0, "msg": "ok"})
    bot.send_card = AsyncMock(return_value={"code": 0, "msg": "ok"})
    bot.send_message = AsyncMock(return_value={"code": 0, "msg": "ok"})
    bot.start_async = AsyncMock(return_value=None)
    return bot


@pytest.fixture
def mock_opencode_client() -> MagicMock:
    """OpencodeClient 的 mock 对象（不发起 HTTP 请求）。

    覆盖 OpencodeClient 的公开异步接口（见 src.opencode_client）：
    - list_sessions() -> list[dict]
    - get_session(session_id) -> dict
    - send_message(session_id, text) -> dict
    - switch_agent(session_id, agent_name) -> None
    - list_agents() -> list[dict]
    - get_messages(session_id) -> list[dict]
    - close() -> None
    - __aenter__/__aexit__（支持 async with）

    默认返回最小化样例数据；测试可覆盖 return_value。
    """
    client = MagicMock(name="mock_opencode_client")
    # 属性
    client.base_url = "http://127.0.0.1:4096"
    client.username = "opencode"
    client.password = "test-secret"  # noqa: S105 - 测试占位
    # 异步方法
    client.list_sessions = AsyncMock(return_value=[
        {"id": "ses_mock_001", "agent": "prometheus", "title": "Mock Plan"},
        {"id": "ses_mock_002", "agent": "atlas", "title": "Mock Execute"},
    ])
    client.get_session = AsyncMock(return_value={
        "id": "ses_mock_001",
        "agent": "prometheus",
        "title": "Mock Plan",
    })
    client.send_message = AsyncMock(return_value={
        "id": "msg_mock_001",
        "sessionID": "ses_mock_001",
    })
    client.switch_agent = AsyncMock(return_value=None)
    client.list_agents = AsyncMock(return_value=[
        {"name": "prometheus", "description": "Planner"},
        {"name": "atlas", "description": "Executor"},
    ])
    client.get_messages = AsyncMock(return_value=[
        {"role": "user", "parts": [{"text": "hello"}]},
        {"role": "assistant", "parts": [{"text": "hi"}]},
    ])
    client.close = AsyncMock(return_value=None)
    # 支持 async with
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_security() -> MagicMock:
    """SecurityGuard 的 mock 对象（白名单/输入清理逻辑被替换）。

    覆盖 SecurityGuard 的公开同步接口（见 src.security）：
    - is_user_allowed(user_id) -> bool（默认 True，可按测试改写）
    - is_chat_allowed(chat_id) -> bool（默认 True）
    - sanitize_input(text) -> str（默认原样返回）
    - check_command(text) -> None（默认不抛错）

    默认宽松放行；需要测试拒绝场景时用 side_effect 或 return_value 覆盖。

    Example::

        def test_denied(mock_security):
            mock_security.is_user_allowed.return_value = False
            assert not mock_security.is_user_allowed("ou_eve")
    """
    guard = MagicMock(name="mock_security_guard")
    guard.allowed_users = {"ou_alice", "ou_bob"}
    guard.allowed_chats = {"oc_test_group"}
    guard.is_user_allowed = MagicMock(return_value=True)
    guard.is_chat_allowed = MagicMock(return_value=True)
    guard.sanitize_input = MagicMock(side_effect=lambda text: text)
    guard.check_command = MagicMock(return_value=None)
    return guard


# ===== 样例数据 =====


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """完整样例配置字典（与 config.example.yaml 结构一致，测试专用值）。

    包含 feishu / opencode / security / logging 四段。
    所有值为测试占位，非真实凭据；可作为 BotApp(config) 或 load_config 替身。
    """
    return {
        "feishu": {
            "app_id": "cli_test_app",
            "app_secret": "test_app_secret",  # noqa: S105 - 测试占位
        },
        "opencode": {
            "base_url": "http://127.0.0.1:4096",
            "username": "opencode",
            "password": "test-opencode-pass",  # noqa: S105 - 测试占位
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
def sample_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """样例环境变量（通过 monkeypatch 注入，测试结束自动还原）。

    覆盖 .env.example 中的变量名，用于验证 config.py 的 ${VAR} 替换逻辑。
    返回注入的变量字典，方便测试断言。

    Example::

        def test_env_loaded(sample_env):
            assert os.environ["FEISHU_APP_ID"] == "cli_test_app"
            assert sample_env["OPENCODE_SERVER_PASSWORD"] == "test-pass"
    """
    env: dict[str, str] = {
        "FEISHU_APP_ID": "cli_test_app",
        "FEISHU_APP_SECRET": "test_app_secret",
        "OPENCODE_BASE_URL": "http://127.0.0.1:4096",
        "OPENCODE_USERNAME": "opencode",
        "OPENCODE_SERVER_PASSWORD": "test-strong-pass",
        "FEISHU_WHITELIST_USER_IDS": "ou_alice,ou_bob",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env
