from __future__ import annotations

import json
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from .pak import PakInfo, inspect_pak


DEFAULT_VID = 0x361D
DEFAULT_PID = 0x0202
REPORT_LEN = 1024
HEADER_LEN = 4
PAYLOAD_LEN = REPORT_LEN - HEADER_LEN

ProgressCallback = Callable[[float, str], None]
ResponseCallback = Callable[[bytes], None]


@dataclass(frozen=True)
class DeviceStatus:
    connected: bool
    count: int
    name: str


@dataclass(frozen=True)
class UploadResult:
    sent_reports: int
    seconds: float
    slot: int
    activated: bool
    demo: bool


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


def _load_pywinusb():
    from pywinusb import hid  # type: ignore

    return hid


def _load_hidapi():
    import hid  # type: ignore

    return hid


def backend_name() -> str:
    return "pywinusb" if sys.platform == "win32" else "HIDAPI"


def matching_devices():
    if sys.platform == "win32":
        hid = _load_pywinusb()
        return hid.HidDeviceFilter(
            vendor_id=DEFAULT_VID,
            product_id=DEFAULT_PID,
        ).get_devices()
    hid = _load_hidapi()
    return hid.enumerate(DEFAULT_VID, DEFAULT_PID)


def _interface_number(device) -> int | None:
    if isinstance(device, dict):
        value = device.get("interface_number")
        return int(value) if isinstance(value, int) else None
    path = str(getattr(device, "device_path", "")).upper()
    return 1 if "MI_01" in path else None


def _device_name(device) -> str:
    if isinstance(device, dict):
        value = device.get("product_string")
    else:
        value = getattr(device, "product_name", "")
    return str(value or "Centerpiece Pro")


def _choose_device(devices):
    if not devices:
        raise RuntimeError(
            "No CPPRO was found. Connect the keyboard directly by USB and retry."
        )
    preferred = [device for device in devices if _interface_number(device) == 1]
    return preferred[0] if preferred else devices[0]


def detect_device() -> DeviceStatus:
    try:
        devices = matching_devices()
    except (ImportError, OSError) as exc:
        return DeviceStatus(False, 0, f"{backend_name()} unavailable: {exc}")
    if not devices:
        return DeviceStatus(False, 0, "CPPRO not found")
    device = _choose_device(devices)
    return DeviceStatus(True, len(devices), _device_name(device))


def build_reports(slot: int, pak: Path) -> tuple[list[bytes], dict]:
    if slot not in range(1, 6):
        raise ValueError("Choose a slot from 1 through 5.")
    identity = str(uuid.uuid4())
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


def _output_report(device):
    candidates = []
    for report in device.find_output_reports() or []:
        try:
            length = len(report.get_raw_data())
        except Exception:
            length = -1
        if length == REPORT_LEN and getattr(report, "report_id", None) == 0x01:
            candidates.append(report)
    if not candidates:
        raise RuntimeError(
            "The CPPRO upload interface is present but its 1024-byte output "
            "report is unavailable."
        )
    return candidates[0]


class _WindowsTransport:
    def __init__(self, candidate) -> None:
        self.device = candidate
        self.device.open()
        self.report = _output_report(self.device)

    def set_response_handler(self, handler: ResponseCallback | None) -> None:
        if handler is None:
            self.device.set_raw_data_handler(None)
            return

        def receive(data) -> None:
            try:
                handler(bytes(int(value) & 0xFF for value in data))
            except Exception:
                return

        self.device.set_raw_data_handler(receive)

    def send(self, raw: bytes) -> None:
        self.report.send(list(raw))

    def close(self) -> None:
        self.device.close()


