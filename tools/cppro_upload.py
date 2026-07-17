#!/usr/bin/env python3
"""Install a local CPPRO .pak into a selected skin slot.

The tool is dry-run by default. Pass --send to write the keyboard. It contains
only the synthesized upload and slot-selection paths needed by skin authors.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from pathlib import Path

from pywinusb import hid  # type: ignore


DEFAULT_VID = 0x361D
DEFAULT_PID = 0x0202
REPORT_LEN = 1024
HEADER_LEN = 4
PAYLOAD_LEN = REPORT_LEN - HEADER_LEN


def frame(message_type: int, payload: bytes = b"", report_id: int = 0x01) -> bytes:
    if len(payload) > PAYLOAD_LEN:
        raise ValueError("payload exceeds one HID report")
    result = bytearray(REPORT_LEN)
    result[0] = report_id
    result[1] = len(payload) & 0xFF
    result[2] = (len(payload) >> 8) & 0xFF
    result[3] = message_type & 0xFF
    result[4 : 4 + len(payload)] = payload
    return bytes(result)


def parse_frame(report: bytes) -> tuple[int, bytes] | None:
    if len(report) < HEADER_LEN:
        return None
    length = report[1] | (report[2] << 8)
    if length > len(report) - HEADER_LEN:
        return None
    return report[3], report[4 : 4 + length]


def build_reports(slot: int, pak: Path, file_id: str | None) -> tuple[list[bytes], dict]:
    if pak.suffix.lower() != ".pak":
        raise SystemExit("Only .pak files are accepted")
    if not pak.is_file() or pak.stat().st_size <= 0:
        raise SystemExit(f"PAK is missing or empty: {pak}")

    identity = file_id or str(uuid.uuid4())
    try:
        uuid.UUID(identity)
    except ValueError as exc:
        raise SystemExit("--file-id must be a UUID") from exc

    metadata = {
        "slot": slot,
        "fileName": pak.stem,
        "fileExtension": "pak",
        "fileSize": pak.stat().st_size,
        "fileID": identity,
    }
    encoded = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    reports = [frame(0x10, encoded)]
    with pak.open("rb") as stream:
        while chunk := stream.read(PAYLOAD_LEN):
            reports.append(frame(0x10, chunk))

    # Minimal control transaction established by successful CPPRO transfers.
    reports.insert(0, frame(0x01))
    reports.insert(2, frame(0x20))
    reports.insert(3, frame(0x00))
    if len(reports) > 1500:
        reports.insert(len(reports) // 2, frame(0x11))
    reports.append(frame(0x20))
    for value in (0x03, 0x05, 0x05, 0x01):
        reports.append(frame(0x08, bytes([value])))
        reports.append(frame(0x07, bytes([value])))
    return reports, metadata


def matching_devices(vid: int, pid: int):
    return hid.HidDeviceFilter(vendor_id=vid, product_id=pid).get_devices()


def describe_devices(devices) -> None:
    if not devices:
        print("No matching CPPRO HID interfaces found.")
        return
    for index, device in enumerate(devices):
        path = str(getattr(device, "device_path", ""))
        name = str(getattr(device, "product_name", "HID Interface"))
        print(f"[{index}] {name} {path}")


def choose_device(devices, index: int | None):
    if not devices:
        raise SystemExit("No CPPRO HID interfaces found")
    if index is not None:
        if not 0 <= index < len(devices):
            raise SystemExit(f"--device-index must be 0..{len(devices) - 1}")
        return devices[index]
    preferred = [
        device
        for device in devices
        if "MI_01" in str(getattr(device, "device_path", "")).upper()
    ]
    return preferred[0] if preferred else devices[0]


def output_report(device):
    reports = device.find_output_reports() or []
    candidates = []
    for report in reports:
        try:
            length = len(report.get_raw_data())
        except Exception:
            length = -1
        if length == REPORT_LEN and getattr(report, "report_id", None) == 0x01:
            candidates.append(report)
    if not candidates:
        raise SystemExit("The selected interface has no 1024-byte report 0x01")
    return candidates[0]


class ResponseMonitor:
    def __init__(self, device) -> None:
        self.ack = threading.Event()
        self.complete = threading.Event()
        self.failed_payload: bytes | None = None
        self.total = 0
        self.types: dict[int, int] = {}
        device.set_raw_data_handler(self._handle)

    def _handle(self, data) -> None:
        try:
            parsed = parse_frame(bytes(int(value) & 0xFF for value in data))
        except Exception:
            return
        self.total += 1
        if parsed is None:
            return
        message_type, payload = parsed
        self.types[message_type] = self.types.get(message_type, 0) + 1
        if message_type in (0x07, 0x08, 0x20):
            self.ack.set()
        if message_type == 0x20 and payload == b"\x00\x00":
            self.complete.set()
        elif message_type == 0x20 and len(payload) == 2:
            self.failed_payload = payload

    def wait_ack(self, timeout: float) -> bool:
        observed = self.ack.wait(timeout)
        self.ack.clear()
        return observed


def select_slot(report, slot: int) -> None:
    for candidate in (slot, slot - 1):
        report.send(list(frame(0x30, bytes([candidate]))))
        time.sleep(0.05)


def upload(args, reports: list[bytes]) -> None:
    devices = matching_devices(args.vid, args.pid)
    device = choose_device(devices, args.device_index)
    device.open()
    monitor = ResponseMonitor(device)
    report = output_report(device)
    sent = 0
    started = time.time()
    try:
        waiting = True
        missed = 0
        for offset in range(0, len(reports), args.window):
            for raw in reports[offset : offset + args.window]:
                report.send(list(raw))
                sent += 1
            if waiting:
                if monitor.wait_ack(args.ack_timeout / 1000.0):
                    missed = 0
                else:
                    missed += 1
                    if missed == 1:
                        print(f"No mid-stream ACK after {sent} reports; continuing.")
                    if missed >= args.disable_wait_after:
                        waiting = False
                        print("Device is quiet mid-stream; per-window waits disabled.")

        if not monitor.complete.wait(args.complete_timeout / 1000.0):
            detail = (
                monitor.failed_payload.hex(" ")
                if monitor.failed_payload is not None
                else "none"
            )
            raise SystemExit(
                "Upload finished sending, but success status 00 00 was not "
                f"observed. Last status: {detail}"
            )
        print("Completion: device returned status 00 00.")

        if args.activate:
            bounce = 1 if args.slot != 1 else 2
            select_slot(report, bounce)
            time.sleep(0.25)
            select_slot(report, args.slot)
            print(f"Activated slot {args.slot} after a slot {bounce} bounce.")
    finally:
        try:
            device.set_raw_data_handler(None)
        except Exception:
            pass
        device.close()

    duration = time.time() - started
    print(
        f"Sent {sent} reports in {duration:.2f}s "
        f"({sent / duration:.1f} reports/s)."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run-by-default CPPRO PAK slot installer"
    )
    parser.add_argument("--slot", type=int, choices=range(1, 6), required=True)
    parser.add_argument("--pak", type=Path, required=True)
    parser.add_argument("--send", action="store_true", help="write the keyboard")
    parser.add_argument(
        "--activate",
        action="store_true",
        help="switch away and back after a successful write",
    )
    parser.add_argument("--file-id")
    parser.add_argument("--device-index", type=int)
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--vid", type=lambda value: int(value, 0), default=DEFAULT_VID)
    parser.add_argument("--pid", type=lambda value: int(value, 0), default=DEFAULT_PID)
    parser.add_argument("--window", type=int, default=64)
    parser.add_argument("--ack-timeout", type=int, default=1000)
    parser.add_argument("--complete-timeout", type=int, default=30000)
    parser.add_argument("--disable-wait-after", type=int, default=5)
    args = parser.parse_args()

    if args.list_devices:
        describe_devices(matching_devices(args.vid, args.pid))
        return 0
    if args.activate and not args.send:
        raise SystemExit("--activate requires --send")

    pak = args.pak.resolve()
    reports, metadata = build_reports(args.slot, pak, args.file_id)
    print(
        f"Prepared slot {args.slot}: {pak.name}, {metadata['fileSize']} bytes, "
        f"{len(reports)} HID reports, fileID {metadata['fileID']}."
    )
    if not args.send:
        print("Dry run complete. No data was sent; add --send to write the slot.")
        return 0

    upload(args, reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
