# -*- coding: utf-8 -*-
"""Generate original art for three CPPRO clean-room screensaver skins.

The output contract intentionally matches the proven Mender Swarm authoring
helper: one full-screen base, two moving overlays, one key-event image, and
sixteen transparent agent frames.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


WIDTH = 1920
HEIGHT = 550
AGENT_WIDTH = 160
AGENT_HEIGHT = 112
SCALE = 3


def glow_layer(layer: Image.Image, radius: float, strength: float = 0.7) -> Image.Image:
    glow = layer.filter(ImageFilter.GaussianBlur(radius))
    alpha = glow.getchannel("A").point(
        lambda value: min(255, int(value * strength))
    )
    glow.putalpha(alpha)
    return Image.alpha_composite(glow, layer)


def save_agent(drawer, path: Path, frame: int) -> None:
    large = Image.new(
        "RGBA",
        (AGENT_WIDTH * SCALE, AGENT_HEIGHT * SCALE),
        (0, 0, 0, 0),
    )
    drawer(ImageDraw.Draw(large, "RGBA"), frame, SCALE)
    large = glow_layer(large, 7.0, 0.42)
    large.resize(
        (AGENT_WIDTH, AGENT_HEIGHT),
        Image.Resampling.LANCZOS,
    ).save(path)


def starfield(image: Image.Image, seed: int, amount: int = 180) -> None:
    rng = random.Random(seed)
    draw = ImageDraw.Draw(image, "RGBA")
    for index in range(amount):
        x = rng.randrange(WIDTH)
        y = rng.randrange(max(1, HEIGHT * 3 // 5))
        radius = 1 if index % 11 else 2
        alpha = rng.randrange(40, 130)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(170, 220, 255, alpha),
        )


def night_shift_base(seed: int) -> Image.Image:
    rng = random.Random(seed)
    image = Image.new("RGBA", (WIDTH, HEIGHT), (3, 7, 22, 255))
    pixels = image.load()
    for y in range(HEIGHT):
        horizon = y / HEIGHT
        for x in range(WIDTH):
            cobalt = int(22 * (1.0 - horizon))
            violet = int(13 * math.sin(x / 340.0) ** 2)
            pixels[x, y] = (
                3 + violet // 3,
                7 + cobalt // 3,
                22 + cobalt + violet,
                255,
            )
    starfield(image, seed)
    draw = ImageDraw.Draw(image, "RGBA")

    # Three parallax neighborhoods, with enough large windows to survive the
    # physical keybed and ASTC texture compression.
    palettes = [
        ((8, 13, 32, 255), 250, 55, 0.30),
        ((7, 10, 23, 255), 320, 42, 0.20),
        ((4, 7, 16, 255), 400, 34, 0.12),
    ]
    for layer, (wall, baseline, minimum, light_chance) in enumerate(palettes):
        x = -40
        while x < WIDTH + 60:
            width = rng.randrange(58, 146)
            height = rng.randrange(minimum, 120 + layer * 44)
            top = baseline - height
            draw.rectangle((x, top, x + width, HEIGHT), fill=wall)
            draw.line(
                (x, top, x + width, top),
                fill=(41, 65, 105, 180),
                width=2,
            )
            for wy in range(top + 14, baseline - 10, 22):
                for wx in range(x + 10, x + width - 8, 18):
                    if rng.random() < light_chance:
                        color = (
                            (255, 190, 68, rng.randrange(120, 220))
                            if rng.random() < 0.72
                            else (80, 220, 255, rng.randrange(90, 190))
                        )
                        draw.rectangle((wx, wy, wx + 7, wy + 9), fill=color)
            x += width + rng.randrange(8, 25)

    # Elevated night traffic and a cool foreground roofscape.
    draw.rectangle((0, 408, WIDTH, 430), fill=(9, 18, 36, 255))
    draw.line((0, 407, WIDTH, 407), fill=(70, 185, 255, 145), width=3)
    for x in range(28, WIDTH, 82):
        draw.rectangle((x, 430, x + 12, HEIGHT), fill=(6, 12, 24, 255))
    for x in range(0, WIDTH, 64):
        draw.line(
            (x, HEIGHT - 28, x + 38, HEIGHT - 28),
            fill=(255, 92, 183, 75),
            width=2,
        )
    return image


def night_shift_flow(seed: int, layer_index: int) -> Image.Image:
    rng = random.Random(seed + layer_index * 31)
    image = Image.new("RGBA", (2000, 590), (0, 0, 0, 0))
    soft = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(soft, "RGBA")
    if layer_index == 0:
        # Sky lanes: blinking autonomous traffic.
        for lane in range(4):
            y = 70 + lane * 82
            for index in range(14):
                x = rng.randrange(-60, 1980)
                color = (85, 222, 255, 155) if index % 3 else (255, 80, 186, 145)
                d.line((x, y, x + 20, y), fill=color, width=3)
                d.ellipse((x + 21, y - 3, x + 27, y + 3), fill=(255, 235, 170, 190))
    else:
        # Windows and trains become a second, slower motion layer.
        for lane in (430, 496):
            for x in range(-20, 2000, 86):
                color = (255, 171, 54, 105) if (x // 86) % 2 else (65, 210, 255, 95)
                d.rectangle((x, lane, x + 36, lane + 8), fill=color)
        for index in range(35):
            x = rng.randrange(20, 1980)
            y = rng.randrange(130, 390)
            d.rectangle((x, y, x + 6, y + 10), fill=(255, 196, 80, 60))
    return glow_layer(soft, 5.0, 0.6)


def night_shift_event() -> Image.Image:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(glow, "RGBA")
    for radius, alpha, width in ((104, 45, 6), (78, 90, 6), (50, 185, 8)):
        d.ellipse(
            (128 - radius, 128 - radius, 128 + radius, 128 + radius),
            outline=(75, 218, 255, alpha),
            width=width,
        )
    d.polygon(
        [(128, 45), (188, 84), (188, 162), (128, 205), (68, 162), (68, 84)],
        fill=(10, 24, 55, 215),
        outline=(255, 102, 198, 230),
    )
    for x in (91, 118, 145):
        for y in (91, 119, 147):
            d.rectangle((x, y, x + 15, y + 18), fill=(255, 202, 76, 225))
    return glow_layer(glow, 8.0, 0.65)


def draw_service_craft(d: ImageDraw.ImageDraw, frame: int, scale: int) -> None:
    def p(value):
        return int(value * scale)

    alarm = frame >= 8
    repair = frame <= 2
    bob = math.sin(frame * 1.27) * 3.0
    cx = p(80)
    cy = p(53 + bob)
    body = (cx - p(35), cy - p(15), cx + p(34), cy + p(16))
    d.rounded_rectangle(
        body,
        radius=p(11),
        fill=(12, 31, 62, 245),
        outline=(92, 226, 255, 255),
        width=p(3),
    )
    d.ellipse(
        (cx - p(11), cy - p(12), cx + p(12), cy + p(12)),
        fill=(34, 81, 124, 255),
        outline=(224, 251, 255, 255),
        width=p(2),
    )
    for side in (-1, 1):
        rotor_x = cx + side * p(42)
        d.line(
            (cx + side * p(27), cy, rotor_x, cy - p(15)),
            fill=(117, 230, 255, 235),
            width=p(3),
        )
        d.ellipse(
            (rotor_x - p(13), cy - p(21), rotor_x + p(13), cy - p(15)),
            fill=(70, 217, 255, 100),
            outline=(190, 246, 255, 210),
            width=p(2),
        )
    beacon = (255, 79, 184, 255) if alarm else (255, 205, 70, 245)
    d.ellipse((cx - p(5), cy - p(23), cx + p(5), cy - p(13)), fill=beacon)
    if repair:
        d.polygon(
            [
                (cx - p(12), cy + p(15)),
                (cx + p(12), cy + p(15)),
                (cx + p(25), cy + p(48)),
                (cx - p(25), cy + p(48)),
            ],
            fill=(255, 211, 94, 78),
        )
        d.line(
            (cx, cy + p(15), cx, cy + p(47)),
            fill=(255, 240, 170, 230),
            width=p(2),
        )
    elif alarm:
        for index in range(4):
            y = cy - p(12) + index * p(9)
            d.line(
                (cx - p(62), y, cx - p(43), y),
                fill=(255, 86, 190, 180 - index * 20),
                width=p(2),
            )


def conveyor_base(seed: int) -> Image.Image:
    rng = random.Random(seed)
    image = Image.new("RGBA", (WIDTH, HEIGHT), (6, 6, 9, 255))
    d = ImageDraw.Draw(image, "RGBA")
    d.rectangle((0, 0, WIDTH, HEIGHT), fill=(8, 9, 12, 255))

    # Factory ceiling and floor.
    for x in range(0, WIDTH + 120, 120):
        d.line((x, 0, x - 90, 125), fill=(61, 69, 73, 120), width=5)
    for y in (92, 202, 312, 422):
        d.rounded_rectangle(
            (0, y, WIDTH, y + 62),
            radius=12,
            fill=(25, 30, 33, 255),
            outline=(87, 104, 108, 230),
            width=3,
        )
        d.rectangle((0, y + 19, WIDTH, y + 45), fill=(11, 14, 16, 255))
        for x in range(-20, WIDTH + 40, 48):
            color = (250, 145, 36, 110) if (x // 48 + y) % 3 == 0 else (58, 205, 196, 85)
            d.polygon(
                [
                    (x, y + 22),
                    (x + 16, y + 32),
                    (x, y + 42),
                    (x + 22, y + 42),
                    (x + 38, y + 32),
                    (x + 22, y + 22),
                ],
                fill=color,
            )
        for x in range(20, WIDTH, 92):
            d.ellipse(
                (x, y + 49, x + 20, y + 69),
                fill=(10, 11, 12, 255),
                outline=(116, 131, 134, 210),
                width=2,
            )

    # Machinery, sorting gates and suspended indicators.
    for index, x in enumerate(range(65, WIDTH, 185)):
        h = rng.randrange(42, 84)
        color = (244, 137, 35, 150) if index % 2 else (49, 218, 202, 135)
        d.rectangle((x, 14, x + 100, 14 + h), fill=(18, 22, 24, 255), outline=color, width=3)
        d.rectangle((x + 13, 27, x + 86, 44), fill=color)
        d.line((x + 50, 14 + h, x + 50, 92), fill=(93, 104, 106, 180), width=4)

    for x in range(0, WIDTH, 38):
        d.line((x, 520, x + 20, 550), fill=(244, 132, 30, 60), width=2)
    return image


def conveyor_flow(seed: int, layer_index: int) -> Image.Image:
    rng = random.Random(seed + 71 * layer_index)
    image = Image.new("RGBA", (2000, 590), (0, 0, 0, 0))
    d = ImageDraw.Draw(image, "RGBA")
    if layer_index == 0:
        for y in (112, 222, 332, 442):
            for x in range(-50, 2000, 96):
                color = (255, 157, 45, 145) if (x // 96) % 2 else (74, 232, 218, 120)
                d.polygon(
                    [(x, y), (x + 18, y + 10), (x, y + 20), (x + 11, y + 20), (x + 30, y + 10), (x + 11, y)],
                    fill=color,
                )
    else:
        # Parcels live on the overlay, so the continuous UMG drift reads as a
        # production line even before a key event occurs.
        for index in range(33):
            x = rng.randrange(-40, 1980)
            y = (100, 210, 320, 430)[index % 4]
            w = rng.randrange(22, 44)
            color = (245, 153, 44, 145) if index % 3 else (61, 216, 204, 135)
            d.rectangle((x, y, x + w, y + 28), fill=(21, 27, 29, 230), outline=color, width=2)
            d.line((x + 5, y + 8, x + w - 5, y + 8), fill=(245, 231, 184, 120), width=2)
    return glow_layer(image, 4.0, 0.55)


def conveyor_event() -> Image.Image:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(image, "RGBA")
    d.ellipse((30, 30, 226, 226), fill=(12, 18, 20, 210), outline=(255, 151, 37, 220), width=9)
    d.ellipse((58, 58, 198, 198), outline=(72, 231, 216, 210), width=7)
    d.rectangle((83, 87, 173, 167), fill=(27, 33, 35, 245), outline=(255, 212, 118, 245), width=6)
    d.line((83, 110, 173, 110), fill=(255, 151, 37, 225), width=7)
    d.line((128, 87, 128, 167), fill=(72, 231, 216, 205), width=5)
    for angle in range(0, 360, 45):
        r0 = 104
        r1 = 122
        a = math.radians(angle)
        d.line(
            (
                128 + math.cos(a) * r0,
                128 + math.sin(a) * r0,
                128 + math.cos(a) * r1,
                128 + math.sin(a) * r1,
            ),
            fill=(255, 187, 68, 180),
            width=6,
        )
    return glow_layer(image, 8.0, 0.62)


def draw_sorter_bot(d: ImageDraw.ImageDraw, frame: int, scale: int) -> None:
    def p(value):
        return int(value * scale)

    repair = frame <= 2
    alarm = frame >= 8
    bob = math.sin(frame * 1.3) * 2
    cx = p(80)
    cy = p(59 + bob)
    d.rounded_rectangle(
        (cx - p(34), cy - p(22), cx + p(34), cy + p(21)),
        radius=p(7),
        fill=(25, 31, 33, 250),
        outline=(255, 151, 40, 255) if alarm else (78, 232, 216, 255),
        width=p(3),
    )
    d.rectangle(
        (cx - p(21), cy - p(14), cx + p(20), cy + p(7)),
        fill=(8, 14, 16, 255),
        outline=(225, 244, 230, 230),
        width=p(2),
    )
    eye = (255, 74, 50, 255) if alarm else (255, 190, 50, 255)
    d.ellipse((cx - p(5), cy - p(8), cx + p(5), cy + p(2)), fill=eye)
    for side in (-1, 1):
        wheel_x = cx + side * p(24)
        d.ellipse(
            (wheel_x - p(10), cy + p(12), wheel_x + p(10), cy + p(31)),
            fill=(7, 9, 10, 255),
            outline=(135, 153, 156, 235),
            width=p(3),
        )
    if repair:
        d.line((cx - p(34), cy - p(3), cx - p(56), cy - p(20)), fill=(255, 184, 56, 255), width=p(5))
        d.line((cx + p(34), cy - p(3), cx + p(56), cy - p(20)), fill=(255, 184, 56, 255), width=p(5))
        d.rectangle((cx - p(63), cy - p(26), cx - p(51), cy - p(14)), fill=(84, 235, 218, 245))
        d.rectangle((cx + p(51), cy - p(26), cx + p(63), cy - p(14)), fill=(84, 235, 218, 245))
    elif alarm:
        for index in range(3):
            d.line(
                (cx - p(55), cy - p(22 + index * 8), cx - p(40), cy - p(22 + index * 8)),
                fill=(255, 102, 40, 170),
                width=p(3),
            )


def circuit_base(seed: int) -> Image.Image:
    rng = random.Random(seed)
    image = Image.new("RGBA", (WIDTH, HEIGHT), (3, 5, 12, 255))
    d = ImageDraw.Draw(image, "RGBA")

    # A giant circuit board doubles as the stunt arena.
    for lane, y in enumerate((70, 175, 280, 385, 490)):
        color = (42, 228, 255, 95) if lane % 2 == 0 else (255, 55, 177, 85)
        points = [(0, y)]
        x = 0
        while x < WIDTH:
            x += rng.randrange(58, 132)
            points.append((min(x, WIDTH), y + rng.choice((-28, 0, 28))))
        d.line(points, fill=color, width=4)
        for x, py in points[1:-1]:
            d.ellipse((x - 8, py - 8, x + 8, py + 8), fill=(7, 17, 28, 255), outline=color, width=3)

    for x in range(45, WIDTH, 118):
        top = rng.randrange(30, 170)
        bottom = rng.randrange(360, 525)
        color = (255, 69, 182, 75) if (x // 118) % 3 == 0 else (55, 229, 255, 72)
        d.line((x, top, x, bottom), fill=color, width=3)
        if x % 2:
            d.arc((x - 55, 190, x + 55, 300), 195, 345, fill=(255, 182, 51, 110), width=5)

    # Ramps, loops, and landing decks are structural silhouettes.
    for x in range(90, WIDTH, 310):
        y = 420 - ((x // 310) % 2) * 115
        d.line((x, y, x + 82, y - 62), fill=(167, 237, 255, 165), width=7)
        d.line((x + 82, y - 62, x + 135, y - 62), fill=(167, 237, 255, 115), width=5)
    for x in range(250, WIDTH, 620):
        d.ellipse((x, 105, x + 150, 255), outline=(255, 62, 184, 145), width=8)
        d.ellipse((x + 28, 133, x + 122, 227), outline=(67, 231, 255, 115), width=4)

    for x in range(0, WIDTH, 26):
        d.rectangle((x, 535, x + 13, 550), fill=(255, 167, 42, 80))
    return glow_layer(image, 3.0, 0.35)


def circuit_flow(seed: int, layer_index: int) -> Image.Image:
    rng = random.Random(seed + 103 * layer_index)
    image = Image.new("RGBA", (2000, 590), (0, 0, 0, 0))
    d = ImageDraw.Draw(image, "RGBA")
    if layer_index == 0:
        for lane, y in enumerate((72, 177, 282, 387, 492)):
            for x in range(-40, 2000, 86):
                color = (66, 238, 255, 150) if lane % 2 == 0 else (255, 63, 187, 135)
                d.ellipse((x, y - 4, x + 12, y + 8), fill=color)
                d.line((x - 20, y + 2, x, y + 2), fill=color, width=2)
    else:
        for index in range(90):
            x = rng.randrange(0, 2000)
            y = rng.randrange(30, 560)
            radius = 2 if index % 5 else 4
            color = (255, 188, 56, rng.randrange(70, 150))
            d.line((x, y, x + rng.randrange(8, 24), y - rng.randrange(2, 14)), fill=color, width=2)
            d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    return glow_layer(image, 5.0, 0.60)


def circuit_event() -> Image.Image:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(image, "RGBA")
    d.ellipse((25, 25, 231, 231), outline=(255, 62, 187, 220), width=12)
    d.ellipse((52, 52, 204, 204), outline=(60, 236, 255, 225), width=7)
    d.polygon(
        [(66, 165), (126, 100), (184, 165), (160, 165), (126, 132), (92, 165)],
        fill=(255, 182, 45, 230),
        outline=(255, 241, 189, 255),
    )
    for angle in range(0, 360, 30):
        a = math.radians(angle)
        d.ellipse(
            (
                128 + math.cos(a) * 112 - 4,
                128 + math.sin(a) * 112 - 4,
                128 + math.cos(a) * 112 + 4,
                128 + math.sin(a) * 112 + 4,
            ),
            fill=(255, 194, 56, 210),
        )
    return glow_layer(image, 9.0, 0.72)


def draw_circuit_rider(d: ImageDraw.ImageDraw, frame: int, scale: int) -> None:
    def p(value):
        return int(value * scale)

    repair = frame <= 2
    alarm = frame >= 8
    airborne = repair or alarm
    turn = (frame - 8) * 0.16 if alarm else 0.0
    cx = p(80)
    cy = p(62 - (10 if airborne else math.sin(frame * 1.2) * 2))
    accent = (255, 63, 184, 255) if alarm else (57, 235, 255, 255)
    for side in (-1, 1):
        wheel_x = cx + side * p(26)
        d.ellipse(
            (wheel_x - p(15), cy - p(2), wheel_x + p(15), cy + p(28)),
            fill=(4, 6, 12, 255),
            outline=accent,
            width=p(4),
        )
        d.ellipse(
            (wheel_x - p(6), cy + p(7), wheel_x + p(6), cy + p(19)),
            fill=(255, 183, 45, 220),
        )
    d.line((cx - p(26), cy + p(10), cx, cy - p(8), cx + p(26), cy + p(10)), fill=accent, width=p(5))
    d.line((cx, cy - p(8), cx + p(15), cy - p(27)), fill=(255, 196, 62, 255), width=p(4))
    d.ellipse((cx + p(8), cy - p(40), cx + p(23), cy - p(25)), fill=(255, 229, 174, 255), outline=accent, width=p(2))
    if repair:
        d.line((cx - p(62), cy + p(34), cx + p(62), cy + p(34)), fill=(255, 184, 48, 175), width=p(4))
        d.line((cx - p(55), cy + p(34), cx - p(15), cy + p(8)), fill=(255, 235, 170, 185), width=p(3))
    if alarm:
        for index in range(5):
            x = cx - p(50 + index * 8)
            y = cy + p(11 + math.sin(turn + index) * 12)
            d.ellipse((x - p(3), y - p(3), x + p(3), y + p(3)), fill=(255, 111, 30, 220 - index * 24))


THEMES = {
    "night-shift": (
        night_shift_base,
        night_shift_flow,
        night_shift_event,
        draw_service_craft,
        0xA17E,
    ),
    "midnight-conveyor": (
        conveyor_base,
        conveyor_flow,
        conveyor_event,
        draw_sorter_bot,
        0xC0DE,
    ),
    "circuit-stunt-show": (
        circuit_base,
        circuit_flow,
        circuit_event,
        draw_circuit_rider,
        0xB17E,
    ),
}


def generate(theme: str, out: Path) -> None:
    base_fn, flow_fn, event_fn, agent_fn, seed = THEMES[theme]
    out.mkdir(parents=True, exist_ok=True)
    base_fn(seed).save(out / "Substrate_Base.png")
    for index in range(2):
        flow_fn(seed, index).save(out / "Substrate_Flow_{:02d}.png".format(index))
    event_fn().save(out / "Damage_Tear.png")
    for frame in range(16):
        save_agent(
            agent_fn,
            out / "Mender_Frame_{:02d}.png".format(frame),
            frame,
        )
    print("Generated {} assets in {}".format(theme, out))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--theme",
        choices=sorted(THEMES),
        default="night-shift",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generated" / "art",
    )
    args = parser.parse_args()
    generate(args.theme, args.out)


if __name__ == "__main__":
    main()
