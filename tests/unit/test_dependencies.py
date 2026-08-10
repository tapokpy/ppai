from unittest.mock import patch

from app.core.dependencies import build_cascade_router
from app.core.router import CascadeRouter


def test_build_cascade_router_wires_dependencies():
    with (
        patch("app.core.dependencies.RAGEngine") as rag_cls,
        patch("app.core.dependencies.default_embedding_function"),
        patch("app.core.dependencies.LocalLLMClient") as local_cls,
        patch("app.core.dependencies.CloudLLMClient") as cloud_cls,
        patch("app.core.dependencies.Redis") as redis_cls,
    ):
        router = build_cascade_router()

    assert isinstance(router, CascadeRouter)
    rag_cls.assert_called_once()
    local_cls.assert_called_once()
    cloud_cls.assert_called_once()
    redis_cls.from_url.assert_called_once()


def test_build_cascade_router_passes_no_proxy_by_default():
    with (
        patch("app.core.dependencies.RAGEngine"),
        patch("app.core.dependencies.default_embedding_function"),
        patch("app.core.dependencies.LocalLLMClient"),
        patch("app.core.dependencies.CloudLLMClient") as cloud_cls,
        patch("app.core.dependencies.Redis"),
        patch("app.core.dependencies.settings") as settings_mock,
    ):
        settings_mock.ANTHROPIC_PROXY_URL = ""
        settings_mock.CLOUD_DAILY_LIMIT_PER_USER = 50
        build_cascade_router()

    assert cloud_cls.call_args.kwargs["proxy_url"] is None


def test_build_cascade_router_forwards_configured_proxy_url():
    with (
        patch("app.core.dependencies.RAGEngine"),
        patch("app.core.dependencies.default_embedding_function"),
        patch("app.core.dependencies.LocalLLMClient"),
        patch("app.core.dependencies.CloudLLMClient") as cloud_cls,
        patch("app.core.dependencies.Redis"),
        patch("app.core.dependencies.settings") as settings_mock,
    ):
        settings_mock.ANTHROPIC_PROXY_URL = "http://gluetun:8888"
        settings_mock.CLOUD_DAILY_LIMIT_PER_USER = 50
        build_cascade_router()

    assert cloud_cls.call_args.kwargs["proxy_url"] == "http://gluetun:8888"
