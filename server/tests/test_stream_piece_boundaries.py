import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi import Request

from app.modules.relay.entities import File, Stream, Torrent


@pytest.mark.parametrize(("start", "end"), [(0, 8), (1, 7), (2, 2), (6, 8)])
def test_file_offset_and_range_never_leak_adjacent_files(start, end):
    async def scenario():
        # File occupies offsets 3..11, crossing three 4-byte torrent pieces.
        payload = b"XYZ012345678ABC"

        async def get_piece(handle, index):
            return payload[index * 4 : (index + 1) * 4]

        service = SimpleNamespace(
            get_piece_data=get_piece, trigger_priority_update=MagicMock()
        )
        torrent = SimpleNamespace(
            piece_size=4, info_hash="hash", service=service, torrent_handle=object()
        )
        file = SimpleNamespace(offset=3, size=9, streams={})
        request = SimpleNamespace(is_disconnected=asyncio_disconnect_false)
        stream = Stream(
            "id",
            "playback",
            "user",
            cast(Torrent, torrent),
            cast(File, file),
            start,
            end,
        )
        iterator = await stream.start(cast(Request, request))
        data = b"".join([chunk async for chunk in iterator])
        assert data == b"012345678"[start : end + 1]
        assert file.streams == {}

    asyncio.run(scenario())


async def asyncio_disconnect_false():
    return False


def test_disconnect_cleans_stream_before_iterator_returns():
    async def scenario():
        async def disconnected():
            return True

        torrent = SimpleNamespace(
            piece_size=4, info_hash="hash", service=MagicMock(), torrent_handle=object()
        )
        file = SimpleNamespace(offset=0, size=4, streams={})
        stream = Stream(
            "id", "playback", "user", cast(Torrent, torrent), cast(File, file), 0, 3
        )
        iterator = await stream.start(
            cast(Request, SimpleNamespace(is_disconnected=disconnected))
        )
        assert [chunk async for chunk in iterator] == []
        assert file.streams == {}
        torrent.service.get_piece_data.assert_not_called()

    asyncio.run(scenario())
