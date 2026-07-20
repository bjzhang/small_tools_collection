"""飞书 Bot 核心客户端（lark-oapi WebSocket 长连接）。

提供：
- FeishuBot：WebSocket 长连接入口
  - 接收消息事件（P2ImMessageReceiveV1）
  - 接收卡片回调（P2CardActionTrigger）
  - 发送文本消息（reply_text / send_text）
  - 发送交互式卡片（reply_card / send_card）
  - @bot 检测（群消息中识别机器人被提及）

依赖：
- lark-oapi >= 1.0.0（实际验证版本 1.7.1）

事件流：
  飞书 → WebSocket → EventDispatcher → sync handler → 后台 event loop → 用户 async callback

lark-oapi 1.7.x 关键 API（经源码内省验证，与早期版本/占位框架有差异）：
- 事件注册：``EventDispatcherHandler.builder("","").register_p2_im_message_receive_v1(fn).build()``
  （**不是** p1，方法名是 ``register_p2_im_message_receive_v1``）
- handler 签名：**单参数** ``fn(event: P2ImMessageReceiveV1) -> None``
  （**不是** ``(ctx, event)`` 双参数）
- 卡片回调：**同一个** EventDispatcherHandler 上 ``register_p2_card_action_trigger(fn)``
  （**不是** 独立的 ``lark.CardActionHandler``；``lark.ws.Client`` 构造器只接收 ``event_handler``）
- WebSocket：``lark.ws.Client(app_id, app_secret, event_handler=..., log_level=..., auto_reconnect=True)``
  → ``.start()`` 阻塞调用

使用：
    bot = FeishuBot(app_id=..., app_secret=...)
    bot.on_message = my_message_handler   # async (ctx: MessageContext) -> None
    bot.on_card_action = my_card_handler  # async (action: CardActionContext) -> None
    bot.start()                           # 阻塞，启动 WebSocket 长连接
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Awaitable, Callable, Optional

import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    P2ImMessageReceiveV1,
)

logger = logging.getLogger(__name__)

MessageHandler = Callable[["MessageContext"], Awaitable[None]]
CardActionHandler = Callable[["CardActionContext"], Awaitable[None]]


class MessageContext:
    """消息事件上下文（封装 P2ImMessageReceiveV1，便于使用）。

    Attributes:
        raw: 原始 lark-oapi 事件对象（P2ImMessageReceiveV1）
        message_id: 消息 ID（om_xxx）
        chat_id: 会话 ID（oc_xxx）
        chat_type: "p2p"（单聊）或 "group"（群聊）
        message_type: "text" / "post" / "image" 等
        content: 消息内容（JSON 字符串）
        text: 纯文本内容（仅 message_type=text 时有效，已剥离 @bot 前缀）
        user_id: 发送者 open_id（ou_xxx）
        sender_open_id: 发送者 open_id（同 user_id，显式别名）
        is_at_bot: 是否 @ 了机器人（仅群聊有意义）
    """

    def __init__(
        self,
        event: P2ImMessageReceiveV1,
        bot_open_id: Optional[str] = None,
    ) -> None:
        self.raw = event
        msg = event.event.message
        sender = event.event.sender

        self.message_id: str = msg.message_id or ""
        self.chat_id: str = msg.chat_id or ""
        self.chat_type: str = msg.chat_type or "p2p"
        self.message_type: str = msg.message_type or ""
        self.content: str = msg.content or ""

        self.sender_open_id: str = (sender.sender_id.open_id
                                    if sender and sender.sender_id else "")
        self.user_id: str = self.sender_open_id

        self.text: str = ""
        self.is_at_bot: bool = False
        if self.message_type == "text":
            try:
                content_dict = json.loads(self.content) if self.content else {}
                self.text = content_dict.get("text", "") or ""
            except (ValueError, TypeError):
                self.text = ""

        mentions = msg.mentions or []
        if self.chat_type == "group" and mentions:
            at_keys: list[str] = []
            for mention in mentions:
                m_key = getattr(mention, "key", None) or ""
                m_id_obj = getattr(mention, "id", None)
                m_open_id = getattr(m_id_obj, "open_id", None) if m_id_obj else None
                is_bot = False
                if bot_open_id and m_open_id == bot_open_id:
                    is_bot = True
                elif m_key and m_key.startswith("@_user_"):
                    if bot_open_id is None:
                        is_bot = True
                if is_bot:
                    self.is_at_bot = True
                    if m_key:
                        at_keys.append(m_key)

            for key in at_keys:
                self.text = self.text.replace(key, "")
            self.text = self.text.strip()


class CardActionContext:
    """卡片回调事件上下文（封装 P2CardActionTrigger，便于使用）。

    Attributes:
        raw: 原始 lark-oapi 事件对象（P2CardActionTrigger）
        value: 按钮携带的 value 字典（来自 action.value）
        tag: action.tag（如 button）
        operator_open_id: 触发者的 open_id
    """

    def __init__(self, event: Any) -> None:
        self.raw = event
        data = getattr(event, "event", None)
        action = getattr(data, "action", None) if data else None
        operator = getattr(data, "operator", None) if data else None

        value = getattr(action, "value", None) if action else None
        self.value: dict = value if isinstance(value, dict) else {}
        self.tag: str = getattr(action, "tag", "") if action else ""
        self.operator_open_id: str = (getattr(operator, "open_id", "")
                                      if operator else "")
        self.user_id: str = self.operator_open_id


class FeishuBot:
    """飞书 Bot 客户端（WebSocket 长连接模式）。

    使用 lark-oapi 的 WebSocket 长连接，无需公网回调 URL，适合本地开发。

    Usage:
        bot = FeishuBot(app_id="cli_xxx", app_secret="xxx")

        async def on_msg(ctx: MessageContext):
            await bot.reply_text(ctx, "收到")

        async def on_card(ctx: CardActionContext):
            logger.info("按钮点击：%s", ctx.value)

        bot.on_message = on_msg
        bot.on_card_action = on_card
        bot.start()  # 阻塞调用
    """

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        bot_open_id: Optional[str] = None,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.bot_open_id = bot_open_id

        self.on_message: Optional[MessageHandler] = None
        self.on_card_action: Optional[CardActionHandler] = None

        self._lark_client: Optional[lark.Client] = None
        self._ws_client: Optional[Any] = None

        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._loop_started = threading.Event()

    # ===== 内部：后台 event loop =====

    def _ensure_event_loop(self) -> asyncio.AbstractEventLoop:
        """启动后台 event loop（守护线程），用于调度 async 用户回调。

        lark-oapi 的 ws.Client.start() 是同步阻塞调用，事件 handler 在 SDK
        工作线程中被同步调用。我们在后台线程跑一个 event loop，通过
        run_coroutine_threadsafe 把 async 回调投递过去执行。
        """
        if self._event_loop is not None and self._event_loop.is_running():
            self._loop_started.wait(timeout=2.0)
            return self._event_loop

        def _run_loop() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._event_loop = loop
            self._loop_started.set()
            loop.run_forever()

        self._loop_thread = threading.Thread(
            target=_run_loop, name="feishu-bot-loop", daemon=True
        )
        self._loop_thread.start()
        self._loop_started.wait(timeout=2.0)
        return self._event_loop  # type: ignore[return-value]

    # ===== lark REST client =====

    @property
    def lark_client(self) -> lark.Client:
        """惰性初始化 lark REST client（用于主动发消息）。"""
        if self._lark_client is None:
            self._lark_client = (
                lark.Client.builder()
                .app_id(self.app_id)
                .app_secret(self.app_secret)
                .log_level(lark.LogLevel.INFO)
                .build()
            )
        return self._lark_client

    # ===== 事件分发器构建 =====

    def _build_event_dispatcher(self) -> lark.EventDispatcherHandler:
        """构建事件 dispatcher（注册消息接收 + 卡片回调 handler）。

        lark-oapi 1.7.x：encrypt_key / verification_token 在 WebSocket 长连接
        模式下可为空字符串（飞书服务端已通过长连接鉴权）。
        """
        bot = self  # 闭包捕获

        def message_receive_handler(event: P2ImMessageReceiveV1) -> None:
            try:
                ctx = MessageContext(event, bot_open_id=bot.bot_open_id)
                logger.info(
                    "收到消息 [%s/%s] from %s: %s",
                    ctx.chat_type,
                    ctx.message_type,
                    ctx.user_id,
                    ctx.text[:100] if ctx.text else "(non-text)",
                )
                if bot.on_message is None:
                    logger.warning("on_message 未设置，丢弃消息")
                    return
                loop = bot._ensure_event_loop()
                asyncio.run_coroutine_threadsafe(bot.on_message(ctx), loop)
            except Exception as e:  # noqa: BLE001
                logger.exception("消息处理异常：%s", e)

        def card_action_handler(event: Any) -> None:
            try:
                ctx = CardActionContext(event)
                logger.info(
                    "收到卡片回调 tag=%s operator=%s value=%s",
                    ctx.tag, ctx.operator_open_id, ctx.value,
                )
                if bot.on_card_action is None:
                    logger.warning("on_card_action 未设置，丢弃回调")
                    return None
                loop = bot._ensure_event_loop()
                asyncio.run_coroutine_threadsafe(
                    bot.on_card_action(ctx), loop
                )
                return None
            except Exception as e:  # noqa: BLE001
                logger.exception("卡片回调异常：%s", e)
                return None

        dispatcher = (
            lark.EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(message_receive_handler)
            .register_p2_card_action_trigger(card_action_handler)
            .build()
        )
        return dispatcher

    # ===== 启动 / 停止 =====

    def start(self) -> None:
        """启动 WebSocket 长连接（阻塞调用）。

        内部：
        1. 启动后台 event loop（调度 async 用户回调）
        2. 构建事件 dispatcher
        3. 创建 lark.ws.Client 并启动（内置断线重连）
        """
        logger.info("启动 FeishuBot（WebSocket 长连接）... app_id=%s", self.app_id)
        self._ensure_event_loop()

        event_handler = self._build_event_dispatcher()

        self._ws_client = lark.ws.Client(
            self.app_id,
            self.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO,
            auto_reconnect=True,
        )
        logger.info("WebSocket 连接中...")
        self._ws_client.start()
        logger.warning("WebSocket 已断开")

    async def start_async(self) -> None:
        """async 版本启动：在 executor 线程中跑阻塞的 start()。"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.start)

    def stop(self) -> None:
        """停止 WebSocket 连接（关闭后台 event loop）。"""
        if self._event_loop is not None and self._event_loop.is_running():
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        logger.info("FeishuBot 已停止")

    # ===== 消息发送 API =====

    async def reply_text(self, ctx: MessageContext, text: str) -> dict:
        """回复消息（发到原会话）。

        Args:
            ctx: 消息上下文
            text: 回复文本

        Returns:
            ``{"success": bool, "message_id": str, ...}``
        """
        return await self.send_message(
            receive_id=ctx.chat_id,
            msg_type="text",
            content=json.dumps({"text": text}, ensure_ascii=False),
        )

    async def send_text(self, chat_id: str, text: str) -> dict:
        """主动发送文本消息。

        Args:
            chat_id: 目标会话 ID（oc_xxx）
            text: 文本内容
        """
        return await self.send_message(
            receive_id=chat_id,
            msg_type="text",
            content=json.dumps({"text": text}, ensure_ascii=False),
        )

    async def reply_card(self, ctx: MessageContext, card: dict) -> dict:
        """回复交互式卡片（发到原会话）。

        Args:
            ctx: 消息上下文
            card: 飞书卡片 JSON（build_session_list_card 等输出）
        """
        return await self.send_message(
            receive_id=ctx.chat_id,
            msg_type="interactive",
            content=json.dumps(card, ensure_ascii=False),
        )

    async def send_card(self, chat_id: str, card: dict) -> dict:
        """主动发送交互式卡片。"""
        return await self.send_message(
            receive_id=chat_id,
            msg_type="interactive",
            content=json.dumps(card, ensure_ascii=False),
        )

    async def send_message(
        self,
        receive_id: str,
        msg_type: str,
        content: str,
        receive_id_type: str = "chat_id",
    ) -> dict:
        """通用发消息（底层 API，封装同步 lark-oapi 为 async）。

        Args:
            receive_id: 接收者 ID
            msg_type: text / post / image / interactive / etc.
            content: 消息内容 JSON 字符串
            receive_id_type: chat_id / open_id / user_id（默认 chat_id）

        Returns:
            成功：``{"success": True, "message_id": "om_xxx"}``
            失败：``{"success": False, "code": int, "msg": str}``
        """

        def _do_send() -> dict:
            request = (
                CreateMessageRequest.builder()
                .receive_id_type(receive_id_type)
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type(msg_type)
                    .content(content)
                    .build()
                )
                .build()
            )
            response = self.lark_client.im.v1.message.create(request)
            if not response.success():
                logger.error(
                    "发送消息失败：code=%s msg=%s",
                    response.code, response.msg,
                )
                return {
                    "success": False,
                    "code": response.code,
                    "msg": response.msg,
                }
            return {
                "success": True,
                "message_id": response.data.message_id,
            }

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = self._ensure_event_loop()
        return await loop.run_in_executor(None, _do_send)
