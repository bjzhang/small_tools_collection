"""集成测试 — 真实 HTTP + 端到端命令流 + 异步上下文管理器清理.

分层设计
--------

本文件包含三类集成测试，按对运行环境的依赖程度递增：

1. **always-on（始终运行）**：用 conftest 的 mock fixtures 串起
   SecurityGuard → CommandRouter → OpencodeClient(mock) → FeishuBot(mock)，
   验证组件接线和数据流。无需任何外部服务，每个 PR 都跑。

2. **serve-gated（仅当 opencode serve 运行时才跑）**：通过真实 HTTP 调用
   OpencodeClient，覆盖 list_sessions / list_agents / 鉴权失败 / 404 等路径。
   检测到本机 opencode serve 未监听则整组 skip（不 fail）。

3. **async-lifecycle（始终运行）**：验证 ``async with OpencodeClient(...)``
   的连接池生命周期（__aenter__/__aexit__/close/复用），用 respx 拦截请求，
   不依赖真实 opencode。

开启真实集成的环境变量
----------------------

- ``OPENCODE_TEST_URL``：opencode serve 地址，默认 ``http://127.0.0.1:4096``
- ``OPENCODE_TEST_USER``：Basic Auth 用户名，默认 ``opencode``
- ``OPENCODE_TEST_PASS``：Basic Auth 密码，默认 ``test-secret``

不设置时，serve-gated 测试会被跳过（端口探测失败）。
"""
from __future__ import annotations

import os
import socket
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx

from main import BotApp
from src.commands import CommandRouter
from src.exceptions import OpencodeAuthError, OpencodeNotFoundError
from src.opencode_client import OpencodeClient


OPENCODE_URL = os.environ.get("OPENCODE_TEST_URL", "http://127.0.0.1:4096")
OPENCODE_USER = os.environ.get("OPENCODE_TEST_USER", "opencode")
OPENCODE_PASS = os.environ.get("OPENCODE_TEST_PASS", "test-secret")  # noqa: S105


def _probe_serve(
    url: str,
    username: str,
    password: str,
    timeout: float = 1.0,
) -> bool:
    """综合探测：TCP 端口可达 + 凭据可通过 Basic Auth.

    任意一项失败都返回 False（测试组整体 skip）：
    - TCP 不通 → opencode serve 未启动
    - TCP 通但 GET /api/session 返回 401 → 凭据不匹配，
      真实测试无法进行，应 skip 而非 fail（避免污染默认 pytest 运行）

    使用同步 httpx.Client（模块导入阶段无事件循环），快速失败。
    """
    try:
        parsed = httpx.URL(url)
    except Exception:
        return False
    host = parsed.host
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=0.5):
            pass
    except OSError:
        return False

    # TCP 通了，再验凭据：401 说明 serve 在跑但 OPENCODE_TEST_PASS 未配置/错误
    try:
        with httpx.Client(
            base_url=url,
            auth=(username, password),
            timeout=timeout,
        ) as http_client:
            resp = http_client.get("/api/session")
    except httpx.HTTPError:
        return False
    if resp.status_code == 401:
        return False
    # 200 / 404 / 其他都算"serve 可达且凭据有效"——具体路径由各测试自行验证
    return True


SERVE_AVAILABLE = _probe_serve(OPENCODE_URL, OPENCODE_USER, OPENCODE_PASS)

skip_if_no_serve = pytest.mark.skipif(
    not SERVE_AVAILABLE,
    reason=f"opencode serve 未运行于 {OPENCODE_URL}（设置 OPENCODE_TEST_URL 等环境变量以启用）",
)


def _make_real_client() -> OpencodeClient:
    """构造真实 OpencodeClient（指向 OPENCODE_URL）。"""
    return OpencodeClient(
        base_url=OPENCODE_URL,
        username=OPENCODE_USER,
        password=OPENCODE_PASS,
    )


@pytest.fixture
async def real_opencode_client():
    """真实 OpencodeClient，生命周期托管（进入/退出 async with）.

    使用方式：``async with real_opencode_client: ...``
    或直接调用 ``await real_opencode_client.list_sessions()`` ——
    fixture 已通过 ``__aenter__`` 初始化底层 httpx 连接池。
    """
    client = _make_real_client()
    await client.__aenter__()
    try:
        yield client
    finally:
        await client.close()


def _build_message_ctx(
    user_id: str = "ou_alice",
    chat_type: str = "p2p",
    text: str = "/list",
    is_at_bot: bool = False,
    message_type: str = "text",
) -> MagicMock:
    """构造一个最小可用的 MessageContext 替身（用于 BotApp._handle_message）。"""
    ctx = MagicMock(name="message_ctx")
    ctx.user_id = user_id
    ctx.chat_type = chat_type
    ctx.text = text
    ctx.is_at_bot = is_at_bot
    ctx.message_type = message_type
    ctx.message_id = "om_integration_001"
    ctx.chat_id = "oc_integration_chat"
    return ctx