class _HidApiTransport:
    def __init__(self, candidate, hid_module=None) -> None:
        self.hid = hid_module or _load_hidapi()
        self.device = self.hid.device()
        path = candidate.get("path")
        if path is None:
            raise RuntimeError("The CPPRO HID interface did not provide a device path.")
        try:
            self.device.open_path(path)
        except OSError as exc:
            if sys.platform.startswith("linux"):
                raise PermissionError(
                    "The CPPRO was found but could not be opened. Install the "
                    "included Linux udev rule, reconnect the keyboard, and retry."
                ) from exc
            raise
        self.stop = threading.Event()
        self.reader: threading.Thread | None = None
        self.handler: ResponseCallback | None = None

    def set_response_handler(self, handler: ResponseCallback | None) -> None:
        self.handler = handler
        if handler is None:
            self.stop.set()
            if self.reader and self.reader.is_alive():
                self.reader.join(timeout=0.5)
            self.reader = None
            return
        if self.reader and self.reader.is_alive():
            return
        self.stop.clear()
        self.reader = threading.Thread(
            target=self._read_loop,
            name="cppro-hid-reader",
            daemon=True,
        )
        self.reader.start()

    def _read_loop(self) -> None:
        while not self.stop.is_set():
            try:
                data = self.device.read(REPORT_LEN, 100)
            except (OSError, ValueError):
                return
            if data and self.handler:
                try:
                    self.handler(bytes(int(value) & 0xFF for value in data))
                except Exception:
                    continue

    def send(self, raw: bytes) -> None:
        try:
            written = self.device.write(raw)
        except TypeError:
            written = self.device.write(list(raw))
        if written not in (None, len(raw)):
            raise OSError(
                f"The CPPRO accepted {written} of {len(raw)} HID report bytes."
            )

    def close(self) -> None:
        self.set_response_handler(None)
        self.device.close()


def _open_transport(candidate):
    if sys.platform == "win32":
        return _WindowsTransport(candidate)
    return _HidApiTransport(candidate)


class _ResponseMonitor:
    def __init__(self, transport) -> None:
        self.ack = threading.Event()
        self.complete = threading.Event()
        self.failed_payload: bytes | None = None
        transport.set_response_handler(self._handle)

    def _handle(self, data: bytes) -> None:
        parsed = parse_frame(data)
        if parsed is None:
            return
        message_type, payload = parsed
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


def _select_slot(transport, slot: int) -> None:
    for candidate in (slot, slot - 1):
        transport.send(frame(0x30, bytes([candidate])))
        time.sleep(0.05)


def upload_pak(
    pak: Path,
    slot: int,
    activate: bool,
    progress: ProgressCallback | None = None,
    *,
    expected_sha256: str | None = None,
    demo: bool = False,
) -> tuple[PakInfo, UploadResult]:
    def emit(value: float, message: str) -> None:
        if progress:
            progress(max(0.0, min(1.0, value)), message)

    emit(0.01, "Checking the PAK…")
    info = inspect_pak(pak, expected_sha256)
    emit(0.05, f"Verified {info.bytes / 1024 / 1024:.1f} MB PAK")
    reports, _ = build_reports(slot, info.path)

    if demo:
        started = time.time()
        for step in range(1, 51):
            time.sleep(0.012)
            emit(
                0.05 + 0.92 * (step / 50),
                f"Demo upload to slot {slot}: {step * 2}%",
            )
        emit(1.0, f"Demo complete — slot {slot} was not changed")
        return info, UploadResult(len(reports), time.time() - started, slot, activate, True)

    devices = matching_devices()
    device = _choose_device(devices)
    transport = _open_transport(device)
    monitor = _ResponseMonitor(transport)
    sent = 0
    started = time.time()
    window = 64
    waiting = True
    missed = 0
    try:
        for offset in range(0, len(reports), window):
            for raw in reports[offset : offset + window]:
                transport.send(raw)
                sent += 1
            emit(
                0.05 + 0.90 * (sent / len(reports)),
                f"Sending to slot {slot} — {sent:,} of {len(reports):,} reports",
            )
            if waiting:
                if monitor.wait_ack(1.0):
                    missed = 0
                else:
                    missed += 1
                    if missed >= 5:
                        waiting = False

        emit(0.96, "Waiting for the keyboard to confirm…")
        if not monitor.complete.wait(30.0):
            detail = (
                monitor.failed_payload.hex(" ")
                if monitor.failed_payload is not None
                else "no status"
            )
            raise RuntimeError(
                "The transfer finished, but the keyboard did not confirm "
                f"success ({detail}). The selected slot may have been reset."
            )
        if activate:
            emit(0.98, f"Activating slot {slot}…")
            bounce = 1 if slot != 1 else 2
            _select_slot(transport, bounce)
            time.sleep(0.25)
            _select_slot(transport, slot)
    finally:
        try:
            transport.set_response_handler(None)
        except Exception:
            pass
        transport.close()

    duration = time.time() - started
    emit(1.0, f"Installed successfully in slot {slot}")
    return info, UploadResult(sent, duration, slot, activate, False)


def demo_arguments() -> SimpleNamespace:
    return SimpleNamespace(demo=True)
