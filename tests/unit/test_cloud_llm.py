from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.services.cloud_llm as cloud_llm_module
from app.services.cloud_llm import CloudLLMClient


@pytest.mark.asyncio
async def test_generate_concatenates_text_blocks():
    client = CloudLLMClient(api_key="test-key", model="claude-3-5-sonnet-20241022")

    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="Ответ "),
            SimpleNamespace(type="text", text="от Claude"),
        ]
    )
    client._client.messages.create = AsyncMock(return_value=response)

    result = await client.generate("Вопрос")

    assert result == "Ответ от Claude"
    client._client.messages.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_includes_context_when_provided():
    client = CloudLLMClient(api_key="test-key", model="claude-3-5-sonnet-20241022")
    create_mock = AsyncMock(
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="ok")])
    )
    client._client.messages.create = create_mock

    await client.generate("Вопрос", context="Справочный контекст")

    sent_content = create_mock.call_args.kwargs["messages"][0]["content"]
    assert "Справочный контекст" in sent_content
    assert "Вопрос" in sent_content


def test_no_proxy_by_default(monkeypatch):
    captured = {}

    class FakeAsyncAnthropic:
        def __init__(self, api_key, http_client=None):
            captured["http_client"] = http_client
            self.messages = MagicMock()

    monkeypatch.setattr(cloud_llm_module.anthropic, "AsyncAnthropic", FakeAsyncAnthropic)

    CloudLLMClient(api_key="test-key", model="claude-3-5-sonnet-20241022")

    assert captured["http_client"] is None


def test_proxy_url_configures_httpx_client_with_proxy(monkeypatch):
    captured = {}

    class FakeAsyncAnthropic:
        def __init__(self, api_key, http_client=None):
            captured["http_client"] = http_client
            self.messages = MagicMock()

    class FakeAsyncClient:
        def __init__(self, proxy=None):
            captured["proxy"] = proxy

    monkeypatch.setattr(cloud_llm_module.anthropic, "AsyncAnthropic", FakeAsyncAnthropic)
    monkeypatch.setattr(cloud_llm_module.httpx, "AsyncClient", FakeAsyncClient)

    CloudLLMClient(api_key="test-key", model="claude-3-5-sonnet-20241022", proxy_url="http://gluetun:8888")

    assert captured["proxy"] == "http://gluetun:8888"
    assert isinstance(captured["http_client"], FakeAsyncClient)
