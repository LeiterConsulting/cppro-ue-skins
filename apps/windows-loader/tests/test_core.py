from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cppro_loader.catalog import (
    SORT_A_Z,
    SORT_DOWNLOADS,
    SORT_NEWEST,
    Skin,
    _enrich_downloads,
    _parse_catalog,
    download_skin,
    sort_skins,
)
from cppro_loader.device import (
    PAYLOAD_LEN,
    _HidApiTransport,
    _choose_device,
    build_reports,
    frame,
    parse_frame,
    upload_pak,
)
from cppro_loader.pak import PAK_MAGIC, inspect_pak, sha256_file


class FrameTests(unittest.TestCase):
    def test_round_trip(self):
        raw = frame(0x10, b"hello")
        self.assertEqual(len(raw), 1024)
        self.assertEqual(parse_frame(raw), (0x10, b"hello"))

    def test_payload_limit(self):
        frame(0x10, b"x" * PAYLOAD_LEN)
        with self.assertRaises(ValueError):
            frame(0x10, b"x" * (PAYLOAD_LEN + 1))

    def test_prefers_cppro_interface_one(self):
        devices = [
            {"path": b"interface-zero", "interface_number": 0},
            {"path": b"interface-one", "interface_number": 1},
        ]
        self.assertEqual(_choose_device(devices)["interface_number"], 1)

    def test_hidapi_transport_writes_full_report(self):
        class Connection:
            def __init__(self):
                self.opened = None
                self.written = []
                self.closed = False

            def open_path(self, path):
                self.opened = path

            def write(self, raw):
                self.written.append(bytes(raw))
                return len(raw)

            def read(self, _length, _timeout):
                return []

            def close(self):
                self.closed = True

        connection = Connection()
        hid_module = mock.Mock()
        hid_module.device.return_value = connection
        transport = _HidApiTransport(
            {"path": b"cppro-interface-one"},
            hid_module=hid_module,
        )
        raw = frame(0x01)
        transport.send(raw)
        transport.close()
        self.assertEqual(connection.opened, b"cppro-interface-one")
        self.assertEqual(connection.written, [raw])
        self.assertTrue(connection.closed)


class PakTests(unittest.TestCase):
    def make_pak(self, directory: Path) -> Path:
        path = directory / "sample.pak"
        prefix = b"x" * 2048
        index = b"index"
        footer = struct.pack(
            "<IIQQ",
            PAK_MAGIC,
            11,
            len(prefix),
            len(index),
        ) + (b"\x00" * 64)
        path.write_bytes(prefix + index + footer)
        return path

    def test_inspects_version_11_footer(self):
        with tempfile.TemporaryDirectory() as temp:
            info = inspect_pak(self.make_pak(Path(temp)))
            self.assertEqual(info.version, 11)
            self.assertEqual(info.index_offset, 2048)

    def test_build_reports_has_metadata_and_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.make_pak(Path(temp))
            reports, metadata = build_reports(3, path)
            self.assertEqual(metadata["slot"], 3)
            self.assertEqual(parse_frame(reports[0]), (0x01, b""))
            message_type, payload = parse_frame(reports[1])
            self.assertEqual(message_type, 0x10)
            self.assertEqual(json.loads(payload)["fileName"], "sample")

    def test_upload_uses_platform_transport_contract(self):
        class FakeTransport:
            def __init__(self):
                self.handler = None
                self.sent = []
                self.closed = False

            def set_response_handler(self, handler):
                self.handler = handler

            def send(self, raw):
                self.sent.append(raw)
                parsed = parse_frame(raw)
                if self.handler and parsed and parsed[0] == 0x20:
                    self.handler(frame(0x20, b"\x00\x00"))

            def close(self):
                self.closed = True

        with tempfile.TemporaryDirectory() as temp:
            path = self.make_pak(Path(temp))
            transport = FakeTransport()
            with (
                mock.patch(
                    "cppro_loader.device.matching_devices",
                    return_value=[{"path": b"fake", "interface_number": 1}],
                ),
                mock.patch(
                    "cppro_loader.device._open_transport",
                    return_value=transport,
                ),
            ):
                info, result = upload_pak(path, 3, False)
            self.assertEqual(info.version, 11)
            self.assertGreater(result.sent_reports, 0)
            self.assertTrue(transport.closed)