# ============================================================================
# 组 1：端到端命令流（始终运行，依赖 conftest 的 mock fixtures）
# ============================================================================
# 这一组验证 SecurityGuard → CommandRouter → OpencodeClient → FeishuBot 的接线，
# 是真实 opencode 不可用时的"保底"集成覆盖。与单元测试的差别：同时启动多个真实
# 组件（CommandParser/CommandRouter/SecurityGuard/BotApp），仅在边界处打桩。


async def test_e2e_list_command_wiring(
    mock_opencode_client: MagicMock,
    mock_feishu_client: MagicMock,
):
    """端到端验证 ``/list`` 命令的完整数据流（mock opencode）。

    覆盖链路：
        CommandParser.parse("/list")
        → CommandRouter.dispatch
        → OpencodeClient.list_sessions（mock）
        → 格式化文本

    断言：
    - 返回值是字符串且包含 ``📋`` 前缀
    - opencode 的 ``list_sessions`` 被调用恰好一次（路由确实分发到了客户端）
    """
    router = CommandRouter(mock_opencode_client)
    response = await router.handle_text("/list")

    assert isinstance(response, str)
    assert "📋" in response
    mock_opencode_client.list_sessions.assert_awaited_once()


async def test_e2e_agents_command_wiring(
    mock_opencode_client: MagicMock,
):
    """端到端验证 ``/agents`` 命令调用 opencode.list_agents 并返回文本。"""
    router = CommandRouter(mock_opencode_client)
    response = await router.handle_text("/agents")

    assert isinstance(response, str)
    mock_opencode_client.list_agents.assert_awaited_once()


async def test_e2e_status_command_wiring(
    mock_opencode_client: MagicMock,
):
    """端到端验证 ``/status <id>`` 命令调用 opencode.get_session。"""
    router = CommandRouter(mock_opencode_client)
    response = await router.handle_text("/status ses_mock_001")

    assert isinstance(response, str)
    mock_opencode_client.get_session.assert_awaited_once_with("ses_mock_001")


async def test_e2e_switch_agent_command_wiring(
    mock_opencode_client: MagicMock,
):
    """端到端验证 ``/switch_agent <id> <agent>`` 调用 opencode.switch_agent.

    覆盖 list_agents 的数据结构需包含 ``id`` 字段（handler 据此校验 agent 合法性）。
    """
    # handler 用 a.get("id") 校验，conftest 默认 mock 只有 "name" 字段 → 覆盖之
    mock_opencode_client.list_agents = AsyncMock(return_value=[
        {"id": "prometheus", "name": "Prometheus", "description": "Planner"},
        {"id": "atlas", "name": "Atlas", "description": "Executor"},
    ])
    router = CommandRouter(mock_opencode_client)
    response = await router.handle_text(
        "/switch_agent ses_mock_001 prometheus"
    )

    assert isinstance(response, str)
    assert "✅" in response, f"switch 应成功，实际响应：{response}"
    mock_opencode_client.switch_agent.assert_awaited_once_with(
        "ses_mock_001", "prometheus"
    )


async def test_e2e_switch_agent_rejects_unknown_agent(
    mock_opencode_client: MagicMock,
):
    """``/switch_agent`` 对不在可用列表中的 agent 名应拒绝（安全约束）.

    handler 必须先 list_agents 校验，不允许任意字符串传给 switch_agent。
    """
    mock_opencode_client.list_agents = AsyncMock(return_value=[
        {"id": "prometheus", "name": "Prometheus"},
    ])
    router = CommandRouter(mock_opencode_client)
    response = await router.handle_text(
        "/switch_agent ses_mock_001 malicious_agent"
    )

    assert "❌" in response
    mock_opencode_client.switch_agent.assert_not_awaited()


async def test_e2e_help_command_no_opencode_call(
    mock_opencode_client: MagicMock,
):
    """``/help`` 命令不应触发任何 opencode API 调用（纯本地文本）。"""
    router = CommandRouter(mock_opencode_client)
    response = await router.handle_text("/help")

    assert isinstance(response, str)
    assert "help" in response.lower() or "/" in response
    # 没有任何 opencode 方法被调用
    mock_opencode_client.list_sessions.assert_not_awaited()
    mock_opencode_client.list_agents.assert_not_awaited()


async def test_e2e_unknown_command_fallback(
    mock_opencode_client: MagicMock,
):
    """未注册的命令返回提示文本，不抛异常。"""
    router = CommandRouter(mock_opencode_client)
    response = await router.handle_text("/nonexistent_cmd")

    assert isinstance(response, str)
    assert len(response) > 0


