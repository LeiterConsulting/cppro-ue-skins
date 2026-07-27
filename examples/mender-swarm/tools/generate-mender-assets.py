"""Generate the original Mender Swarm artwork from its five-state atlas."""

from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


EXAMPLE = Path(__file__).resolve().parents[1]
ATLAS = EXAMPLE / "source-art" / "T_MenderPrototypeAtlas.png"
OUT = EXAMPLE / "generated" / "art"
WIDTH = 1920
HEIGHT = 550
SEED = 0xC0FFEE


def lerp(a, b, amount):
    return int(round(a + (b - a) * amount))


def background():
    rng = random.Random(SEED)
    image = Image.new("RGB", (WIDTH, HEIGHT), (5, 8, 15))
    pixels = image.load()

    hot_spots = [
        (240, 120, (14, 38, 53), 360),
        (720, 390, (28, 17, 48), 420),
        (1260, 150, (12, 49, 46), 450),
        (1700, 420, (42, 15, 38), 360),
    ]
    for y in range(HEIGHT):
        base_t = y / max(1, HEIGHT - 1)
        for x in range(WIDTH):
            r = lerp(5, 10, base_t)
            g = lerp(10, 6, base_t)
            b = lerp(18, 24, base_t)
            for hx, hy, color, radius in hot_spots:
                distance = math.hypot(x - hx, y - hy)
                influence = max(0.0, 1.0 - distance / radius) ** 2
                r += int(color[0] * influence)
                g += int(color[1] * influence)
                b += int(color[2] * influence)
            grain = rng.randrange(-2, 3)
            pixels[x, y] = (
                max(0, min(255, r + grain)),
                max(0, min(255, g + grain)),
                max(0, min(255, b + grain)),
            )

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    cell_w = 48
    cell_h = 28
    for row, y in enumerate(range(-cell_h, HEIGHT + cell_h, cell_h)):
        offset = 0 if row % 2 == 0 else cell_w // 2
        for x in range(-cell_w + offset, WIDTH + cell_w, cell_w):
            points = [
                (x + 12, y),
                (x + 36, y),
                (x + 48, y + 14),
                (x + 36, y + 28),
                (x + 12, y + 28),
                (x, y + 14),
            ]
            color = (
                (35, 236, 213, 19)
                if (x // cell_w + row) % 3
                else (235, 70, 209, 17)
            )
            draw.line(points + [points[0]], fill=color, width=1)

    for index in range(18):
        y0 = rng.randrange(0, HEIGHT)
        amplitude = rng.randrange(8, 32)
        wavelength = rng.randrange(140, 360)
        phase = rng.random() * math.tau
        points = []
        for x in range(-20, WIDTH + 21, 18):
            y = y0 + math.sin(x / wavelength * math.tau + phase) * amplitude
            points.append((x, y))
        color = (
            (59, 233, 213, rng.randrange(8, 18))
            if index % 2 == 0
            else (224, 72, 201, rng.randrange(7, 15))
        )
        draw.line(points, fill=color, width=1)

    for index in range(1150):
        x = rng.randrange(8, WIDTH - 8)
        y = rng.randrange(6, HEIGHT - 6)
        radius = 1 if index % 7 else 2
        color = (
            (94, 255, 224, rng.randrange(20, 52))
            if index % 4
            else (245, 104, 220, rng.randrange(18, 44))
        )
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=color,
        )

    overlay = overlay.filter(ImageFilter.GaussianBlur(0.35))
    image = Image.alpha_composite(image.convert("RGBA"), overlay)
    image.save(OUT / "Substrate_Base.png")


def flow_layers():
    """Create sparse layers intended for smooth UMG transform animation."""
    for layer_index in range(2):
        rng = random.Random(SEED + 30 + layer_index)
        image = Image.new("RGBA", (2000, 590), (0, 0, 0, 0))
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow, "RGBA")
        crisp = Image.new("RGBA", image.size, (0, 0, 0, 0))
        crisp_draw = ImageDraw.Draw(crisp, "RGBA")

        for filament in range(4):
            y0 = 85 + filament * 140 + layer_index * 32
            points = []
            for x in range(-20, image.width + 21, 24):
                y = (
                    y0
                    + math.sin(
                        x / (330.0 + filament * 55.0) * math.tau
                        + filament * 1.4
                        + layer_index * 0.8
                    )
                    * (12.0 + filament * 3.0)
                )
                points.append((x, y))
            color = (
                (78, 255, 229, 45)
                if (filament + layer_index) % 2
                else (255, 86, 217, 38)
            )
            glow_draw.line(points, fill=color, width=10)
            crisp_draw.line(
                points,
                fill=(
                    (185, 255, 244, 64)
                    if (filament + layer_index) % 2
                    else (255, 180, 237, 54)
                ),
                width=2,
            )

        for device in range(105):
            x = rng.randrange(30, image.width - 30)
            y = rng.randrange(22, image.height - 22)
            radius = 2 if device % 9 else 3
            color = (
                (115, 255, 230, rng.randrange(80, 135))
                if (device + layer_index) % 3
                else (255, 105, 220, rng.randrange(68, 118))
            )
            crisp_draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=color,
            )
            if device % 23 == 0:
                crisp_draw.ellipse(
                    (x - 8, y - 8, x + 8, y + 8),
                    outline=(215, 255, 249, 80),
                    width=2,
                )

        glow = glow.filter(ImageFilter.GaussianBlur(8.0))
        image = Image.alpha_composite(image, glow)
        image = Image.alpha_composite(image, crisp)
        image.save(OUT / "Substrate_Flow_{:02d}.png".format(layer_index))


