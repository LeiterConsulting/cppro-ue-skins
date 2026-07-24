from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    directory = Path(__file__).resolve().parent / "assets"
    directory.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (256, 256), "#17233A")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((25, 60, 231, 196), 24, fill="#F3F5F8")
    colors = ("#18A7C9", "#2A9D77", "#E59B2F", "#8A63D2", "#18A7C9")
    for index, color in enumerate(colors):
        left = 42 + index * 35
        draw.rounded_rectangle(
            (left, 91, left + 27, 136),
            6,
            fill=color,
        )
    draw.rounded_rectangle((74, 149, 182, 170), 8, fill="#17233A")
    ico = directory / "cppro-loader.ico"
    png = directory / "cppro-loader.png"
    icns = directory / "cppro-loader.icns"
    image.save(
        ico,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    image.save(png, format="PNG")
    image.save(icns, format="ICNS")
    for output in (ico, png, icns):
        print(output)


if __name__ == "__main__":
    main()