async def test_e2e_botapp_message_to_reply(
    mock_security: MagicMock,
    mock_opencode_client: MagicMock,
    mock_feishu_client: MagicMock,
    sample_config: dict,
):
    """端到端：BotApp._handle_message 全链路（mock opencode + mock bot）。

    覆盖：
        入站消息（白名单用户 ou_alice，文本 ``/list``）
        → SecurityGuard.is_user_allowed（通过）
        → CommandRouter.handle_text
        → OpencodeClient.list_sessions（mock）
        → FeishuBot.reply_text（mock）

    断言：
    - ``reply_text`` 被调用恰好一次
    - 第二个参数（响应文本）包含 ``📋``（来自 /list 命令的格式化输出）
    """
    app = BotApp(sample_config)
    # 用 mock 替换真实依赖（避免触发真实飞书/opencode）
    app.security = mock_security
    app.opencode = mock_opencode_client
    app.router = CommandRouter(mock_opencode_client)
    app.bot = mock_feishu_client

    ctx = _build_message_ctx(user_id="ou_alice", text="/list")
    await app._handle_message(ctx)

    mock_feishu_client.reply_text.assert_awaited_once()
    args = mock_feishu_client.reply_text.call_args.args
    assert args[0] is ctx
    assert "📋" in args[1]


async def test_e2e_botapp_rejected_user_no_reply(
    mock_security: MagicMock,
    mock_feishu_client: MagicMock,
    sample_config: dict,
):
    """非白名单用户的消息被 SecurityGuard 拦截，不触发任何回复。

    通过覆盖 ``mock_security.is_user_allowed`` 返回 False 模拟拒绝。
    """
    mock_security.is_user_allowed.return_value = False

    app = BotApp(sample_config)
    app.security = mock_security
    app.bot = mock_feishu_client

    ctx = _build_message_ctx(user_id="ou_hacker", text="/list")
    await app._handle_message(ctx)

    mock_feishu_client.reply_text.assert_not_awaited()
    # 显式还原，避免污染同 fixture 的其他测试
    mock_security.is_user_allowed.return_value = True


async def test_e2e_botapp_non_command_replies_with_help_hint(
    mock_security: MagicMock,
    mock_opencode_client: MagicMock,
    mock_feishu_client: MagicMock,
    sample_config: dict,
):
    """非命令文本（不以 / 开头）会被 BotApp 兜底为帮助提示。"""
    app = BotApp(sample_config)
    app.security = mock_security
    app.opencode = mock_opencode_client
    app.router = CommandRouter(mock_opencode_client)
    app.bot = mock_feishu_client

    ctx = _build_message_ctx(user_id="ou_alice", text="hello there")
    await app._handle_message(ctx)

    mock_feishu_client.reply_text.assert_awaited_once()
    reply_text: str = mock_feishu_client.reply_text.call_args.args[1]
    assert "/help" in reply_text


async def test_e2e_opencode_failure_surfaces_in_command_response(
    mock_opencode_client: MagicMock,
):
    """opencode 调用抛异常时，CommandRouter.dispatch 应捕获并返回错误文本.

    验证错误隔离：单条命令失败不会冒泡到 BotApp 顶层异常处理。
    """
    mock_opencode_client.list_sessions = AsyncMock(
        side_effect=RuntimeError("simulated opencode outage")
    )
    router = CommandRouter(mock_opencode_client)

    response = await router.handle_text("/list")

    assert isinstance(response, str)
    assert "❌" in response or "失败" in response


# ============================================================================
# 组 2：真实 opencode serve HTTP 集成（serve 未运行则整组 skip）
# ============================================================================


@skip_if_no_serve
async def test_real_list_sessions_returns_list(
    real_opencode_client: OpencodeClient,
):
    """``GET /api/session`` 真实调用应返回 list[dict]。

    通过真实 HTTP 验证：
    - Basic Auth 配置正确（否则会抛 OpencodeAuthError）
    - 响应解析为 list
    """
    sessions = await real_opencode_client.list_sessions()
    assert isinstance(sessions, list)
    # 每条 session 至少应有 id 字段（约定）
    for s in sessions:
        assert isinstance(s, dict)
        assert "id" in s


@skip_if_no_serve
async def test_real_list_agents_returns_list(
    real_opencode_client: OpencodeClient,
):
    """``GET /api/agent`` 真实调用应返回 agent 列表。"""
    agents = await real_opencode_client.list_agents()
    assert isinstance(agents, list)
    for a in agents:
        assert isinstance(a, dict)


@skip_if_no_serve
async def test_real_get_session_not_found():
    """请求不存在的 session_id 应抛 OpencodeNotFoundError.

    使用未占用的随机 id（ses_does_not_exist_xxx），依赖 opencode serve 的 404 路径。
    """
    client = _make_real_client()
    async with client:
        with pytest.raises(OpencodeNotFoundError):
            await client.get_session("ses_does_not_exist_integration_test")