def tear():
    rng = random.Random(SEED + 1)
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    center = (128, 128)

    membrane = Image.new("RGBA", image.size, (0, 0, 0, 0))
    membrane_draw = ImageDraw.Draw(membrane, "RGBA")
    membrane_draw.ellipse(
        (43, 43, 213, 213),
        fill=(84, 244, 224, 52),
        outline=(229, 255, 250, 175),
        width=8,
    )
    membrane_draw.ellipse(
        (77, 77, 179, 179),
        fill=(255, 87, 207, 64),
        outline=(255, 220, 116, 205),
        width=7,
    )
    membrane = membrane.filter(ImageFilter.GaussianBlur(4.0))
    image = Image.alpha_composite(image, membrane)
    draw = ImageDraw.Draw(image, "RGBA")

    for arm in range(14):
        angle = arm / 14.0 * math.tau + rng.uniform(-0.13, 0.13)
        length = rng.uniform(68, 118)
        points = [center]
        for step in range(1, 6):
            distance = length * step / 5.0
            jitter = rng.uniform(-9, 9)
            points.append(
                (
                    center[0] + math.cos(angle) * distance + jitter,
                    center[1] + math.sin(angle) * distance + jitter,
                )
            )
        draw.line(points, fill=(18, 15, 38, 215), width=11)
        draw.line(points, fill=(255, 83, 211, 235), width=7)
        draw.line(points, fill=(255, 235, 175, 235), width=3)

    for radius, alpha, width in (
        (18, 245, 8),
        (42, 200, 7),
        (74, 140, 6),
        (108, 80, 5),
    ):
        draw.ellipse(
            (
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ),
            outline=(160, 255, 240, alpha),
            width=width,
        )
    draw.ellipse((113, 113, 143, 143), fill=(255, 246, 206, 235))
    glow = image.filter(ImageFilter.GaussianBlur(5.0))
    glow.putalpha(glow.getchannel("A").point(lambda value: value // 3))
    image = Image.alpha_composite(glow, image)
    image.save(OUT / "Damage_Tear.png")


def mender_frames():
    atlas = Image.open(ATLAS).convert("RGBA")
    cell_width = atlas.width // 5
    cells = [
        atlas.crop((i * cell_width, 0, (i + 1) * cell_width, atlas.height))
        for i in range(5)
    ]

    state_sequence = [3, 4, 3, 0, 0, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1]
    for frame_index, state_index in enumerate(state_sequence):
        source = cells[state_index]
        bbox = source.getbbox()
        if bbox:
            source = source.crop(bbox)
        source.thumbnail((150, 96), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (160, 112), (0, 0, 0, 0))

        bob_x = int(round(math.sin(frame_index * 1.71) * 2))
        bob_y = int(round(math.cos(frame_index * 1.13) * 2))
        x = (canvas.width - source.width) // 2 + bob_x
        y = (canvas.height - source.height) // 2 + bob_y
        canvas.alpha_composite(source, (x, y))

        if frame_index >= 8:
            glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            glow.alpha_composite(canvas)
            alpha = glow.getchannel("A").filter(ImageFilter.GaussianBlur(5))
            tint = Image.new("RGBA", canvas.size, (255, 68, 200, 0))
            tint.putalpha(alpha.point(lambda value: value * 2 // 5))
            canvas = Image.alpha_composite(tint, canvas)
        elif frame_index <= 2:
            alpha = canvas.getchannel("A")
            tint = Image.new("RGBA", canvas.size, (255, 195, 87, 0))
            tint.putalpha(alpha.point(lambda value: value // 5))
            canvas = Image.alpha_composite(tint, canvas)
            canvas = ImageEnhance.Color(canvas).enhance(1.18)
        else:
            alpha = canvas.getchannel("A")
            tint = Image.new("RGBA", canvas.size, (82, 255, 230, 0))
            tint.putalpha(alpha.point(lambda value: value // 7))
            canvas = Image.alpha_composite(tint, canvas)
            canvas = ImageEnhance.Brightness(canvas).enhance(1.12)

        clean = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        clean.alpha_composite(canvas)
        clean_pixels = clean.load()
        for y in range(clean.height):
            for x in range(clean.width):
                if clean_pixels[x, y][3] == 0:
                    clean_pixels[x, y] = (0, 0, 0, 0)
        clean.save(OUT / "Mender_Frame_{:02d}.png".format(frame_index))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    background()
    flow_layers()
    tear()
    mender_frames()
    print("Generated Mender Swarm assets in {}".format(OUT))


if __name__ == "__main__":
    main()
