"""OpencodeClient 单元测试 — 使用 respx mock httpx。"""
from __future__ import annotations

import json as _json

import httpx
import pytest
import respx

from src.exceptions import (
    OpencodeAuthError,
    OpencodeClientError,
    OpencodeNotFoundError,
    OpencodeServerError,
    OpencodeTimeoutError,
)
from src.opencode_client import OpencodeClient


BASE_URL = "http://127.0.0.1:4096"


@pytest.fixture
def client():
    """每个测试用独立 client。"""
    return OpencodeClient(
        base_url=BASE_URL,
        username="opencode",
        password="test-secret",
    )


@respx.mock
async def test_init_with_auth(client: OpencodeClient):
    """验证 Basic Auth header 正确生成（通过实际请求验证）。

    httpx 0.28+ 将 tuple auth 包装为 BasicAuth 对象（无私有属性），
    通过检查实际发出的 Authorization header 验证。
    """
    import base64

    route = respx.get(f"{BASE_URL}/api/session").respond(200, json={"data": []})
    async with client:
        await client.list_sessions()
        http_client = client.client
        assert str(http_client.base_url) == "http://127.0.0.1:4096"
    assert route.called
    auth_header = route.calls.last.request.headers.get("authorization", "")
    assert auth_header.startswith("Basic ")
    decoded = base64.b64decode(auth_header[6:]).decode()
    assert decoded == "opencode:test-secret"


async def test_init_strips_trailing_slash():
    """base_url 尾斜杠被去除。"""
    client = OpencodeClient(
        base_url="http://127.0.0.1:4096/",
        username="u",
        password="p",
    )
    assert client.base_url == "http://127.0.0.1:4096"


@respx.mock
async def test_list_sessions_success(client: OpencodeClient):
    """list_sessions 成功返回 Session 列表。"""
    respx.get(f"{BASE_URL}/api/session").respond(
        200,
        json={
            "data": [
                {"id": "ses_001", "agent": "prometheus", "title": "Plan A"},
                {"id": "ses_002", "agent": "atlas", "title": "Execute B"},
            ]
        },
    )

    async with client:
        sessions = await client.list_sessions()

    assert len(sessions) == 2
    assert sessions[0]["id"] == "ses_001"
    assert sessions[0]["agent"] == "prometheus"
    assert sessions[1]["agent"] == "atlas"


@respx.mock
async def test_list_sessions_empty(client: OpencodeClient):
    """空 session 列表。"""
    respx.get(f"{BASE_URL}/api/session").respond(200, json={"data": []})

    async with client:
        sessions = await client.list_sessions()

    assert sessions == []


@respx.mock
async def test_list_sessions_legacy_format(client: OpencodeClient):
    """兼容裸数组格式（无 data 字段）。"""
    respx.get(f"{BASE_URL}/api/session").respond(
        200,
        json=[{"id": "ses_legacy"}],
    )

    async with client:
        sessions = await client.list_sessions()

    assert len(sessions) == 1
    assert sessions[0]["id"] == "ses_legacy"


@respx.mock
async def test_switch_agent_success(client: OpencodeClient):
    """switch_agent 成功（204 响应）。"""
    route = respx.post(f"{BASE_URL}/api/session/ses_001/agent").respond(204)

    async with client:
        result = await client.switch_agent("ses_001", "prometheus")

    assert route.called
    assert result is None
    received = route.calls.last.request
    body = _json.loads(received.content)
    assert body == {"agent": "prometheus"}


@respx.mock
async def test_send_message_success(client: OpencodeClient):
    """send_message 成功返回 PromptResponse。"""
    respx.post(f"{BASE_URL}/api/session/ses_001/prompt").respond(
        200,
        json={"data": {"id": "msg_001", "sessionID": "ses_001"}},
    )

    async with client:
        result = await client.send_message("ses_001", "hello world")

    assert result["id"] == "msg_001"
    assert result["sessionID"] == "ses_001"


@respx.mock
async def test_auth_failure(client: OpencodeClient):
    """401 抛出 OpencodeAuthError。"""
    respx.get(f"{BASE_URL}/api/session").respond(401, json={"error": "unauthorized"})

    with pytest.raises(OpencodeAuthError, match="认证失败"):
        async with client:
            await client.list_sessions()


@respx.mock
async def test_not_found(client: OpencodeClient):
    """404 抛出 OpencodeNotFoundError。"""
    respx.get(f"{BASE_URL}/api/session/ses_unknown").respond(404)

    with pytest.raises(OpencodeNotFoundError, match="资源不存在"):
        async with client:
            await client.get_session("ses_unknown")


@respx.mock
async def test_server_error(client: OpencodeClient):
    """500 抛出 OpencodeServerError。"""
    respx.get(f"{BASE_URL}/api/session").respond(500, text="Internal Server Error")

    with pytest.raises(OpencodeServerError) as exc_info:
        async with client:
            await client.list_sessions()

    assert exc_info.value.status_code == 500


@respx.mock
async def test_client_error(client: OpencodeClient):
    """403 抛出 OpencodeClientError（非 401/404）。"""
    respx.get(f"{BASE_URL}/api/session").respond(403, text="Forbidden")

    with pytest.raises(OpencodeClientError) as exc_info:
        async with client:
            await client.list_sessions()

    assert exc_info.value.status_code == 403


@respx.mock
async def test_timeout_error(client: OpencodeClient):
    """超时抛出 OpencodeTimeoutError。"""
    respx.get(f"{BASE_URL}/api/session").mock(side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(OpencodeTimeoutError, match="请求超时"):
        async with client:
            await client.list_sessions()


@respx.mock
async def test_get_messages(client: OpencodeClient):
    """get_messages 返回消息列表。"""
    respx.get(f"{BASE_URL}/api/session/ses_001/message").respond(
        200,
        json={
            "data": [
                {"id": "msg_1", "role": "user", "content": "hi"},
                {"id": "msg_2", "role": "assistant", "content": "hello"},
            ]
        },
    )

    async with client:
        messages = await client.get_messages("ses_001")

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["content"] == "hello"


@respx.mock
async def test_list_agents(client: OpencodeClient):
    """list_agents 返回 agent 列表。"""
    respx.get(f"{BASE_URL}/api/agent").respond(
        200,
        json={
            "data": [
                {"id": "prometheus", "name": "Plan Builder", "description": "..."},
                {"id": "atlas", "name": "Plan Executor"},
            ]
        },
    )

    async with client:
        agents = await client.list_agents()

    assert len(agents) == 2
    assert agents[0]["id"] == "prometheus"
    assert agents[1]["id"] == "atlas"