class CatalogTests(unittest.TestCase):
    def entry(self, skin_id="skin", name="Skin", published_at="2026-01-01T00:00:00Z"):
        return {
            "id": skin_id,
            "name": name,
            "subtitle": "Subtitle",
            "description": "Description",
            "tags": [],
            "filename": "skin.pak",
            "bytes": 1,
            "sha256": "A" * 64,
            "source_path": "examples/skin/release/skin.pak",
            "download_url": "https://example.com/skin.pak",
            "docs_url": "https://example.com",
            "accent": "#000000",
            "published_at": published_at,
            "release_tag": "v1",
            "release_asset": f"{skin_id}.pak",
            "downloads": 0,
        }

    def skin(self, skin_id, name, published_at, downloads=0):
        return Skin.from_dict(
            {
                **self.entry(skin_id, name, published_at),
                "downloads": downloads,
            }
        )

    def test_rejects_duplicate_ids(self):
        entry = self.entry()
        payload = json.dumps(
            {
                "schema": "cppro-skin-catalog",
                "version": 1,
                "skins": [entry, entry],
            }
        ).encode()
        with self.assertRaises(ValueError):
            _parse_catalog(payload)

    def test_downloads_and_verifies_catalog_pak(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = PakTests().make_pak(directory)
            skin = Skin(
                id="sample",
                name="Sample",
                subtitle="Test",
                description="Test",
                tags=(),
                filename="downloaded.pak",
                bytes=source.stat().st_size,
                sha256=sha256_file(source),
                source_path="examples/sample/release/downloaded.pak",
                download_url=source.as_uri(),
                docs_url="https://example.com",
                accent="#000000",
                published_at="2026-01-01T00:00:00Z",
                release_tag="v1",
                release_asset="downloaded.pak",
                downloads=0,
            )
            import cppro_loader.catalog as catalog

            original_local_app_data = catalog.local_app_data
            catalog.local_app_data = lambda: directory / "cache"
            try:
                destination = download_skin(skin)
                self.assertEqual(destination.name, "downloaded.pak")
                self.assertEqual(sha256_file(destination), skin.sha256)
                self.assertEqual(download_skin(skin), destination)
            finally:
                catalog.local_app_data = original_local_app_data

    def test_enriches_release_download_counts_and_urls(self):
        skins = [
            self.skin("alpha", "Alpha", "2026-01-01T00:00:00Z"),
            self.skin("beta", "Beta", "2026-01-02T00:00:00Z"),
        ]
        payload = json.dumps(
            [
                {
                    "assets": [
                        {
                            "name": "alpha.pak",
                            "download_count": 12,
                            "browser_download_url": "https://example.com/alpha.pak",
                        },
                        {
                            "name": "beta.pak",
                            "download_count": 3,
                            "browser_download_url": "https://example.com/beta.pak",
                        },
                    ]
                },
                {
                    "assets": [
                        {
                            "name": "alpha.pak",
                            "download_count": 5,
                            "browser_download_url": "https://old.example.com/alpha.pak",
                        }
                    ]
                },
            ]
        ).encode()
        enriched = _enrich_downloads(skins, payload)
        self.assertEqual(enriched[0].downloads, 17)
        self.assertEqual(enriched[1].downloads, 3)
        self.assertEqual(
            enriched[0].download_url,
            "https://example.com/alpha.pak",
        )

    def test_sorts_newest_alphabetical_and_downloads(self):
        skins = [
            self.skin("alpha", "Alpha", "2026-01-01T00:00:00Z", 2),
            self.skin("charlie", "Charlie", "2026-01-03T00:00:00Z", 1),
            self.skin("beta", "Beta", "2026-01-02T00:00:00Z", 9),
        ]
        self.assertEqual(
            [skin.id for skin in sort_skins(skins, SORT_NEWEST)],
            ["charlie", "beta", "alpha"],
        )
        self.assertEqual(
            [skin.id for skin in sort_skins(skins, SORT_A_Z)],
            ["alpha", "beta", "charlie"],
        )
        self.assertEqual(
            [skin.id for skin in sort_skins(skins, SORT_DOWNLOADS)],
            ["beta", "alpha", "charlie"],
        )


if __name__ == "__main__":
    unittest.main()
