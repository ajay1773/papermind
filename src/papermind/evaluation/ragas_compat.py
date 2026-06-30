"""Compatibility shims required before importing ragas."""

from __future__ import annotations

import sys
import types


def apply_ragas_compat() -> None:
    """RAGAS optionally imports Vertex AI via langchain-community; stub if missing."""
    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return

    stub = types.ModuleType(module_name)

    class ChatVertexAI:  # noqa: N801 - matches upstream class name
        pass

    stub.ChatVertexAI = ChatVertexAI
    sys.modules[module_name] = stub
