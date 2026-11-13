import asyncio
import hashlib
from types import SimpleNamespace
from typing import cast

import libtorrent
from fastapi import Request

from app.modules.relay.service import RelayService


def test_real_libtorrent_reads_and_streams_local_piece(tmp_path, monkeypatch):
    """No trackers/peers: validate the native alert path using a verified seed."""
    data = bytes(range(256)) * 100
    (tmp_path / "video.mp4").write_bytes(data)
    piece_size = 16384
    torrent_bytes = libtorrent.bencode(
        {
            b"info": {
                b"name": b"video.mp4",
                b"length": len(data),
                b"piece length": piece_size,
                b"pieces": b"".join(
                    hashlib.sha1(data[offset : offset + piece_size]).digest()
                    for offset in range(0, len(data), piece_size)
                ),
            }
        }
    )
    monkeypatch.setattr(
        "app.modules.relay.service.config",
        SimpleNamespace(
            downloads_dir=tmp_path,
            libtorrent_port=0,
        ),
    )

    async def scenario():
        service = RelayService()
        try:
            torrent = service.add_torrent(torrent_bytes, priority=1)
            file = service.get_torrent_file(torrent.info_hash, 0)
            handle = file.torrent.torrent_handle

            async def wait_for_seed():
                while not all(handle.have_piece(i) for i in range(2)):
                    await asyncio.sleep(0.01)

            await asyncio.wait_for(wait_for_seed(), timeout=10)

            async def connected():
                return False

            iterator = await file.stream(
                playback_id="local",
                user_id="user",
                stream_start_byte=100,
                stream_end_byte=20000,
                request=cast(Request, SimpleNamespace(is_disconnected=connected)),
            )

            async def consume():
                return b"".join([chunk async for chunk in iterator])

            assert await asyncio.wait_for(consume(), timeout=10) == data[100:20001]
            assert file.streams == {}
            assert service._pending_piece_reads == {}
            assert service._piece_fetch_tasks == {}
        finally:
            service._libtorrent_session.set_alert_notify(lambda: None)

    asyncio.run(scenario())
