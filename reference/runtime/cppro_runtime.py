"""Headless reference runtime for CPPRO interactive-skin behavior.

The keyboard-facing Blueprint adapter should mirror these semantics: normalize raw
SkinApi samples into edges, map usage IDs through a profile, and send actions to a
mode/state machine.  This module deliberately has no Unreal dependency so traces
can be replayed in unit tests before a skin is cooked or uploaded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Protocol


class Edge(str, Enum):
    PRESSED = "pressed"
    RELEASED = "released"
    ANALOG = "analog"


class SkinState(str, Enum):
    BOOT = "boot"
    ATTRACT = "attract"
    READY = "ready"
    LIVE = "live"
    PAUSED = "paused"
    RESULT = "result"

    # Compatibility names for early experiments. New examples use LIVE/RESULT.
    PLAYING = "live"
    GAME_OVER = "result"


@dataclass(frozen=True)
class RawKeySample:
    """The verified raw SkinApi OnKeyEvent payload."""

    hcode: int
    is_actuated: bool
    percentage: int
    time_ms: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.hcode <= 255:
            raise ValueError("hcode must fit the cooked ByteProperty (0..255)")
        if self.time_ms < 0:
            raise ValueError("time_ms cannot be negative")


@dataclass(frozen=True)
class KeyEvent:
    hcode: int
    edge: Edge
    percentage: int
    time_ms: int


@dataclass
class _KeyTrack:
    is_actuated: bool = False
    percentage: int = 0
    observed: bool = False


class InputAdapter:
    """Turns a noisy stream of raw samples into deterministic input edges."""

    def __init__(self) -> None:
        self._keys: dict[int, _KeyTrack] = {}

    def reset(self) -> None:
        self._keys.clear()

    def consume(self, sample: RawKeySample) -> list[KeyEvent]:
        track = self._keys.setdefault(sample.hcode, _KeyTrack())
        events: list[KeyEvent] = []

        if sample.is_actuated != track.is_actuated:
            events.append(
                KeyEvent(
                    hcode=sample.hcode,
                    edge=Edge.PRESSED if sample.is_actuated else Edge.RELEASED,
                    percentage=sample.percentage,
                    time_ms=sample.time_ms,
                )
            )
        elif track.observed and sample.percentage != track.percentage:
            events.append(
                KeyEvent(
                    hcode=sample.hcode,
                    edge=Edge.ANALOG,
                    percentage=sample.percentage,
                    time_ms=sample.time_ms,
                )
            )

        track.is_actuated = sample.is_actuated
        track.percentage = sample.percentage
        track.observed = True
        return events


@dataclass(frozen=True)
class Profile:
    """Maps USB usage IDs (HCode) to semantic game actions."""

    name: str
    bindings: Mapping[int, str]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Profile":
        return cls(
            name=str(value["name"]),
            bindings={int(key): str(action) for key, action in value["bindings"].items()},
        )

    @classmethod
    def from_key_ids(
        cls,
        value: Mapping[str, Any],
        layout: Mapping[str, Any],
    ) -> "Profile":
        """Resolve designer-facing physical key IDs to native layout indices."""

        index_by_id = {
            str(key["id"]): int(key["layout_index"])
            for key in layout["keys"]
        }
        unknown = sorted(set(value["bindings"]) - set(index_by_id))
        if unknown:
            raise ValueError(
                "profile references unknown key IDs: " + ", ".join(unknown)
            )
        return cls(
            name=str(value["name"]),
            bindings={
                index_by_id[str(key_id)]: str(action)
                for key_id, action in value["bindings"].items()
            },
        )

    def action_for(self, hcode: int) -> str | None:
        return self.bindings.get(hcode)


@dataclass(frozen=True)
class ActionEvent:
    action: str
    key: KeyEvent
    profile: str


class Mode(Protocol):
    name: str

    def on_enter(self, runtime: "SkinRuntime") -> None: ...

    def on_action(self, runtime: "SkinRuntime", event: ActionEvent) -> None: ...

    def on_release(self, runtime: "SkinRuntime", event: ActionEvent) -> None: ...

    def on_analog(self, runtime: "SkinRuntime", event: ActionEvent) -> None: ...


@dataclass
class SkinRuntime:
    profiles: Mapping[str, Profile]
    modes: Mapping[str, Mode]
    active_profile_name: str
    active_mode_name: str
    state: SkinState = SkinState.BOOT
    adapter: InputAdapter = field(default_factory=InputAdapter)
    event_log: list[ActionEvent] = field(default_factory=list)

    @property
    def profile(self) -> Profile:
        return self.profiles[self.active_profile_name]

    @property
    def mode(self) -> Mode:
        return self.modes[self.active_mode_name]

    def boot_complete(self) -> None:
        self._require_state(SkinState.BOOT)
        self.state = SkinState.READY
        self.mode.on_enter(self)

    def set_profile(self, name: str) -> None:
        if name not in self.profiles:
            raise KeyError(f"unknown profile: {name}")
        self.active_profile_name = name
        # A held key from the old profile must not become a phantom edge in the new one.
        self.adapter.reset()

    def set_mode(self, name: str) -> None:
        if name not in self.modes:
            raise KeyError(f"unknown mode: {name}")
        if self.state not in (SkinState.READY, SkinState.PAUSED, SkinState.GAME_OVER):
            raise RuntimeError("modes may only change from ready, paused, or game_over")
        self.active_mode_name = name
        self.adapter.reset()
        self.mode.on_enter(self)

    def start(self) -> None:
        self._require_state(SkinState.READY)
        self.state = SkinState.LIVE

    def pause(self) -> None:
        self._require_state(SkinState.LIVE)
        self.state = SkinState.PAUSED

    def resume(self) -> None:
        self._require_state(SkinState.PAUSED)
        self.state = SkinState.LIVE

    def game_over(self) -> None:
        self._require_state(SkinState.LIVE)
        self.state = SkinState.RESULT

    def reset_game(self) -> None:
        self._require_state(SkinState.RESULT)
        self.state = SkinState.READY
        self.adapter.reset()
        self.mode.on_enter(self)

    def enter_attract(self) -> None:
        if self.state not in (SkinState.BOOT, SkinState.READY):
            raise RuntimeError("attract may only begin from boot or ready")
        self.state = SkinState.ATTRACT
        self.adapter.reset()

    def wake(self) -> None:
        self._require_state(SkinState.ATTRACT)
        self.state = SkinState.READY
        self.adapter.reset()
        self.mode.on_enter(self)

    def consume(self, sample: RawKeySample) -> list[ActionEvent]:
        dispatched: list[ActionEvent] = []
        for key_event in self.adapter.consume(sample):
            action = self.profile.action_for(key_event.hcode)
            if action is None:
                continue
            event = ActionEvent(action, key_event, self.profile.name)
            self.event_log.append(event)
            dispatched.append(event)
            if key_event.edge is Edge.ANALOG:
                self.mode.on_analog(self, event)
            elif key_event.edge is Edge.PRESSED:
                self.mode.on_action(self, event)
            elif key_event.edge is Edge.RELEASED:
                self.mode.on_release(self, event)
        return dispatched

    def replay(self, samples: Iterable[RawKeySample]) -> list[ActionEvent]:
        return [event for sample in samples for event in self.consume(sample)]

    def _require_state(self, expected: SkinState) -> None:
        if self.state is not expected:
            raise RuntimeError(f"expected state {expected.value}, got {self.state.value}")


@dataclass
class CounterMode:
    """Small example mode used by tests and as a Blueprint implementation guide."""

    name: str = "counter"
    score: int = 0
    last_pressure: int = 0

    def on_enter(self, runtime: SkinRuntime) -> None:
        self.score = 0
        self.last_pressure = 0

    def on_action(self, runtime: SkinRuntime, event: ActionEvent) -> None:
        if event.action == "start" and runtime.state is SkinState.READY:
            runtime.start()
        elif event.action == "hit" and runtime.state is SkinState.LIVE:
            self.score += 1
        elif event.action == "pause" and runtime.state is SkinState.LIVE:
            runtime.pause()
        elif event.action == "pause" and runtime.state is SkinState.PAUSED:
            runtime.resume()
        elif event.action == "end" and runtime.state is SkinState.LIVE:
            runtime.game_over()
        elif event.action == "reset" and runtime.state is SkinState.RESULT:
            runtime.reset_game()

    def on_release(self, runtime: SkinRuntime, event: ActionEvent) -> None:
        pass

    def on_analog(self, runtime: SkinRuntime, event: ActionEvent) -> None:
        if event.action == "hit" and runtime.state is SkinState.LIVE:
            self.last_pressure = event.key.percentage


@dataclass
class AppShellMode:
    """Reference app shell used by Keyfield A2 and future example skins."""

    palettes: tuple[str, ...]
    name: str = "app_shell"
    palette_index: int = 0
    release_count: int = 0

    @property
    def palette(self) -> str:
        return self.palettes[self.palette_index]

    def on_enter(self, runtime: SkinRuntime) -> None:
        self.release_count = 0

    def on_action(self, runtime: SkinRuntime, event: ActionEvent) -> None:
        if event.action == "next_palette":
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
        elif event.action == "start_or_resume":
            if runtime.state is SkinState.READY:
                runtime.start()
            elif runtime.state is SkinState.PAUSED:
                runtime.resume()
            elif runtime.state is SkinState.RESULT:
                runtime.reset_game()
        elif event.action == "pause" and runtime.state is SkinState.LIVE:
            runtime.pause()
        elif event.action == "reset" and runtime.state in (
            SkinState.LIVE,
            SkinState.PAUSED,
            SkinState.RESULT,
        ):
            runtime.state = SkinState.READY
            runtime.adapter.reset()

    def on_release(self, runtime: SkinRuntime, event: ActionEvent) -> None:
        # Release remains observable even when the app is paused, which is the
        # key invariant needed to prevent visually latched keys.
        self.release_count += 1

    def on_analog(self, runtime: SkinRuntime, event: ActionEvent) -> None:
        pass
