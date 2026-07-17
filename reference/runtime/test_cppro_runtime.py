import json
import unittest
from pathlib import Path

from cppro_runtime import (
    AppShellMode,
    CounterMode,
    Edge,
    InputAdapter,
    Profile,
    RawKeySample,
    SkinRuntime,
    SkinState,
)


REPOSITORY = Path(__file__).resolve().parents[2]
KIT_EXAMPLE = REPOSITORY / "examples" / "keyfield-a2" / "manifest"
LAYOUT = REPOSITORY / "layout" / "cppro-key-layout-v1.json"


class InputAdapterTests(unittest.TestCase):
    def test_emits_one_press_one_release_and_analog_changes(self):
        adapter = InputAdapter()
        self.assertEqual(adapter.consume(RawKeySample(4, False, 0)), [])

        pressed = adapter.consume(RawKeySample(4, True, 51, 10))
        repeated = adapter.consume(RawKeySample(4, True, 51, 11))
        analog = adapter.consume(RawKeySample(4, True, 87, 12))
        released = adapter.consume(RawKeySample(4, False, 0, 13))

        self.assertEqual([event.edge for event in pressed], [Edge.PRESSED])
        self.assertEqual(repeated, [])
        self.assertEqual([event.edge for event in analog], [Edge.ANALOG])
        self.assertEqual([event.edge for event in released], [Edge.RELEASED])

    def test_rejects_hcode_that_cannot_fit_byte_property(self):
        with self.assertRaises(ValueError):
            RawKeySample(256, True, 100)


class RuntimeTests(unittest.TestCase):
    def make_runtime(self):
        mode = CounterMode()
        runtime = SkinRuntime(
            profiles={
                "game": Profile("game", {4: "start", 7: "hit", 19: "pause", 8: "end", 21: "reset"}),
                "alt": Profile("alt", {4: "hit"}),
            },
            modes={"counter": mode},
            active_profile_name="game",
            active_mode_name="counter",
        )
        runtime.boot_complete()
        return runtime, mode

    def press(self, runtime, hcode, percentage=100, time_ms=0):
        runtime.consume(RawKeySample(hcode, False, 0, time_ms))
        return runtime.consume(RawKeySample(hcode, True, percentage, time_ms + 1))

    def release(self, runtime, hcode, time_ms=0):
        return runtime.consume(RawKeySample(hcode, False, 0, time_ms))

    def test_game_state_lifecycle(self):
        runtime, mode = self.make_runtime()
        self.assertEqual(runtime.state, SkinState.READY)

        self.press(runtime, 4)
        self.assertEqual(runtime.state, SkinState.LIVE)
        self.press(runtime, 7)
        self.assertEqual(mode.score, 1)

        self.press(runtime, 19)
        self.assertEqual(runtime.state, SkinState.PAUSED)
        self.release(runtime, 19)
        self.press(runtime, 19)
        self.assertEqual(runtime.state, SkinState.LIVE)

        self.press(runtime, 8)
        self.assertEqual(runtime.state, SkinState.RESULT)
        self.press(runtime, 21)
        self.assertEqual(runtime.state, SkinState.READY)
        self.assertEqual(mode.score, 0)

    def test_profile_switch_resets_edges_and_changes_mapping(self):
        runtime, mode = self.make_runtime()
        runtime.set_profile("alt")
        runtime.start()

        self.press(runtime, 4)
        self.assertEqual(mode.score, 1)

    def test_analog_sample_reaches_active_mode(self):
        runtime, mode = self.make_runtime()
        self.press(runtime, 4)
        self.press(runtime, 7, 30)
        runtime.consume(RawKeySample(7, True, 73, 20))
        self.assertEqual(mode.last_pressure, 73)

    def test_release_is_dispatched_to_mode(self):
        profile_data = json.loads((KIT_EXAMPLE / "profile.json").read_text())
        layout_data = json.loads(LAYOUT.read_text())
        profile = Profile.from_key_ids(profile_data, layout_data)
        mode = AppShellMode(("cyan", "magenta", "amber"))
        runtime = SkinRuntime(
            profiles={"shell": profile},
            modes={"shell": mode},
            active_profile_name="shell",
            active_mode_name="shell",
        )
        runtime.boot_complete()
        self.press(runtime, 44)
        self.assertEqual(runtime.state, SkinState.LIVE)
        self.release(runtime, 44)
        self.assertEqual(mode.release_count, 1)

    def test_keyfield_a2_app_shell_controls_and_palette_wrap(self):
        profile_data = json.loads((KIT_EXAMPLE / "profile.json").read_text())
        layout_data = json.loads(LAYOUT.read_text())
        profile = Profile.from_key_ids(profile_data, layout_data)
        mode = AppShellMode(("cyan", "magenta", "amber"))
        runtime = SkinRuntime(
            profiles={"shell": profile},
            modes={"shell": mode},
            active_profile_name="shell",
            active_mode_name="shell",
        )
        runtime.boot_complete()

        for expected in ("magenta", "amber", "cyan"):
            self.press(runtime, 16)
            self.release(runtime, 16)
            self.assertEqual(mode.palette, expected)

        self.press(runtime, 44)
        self.release(runtime, 44)
        self.assertEqual(runtime.state, SkinState.LIVE)
        self.press(runtime, 0)
        self.release(runtime, 0)
        self.assertEqual(runtime.state, SkinState.PAUSED)
        self.press(runtime, 44)
        self.release(runtime, 44)
        self.assertEqual(runtime.state, SkinState.LIVE)
        self.press(runtime, 13)
        self.assertEqual(runtime.state, SkinState.READY)


if __name__ == "__main__":
    unittest.main()
