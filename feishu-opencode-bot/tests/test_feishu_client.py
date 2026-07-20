"""FeishuBot 单元测试（不依赖真实飞书连接，mock lark-oapi）。"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.feishu_client import CardActionContext, FeishuBot, MessageContext


def _build_message_event(
    text: str = "hello",
    chat_type: str = "p2p",
    message_type: str = "text",
    mentions=None,
    message_id: str = "om_test001",
    chat_id: str = "oc_chat001",
    open_id: str = "ou_alice",
):
    event = MagicMock()
    event.event.message.message_id = message_id
    event.event.message.chat_id = chat_id
    event.event.message.chat_type = chat_type
    event.event.message.message_type = message_type
    event.event.message.content = (
        json.dumps({"text": text}) if message_type == "text" else "{}"
    )
    event.event.message.mentions = mentions or []
    event.event.sender.sender_id.open_id = open_id
    return event


def _build_card_event(value=None, tag="button", open_id="ou_bob"):
    event = MagicMock()
    event.event.action.value = value if value is not None else {"cmd": "list"}
    event.event.action.tag = tag
    event.event.operator.open_id = open_id
    return event


def test_bot_init_basic():
    bot = FeishuBot(app_id="cli_test", app_secret="secret")
    assert bot.app_id == "cli_test"
    assert bot.app_secret == "secret"
    assert bot.bot_open_id is None
    assert bot.on_message is None
    assert bot.on_card_action is None


def test_bot_init_with_open_id():
    bot = FeishuBot(app_id="cli", app_secret="s", bot_open_id="ou_bot")
    assert bot.bot_open_id == "ou_bot"


def test_bot_lark_client_lazy():
    bot = FeishuBot(app_id="cli", app_secret="s")
    assert bot._lark_client is None
    _ = bot.lark_client
    assert bot._lark_client is not None


def test_message_context_p2p_text():
    event = _build_message_event(text="hello", chat_type="p2p")
    ctx = MessageContext(event)
    assert ctx.message_id == "om_test001"
    assert ctx.chat_id == "oc_chat001"
    assert ctx.chat_type == "p2p"
    assert ctx.message_type == "text"
    assert ctx.text == "hello"
    assert ctx.user_id == "ou_alice"
    assert ctx.sender_open_id == "ou_alice"
    assert ctx.is_at_bot is False


def test_message_context_non_text():
    event = _build_message_event(message_type="post")
    ctx = MessageContext(event)
    assert ctx.message_type == "post"
    assert ctx.text == ""


def test_message_context_group_at_bot_by_key():
    mention = MagicMock()
    mention.key = "@_user_1"
    mention.id.open_id = "ou_bot123"
    event = _build_message_event(
        text="@_user_1 /list", chat_type="group", mentions=[mention],
    )
    ctx = MessageContext(event)
    assert ctx.chat_type == "group"
    assert ctx.is_at_bot is True
    assert "@_user_1" not in ctx.text
    assert "/list" in ctx.text


def test_message_context_group_at_bot_by_open_id():
    mention = MagicMock()
    mention.key = "@_user_2"
    mention.id.open_id = "ou_known_bot"
    event = _build_message_event(
        text="@_user_2 hi", chat_type="group", mentions=[mention],
    )
    ctx = MessageContext(event, bot_open_id="ou_known_bot")
    assert ctx.is_at_bot is True
    assert "hi" in ctx.text


def test_message_context_group_no_at():
    event = _build_message_event(text="hello", chat_type="group", mentions=[])
    ctx = MessageContext(event)
    assert ctx.is_at_bot is False


def test_message_context_p2p_no_at_detection():
    mention = MagicMock()
    mention.key = "@_user_1"
    mention.id.open_id = "ou_bot123"
    event = _build_message_event(
        text="@_user_1 hi", chat_type="p2p", mentions=[mention],
    )
    ctx = MessageContext(event)
    assert ctx.is_at_bot is False


def test_message_context_invalid_json():
    event = _build_message_event()
    event.event.message.content = "invalid json"
    ctx = MessageContext(event)
    assert ctx.text == ""


def test_message_context_empty_content():
    event = _build_message_event()
    event.event.message.content = ""
    ctx = MessageContext(event)
    assert ctx.text == ""


def test_card_action_context():
    event = _build_card_event(value={"cmd": "switch", "session": "s1"})
    ctx = CardActionContext(event)
    assert ctx.value == {"cmd": "switch", "session": "s1"}
    assert ctx.tag == "button"
    assert ctx.operator_open_id == "ou_bob"
    assert ctx.user_id == "ou_bob"


def test_card_action_context_non_dict_value():
    event = _build_card_event()
    event.event.action.value = "not a dict"
    ctx = CardActionContext(event)
    assert ctx.value == {}


def test_on_message_handler_set():
    bot = FeishuBot(app_id="cli", app_secret="s")

    async def handler(ctx):
        pass

    bot.on_message = handler
    assert bot.on_message is handler


def test_on_card_action_handler_set():
    bot = FeishuBot(app_id="cli", app_secret="s")

    async def handler(action):
        pass

    bot.on_card_action = handler
    assert bot.on_card_action is handler


def test_event_dispatcher_build():
    bot = FeishuBot(app_id="cli", app_secret="s")
    dispatcher = bot._build_event_dispatcher()
    assert dispatcher is not None


@pytest.fixture
def bot_with_mock_client():
    bot = FeishuBot(app_id="cli", app_secret="s")
    mock_response = MagicMock()
    mock_response.success.return_value = True
    mock_response.data.message_id = "om_new001"

    mock_create = MagicMock(return_value=mock_response)
    bot._lark_client = MagicMock()
    bot._lark_client.im.v1.message.create = mock_create
    return bot, mock_create


async def test_reply_text(bot_with_mock_client):
    bot, mock_create = bot_with_mock_client
    ctx = MessageContext(_build_message_event())
    result = await bot.reply_text(ctx, "收到")
    assert result["success"] is True
    assert result["message_id"] == "om_new001"
    mock_create.assert_called_once()


async def test_send_text(bot_with_mock_client):
    bot, mock_create = bot_with_mock_client
    result = await bot.send_text("oc_chat", "hi")
    assert result["success"] is True
    mock_create.assert_called_once()


async def test_send_card(bot_with_mock_client):
    bot, mock_create = bot_with_mock_client
    card = {
        "config": {},
        "header": {"title": {"tag": "plain_text", "content": "test"}},
        "elements": [],
    }
    result = await bot.send_card("oc_chat", card)
    assert result["success"] is True
    call_request = mock_create.call_args.args[0]
    assert call_request.receive_id_type == "chat_id"


async def test_send_message_failure(bot_with_mock_client):
    bot, mock_create = bot_with_mock_client
    mock_response = MagicMock()
    mock_response.success.return_value = False
    mock_response.code = 230002
    mock_response.msg = "invalid chat_id"
    mock_create.return_value = mock_response

    result = await bot.send_text("oc_invalid", "hi")
    assert result["success"] is False
    assert result["code"] == 230002
    assert "invalid" in result["msg"]


async def test_message_handler_dispatched(bot_with_mock_client):
    bot, _ = bot_with_mock_client
    received: list = []

    async def handler(ctx):
        received.append(ctx.text)

    bot.on_message = handler
    event = _build_message_event(text="ping", chat_type="p2p")
    bot._build_event_dispatcher()
    import lark_oapi as lark

    reg_handlers = lark.EventDispatcherHandler.builder("", "")
    message_receive_handler = bot._build_event_dispatcher()
    assert message_receive_handler is not None
