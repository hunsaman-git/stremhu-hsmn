from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.modules.stream.service import StreamService


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, (0, 9, 10)),
        ("bytes=0-0", (0, 0, 1)),
        ("bytes=5-", (5, 9, 5)),
        ("bytes=5-999", (5, 9, 5)),
        ("bytes=-3", (7, 9, 3)),
        ("bytes=-999", (0, 9, 10)),
    ],
)
def test_single_range(header, expected):
    parsed = object.__new__(StreamService)._parse_range_header(10, header)
    assert (parsed.start_byte, parsed.end_byte, parsed.content_length) == expected


@pytest.mark.parametrize(
    "header",
    [
        "bytes=abc",
        "bytes=x-y",
        "bytes=",
        "bytes=-",
        "bytes=--1",
        "bytes=+1-2",
        "bytes=1-+2",
        "bytes=1-2-3",
        "bytes=1_0-",
        "bytes=١-٢",
        "bytes=10-",
        "bytes=8-2",
        "bytes=-0",
        "bytes=0-1,3-4",
        "items=0-1",
        "bytes=" + "9" * 5000 + "-",
    ],
)
def test_invalid_ranges_are_416_with_size(header):
    with pytest.raises(HTTPException) as error:
        object.__new__(StreamService)._parse_range_header(10, header)
    assert error.value.status_code == 416
    assert error.value.headers == {"Content-Range": "bytes */10"}


def test_empty_file():
    service = object.__new__(StreamService)
    assert service._parse_range_header(0).content_length == 0
    with pytest.raises(HTTPException) as error:
        service._parse_range_header(0, "bytes=0-")
    assert error.value.headers == {"Content-Range": "bytes */0"}


@pytest.mark.parametrize("method", ["GET", "HEAD"])
@pytest.mark.parametrize("header", [None, "bytes=3-999", "bytes=-2", "bytes=bad"])
def test_stream_http_contract(monkeypatch, method, header):
    # Real router and range parser; no external trackers or production database.
    import importlib
    from contextlib import contextmanager

    module = importlib.import_module("app.modules.stream.router")
    service = MagicMock()
    file = MagicMock(name="video")
    file.name = "video.mp4"
    file.size = 10

    async def prepare(**kwargs):
        return object.__new__(StreamService)._parse_range_header(
            file.size, kwargs["range_header"]
        ), file

    async def body(**kwargs):
        async def iterator():
            yield b"0123456789"[
                kwargs["stream_start_byte"] : kwargs["stream_end_byte"] + 1
            ]

        return iterator()

    service.prepare_for_stream = prepare
    service.save_playback_history = AsyncMock()
    file.stream = AsyncMock(side_effect=body)
    user = MagicMock(id="user")
    auth = MagicMock()
    auth.verify_api_key.return_value = user

    @contextmanager
    def session():
        yield MagicMock()

    monkeypatch.setattr(module, "isolated_db_session", session)
    monkeypatch.setattr(module, "create_auth_service", lambda db: auth)
    monkeypatch.setattr(module, "create_stream_service", lambda db: service)
    monkeypatch.setattr(module, "get_relay_service", MagicMock())
    monkeypatch.setattr(module, "create_playbacks_service", MagicMock())
    app = FastAPI()
    app.include_router(module.router)
    from app.modules.stream.schemas import StreamToken

    app.dependency_overrides[module.get_parsed_stream_token] = lambda: StreamToken(
        indexer_id="test", torrent_id="1", file_index=0, playback_id="playback"
    )
    with TestClient(app) as client:
        response = client.request(
            method, "/key/stream/token", headers={"Range": header} if header else {}
        )
    if header == "bytes=bad":
        assert response.status_code == 416
        assert response.headers["content-range"] == "bytes */10"
        file.stream.assert_not_awaited()
        return
    expected = (
        b"0123456789"
        if header is None
        else (b"3456789" if header == "bytes=3-999" else b"89")
    )
    assert response.status_code == (200 if header is None else 206)
    assert int(response.headers["content-length"]) == len(expected)
    assert response.content == (expected if method == "GET" else b"")
    if header:
        assert response.headers["content-range"] == f"bytes {10 - len(expected)}-9/10"
    if method == "HEAD":
        file.stream.assert_not_awaited()
