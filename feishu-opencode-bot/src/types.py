"""opencode API 数据类型（TypedDict，便于 dict 字段提示）。"""
from __future__ import annotations

from typing import TypedDict


class Session(TypedDict, total=False):
    """opencode session（GET /api/session 元素）。"""
    id: str
    agent: str          # "prometheus" / "atlas" / ...
    model: str
    title: str
    createdAt: str
    updatedAt: str
    # 其他可能字段（total=False 容忍）


class Agent(TypedDict, total=False):
    """opencode agent（GET /api/agent 元素）。"""
    id: str             # "prometheus", "atlas", "sisyphus"...
    name: str
    system: str         # 系统提示词
    description: str
    model: str
    tools: list[str]


class Message(TypedDict, total=False):
    """opencode session 消息（GET /api/session/{id}/message 元素）。"""
    id: str
    role: str           # "user" / "assistant"
    content: str
    createdAt: str


class PromptResponse(TypedDict, total=False):
    """POST /api/session/{id}/prompt 响应。"""
    id: str
    sessionID: str