@skip_if_no_serve
async def test_real_auth_failure_raises_auth_error():
    """错误的密码应触发 OpencodeAuthError（401）。"""
    client = OpencodeClient(
        base_url=OPENCODE_URL,
        username=OPENCODE_USER,
        password="definitely-wrong-password",  # noqa: S106 - 故意错误
    )
    async with client:
        with pytest.raises(OpencodeAuthError):
            await client.list_sessions()


@skip_if_no_serve
async def test_real_e2e_list_through_router(
    real_opencode_client: OpencodeClient,
):
    """端到端：CommandRouter + 真实 opencode + ``/list``.

    与 ``test_e2e_list_command_wiring``（mock 版本）互补：这里验证真实响应
    能被 CommandRouter._handle_list 正确格式化。
    """
    router = CommandRouter(real_opencode_client)
    response = await router.handle_text("/list")

    assert isinstance(response, str)
    # 命令成功时不包含 ❌；失败时（如 opencode 抛错）会包含 ❌
    # 我们只断言返回值类型与基本格式，不强制 sessions 是否为空
    assert len(response) > 0


@skip_if_no_serve
async def test_real_e2e_agents_through_router(
    real_opencode_client: OpencodeClient,
):
    """端到端：CommandRouter + 真实 opencode + ``/agents``."""
    router = CommandRouter(real_opencode_client)
    response = await router.handle_text("/agents")

    assert isinstance(response, str)
    assert len(response) > 0


# ============================================================================
# 组 3：异步上下文管理器生命周期（始终运行，用 respx 拦截）
# ============================================================================


@respx.mock
async def test_async_context_manager_initializes_and_closes_pool():
    """``async with OpencodeClient`` 应在进入时建池、退出时关池.

    用 respx 拦截请求，避免依赖真实 serve。
    """
    respx.get(f"{OPENCODE_URL}/api/session").respond(200, json={"data": []})
    client = OpencodeClient(
        base_url=OPENCODE_URL,
        username=OPENCODE_USER,
        password=OPENCODE_PASS,
    )

    # 进入前：连接池未创建
    assert client._client is None

    async with client:
        # 进入后：连接池已惰性初始化
        assert client._client is not None
        await client.list_sessions()

    # 退出后：连接池已关闭并清空
    assert client._client is None


@respx.mock
async def test_async_context_manager_exit_releases_even_on_exception():
    """``__aexit__`` 在块内抛异常时仍应关闭连接池.

    防止异常路径下资源泄漏。
    """
    respx.get(f"{OPENCODE_URL}/api/session").respond(500, text="boom")
    client = OpencodeClient(
        base_url=OPENCODE_URL,
        username=OPENCODE_USER,
        password=OPENCODE_PASS,
    )

    with pytest.raises(Exception):  # OpencodeServerError
        async with client:
            assert client._client is not None
            await client.list_sessions()

    # 即使块内抛异常，连接池也应被关闭
    assert client._client is None


@respx.mock
async def test_client_can_be_reentered_after_close():
    """客户端 close 后允许重新进入新的 async with（新连接池）.

    覆盖"短生命周期客户端被复用"的场景。
    """
    route = respx.get(f"{OPENCODE_URL}/api/session").respond(
        200, json={"data": []}
    )
    client = OpencodeClient(
        base_url=OPENCODE_URL,
        username=OPENCODE_USER,
        password=OPENCODE_PASS,
    )

    async with client:
        await client.list_sessions()
    assert client._client is None

    async with client:
        await client.list_sessions()
    assert client._client is None

    assert route.call_count == 2


@respx.mock
async def test_close_is_idempotent():
    """多次调用 ``close()`` 不应抛异常.

    保险性测试：防止重复 close 引发的 RuntimeError（aclose 已关闭的池）。
    """
    respx.get(f"{OPENCODE_URL}/api/session").respond(200, json={"data": []})
    client = OpencodeClient(
        base_url=OPENCODE_URL,
        username=OPENCODE_USER,
        password=OPENCODE_PASS,
    )

    async with client:
        await client.list_sessions()

    # 再关两次：都应该是 no-op，不抛异常
    await client.close()
    await client.close()
    assert client._client is None


async def test_close_without_enter_is_noop():
    """从未进入 async with 的客户端，直接 close 应安全无副作用.

    覆盖"构造后立刻销毁"的边界情况。
    """
    client = OpencodeClient(
        base_url=OPENCODE_URL,
        username=OPENCODE_USER,
        password=OPENCODE_PASS,
    )
    # _client 从未被访问过
    assert client._client is None
    await client.close()  # 不应抛异常
    assert client._client is None
