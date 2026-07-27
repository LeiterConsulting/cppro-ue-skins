# Examples

Every example is a curated, device-tested starting point rather than a dump of
development experiments. Each folder documents the interaction model, source
assets, exact release PAK, checksum, and any important runtime limitations.

Every installable example also follows the
[skin library standard](SKIN_STANDARD.md). Its `library.json` entry is compiled
into the Windows loader catalog, so adding an example does not require editing
the application.

| Example | Start here when you want to build | Device-tested slot |
| --- | --- | ---: |
| [Keyfield A2](keyfield-a2/README.md) | An app-like skin with all 68 keys, modes, palettes, readable safe-region UI, and bounded press/release effects | 5 |
| [Keyfield Pulse](keyfield-pulse/README.md) | A clean always-live keyboard skin with mapped lights, hold-sensitive releases, waves, and Caps state | 2 |
| [Moodfield](moodfield/README.md) | A living substrate with persistent typing geography, compact-pattern recognition, lifecycle color, and Caps state | 2 |
| [Mender Swarm](mender-swarm/README.md) | A synthetic fabric maintained by twelve animated agents, with persistent key damage and four concurrent repair crews | 2 |
| [Koi Pond](koi-pond/README.md) | A full-screen living scene with animated actors, continuous steering, ripples, and localized physics impulses | 5 |
| [Koi Pond: Caps Indicator](koi-pond-caps-indicator/README.md) | A visual skin that also keeps a small persistent Boolean-style state across input events | 4 |

The Caps Indicator variant deliberately reuses the Koi Pond artwork and shared
`/Game/CPPRO/TouchPoolL1` content. Its folder contains only the additional
Blueprint layer, exact map snapshot, and release artifact needed to explain and
reproduce the stateful behavior.

Use a nonessential slot when testing a rebuilt PAK, keep a known-good skin in a
different slot, and read [Safety and Compatibility](../docs/safety-and-compatibility.md)
before writing to the keyboard.
