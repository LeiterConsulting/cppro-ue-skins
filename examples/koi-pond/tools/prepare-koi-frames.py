"""Build device-safe koi frames from the example's transparent atlas.

The first atlas row is the eight-pose cruise loop. By default, FFmpeg motion
interpolation inserts one in-between pose between each source pose, including
the frame-7-to-frame-0 seam. The second row is a pronounced turn/reaction
sequence and is intentionally not mixed into ordinary cruising.
"""

from argparse import ArgumentParser
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image


FRAME_SIZE = (256, 128)
SOURCE_FRAME_COUNT = 8
RUNTIME_FRAME_COUNT = 16


def save_source_frames(rgba: Image.Image, output: Path) -> list[Path]:
    frames = []
    for index in range(SOURCE_FRAME_COUNT):
        frame = rgba.crop(
            (index * FRAME_SIZE[0], 0, (index + 1) * FRAME_SIZE[0], FRAME_SIZE[1])
        )
        path = output / f"Source_{index:02d}.png"
        frame.save(path)
        frames.append(path)
    return frames


def interpolate_cruise_frames(frames: list[Path], output: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg is required for motion-compensated koi interpolation"
        )

    with tempfile.TemporaryDirectory(prefix="cppro-koi-") as temp_name:
        temp = Path(temp_name)
        # Two repeated poses give the interpolation filter enough look-ahead
        # to generate the final frame between source frame 7 and frame 0.
        loop_inputs = frames + frames[:2]
        for index, source in enumerate(loop_inputs):
            shutil.copy2(source, temp / f"Input_{index:02d}.png")

        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "warning",
                "-framerate",
                "8",
                "-i",
                str(temp / "Input_%02d.png"),
                "-vf",
                (
                    "minterpolate=fps=16:mi_mode=mci:mc_mode=aobmc:"
                    "me_mode=bidir:vsbmc=1,format=rgba"
                ),
                "-frames:v",
                str(RUNTIME_FRAME_COUNT),
                str(temp / "Smooth_%02d.png"),
            ],
            check=True,
        )
        generated = sorted(temp.glob("Smooth_*.png"))
        if len(generated) != RUNTIME_FRAME_COUNT:
            raise RuntimeError(
                f"Expected {RUNTIME_FRAME_COUNT} interpolated frames, "
                f"got {len(generated)}"
            )
        for index, source in enumerate(generated):
            shutil.copy2(source, output / f"Koi_Cruise_{index:02d}.png")


def write_contact_sheet(output: Path) -> None:
    gutter = 4
    columns = 4
    rows = RUNTIME_FRAME_COUNT // columns
    width = gutter + columns * (FRAME_SIZE[0] + gutter)
    height = gutter + rows * (FRAME_SIZE[1] + gutter)
    sheet = Image.new("RGBA", (width, height), (32, 32, 32, 255))
    for index in range(RUNTIME_FRAME_COUNT):
        with Image.open(output / f"Koi_Cruise_{index:02d}.png") as frame:
            x = gutter + (index % columns) * (FRAME_SIZE[0] + gutter)
            y = gutter + (index // columns) * (FRAME_SIZE[1] + gutter)
            sheet.paste(frame.convert("RGBA"), (x, y))
    sheet.save(output / "contact.png")


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("atlas", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="Write the eight source cruise poses without interpolation",
    )
    args = parser.parse_args()

    with Image.open(args.atlas) as atlas:
        rgba = atlas.convert("RGBA")
        if rgba.size != (2048, 256):
            raise ValueError(
                f"Expected a 2048x256 atlas, got {rgba.width}x{rgba.height}"
            )
        args.output.mkdir(parents=True, exist_ok=True)
        frames = save_source_frames(rgba, args.output)
        if args.source_only:
            for index in range(RUNTIME_FRAME_COUNT):
                shutil.copy2(
                    frames[index % SOURCE_FRAME_COUNT],
                    args.output / f"Koi_Cruise_{index:02d}.png",
                )
        else:
            interpolate_cruise_frames(frames, args.output)
        write_contact_sheet(args.output)


if __name__ == "__main__":
    main()
