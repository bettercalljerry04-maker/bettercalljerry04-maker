"""Animate a pixel-art room with Pillow; all regions use a 240 x 135 grid.

Run: python3 tools/animate_room.py
Optional: --config regions.json, --guide /tmp/room-regions.png
The guide command only writes a marked preview, never the final animation.

Inspect the selected base before enabling head_polygon. A tightly fitted ear
polygon is often safer than the whole head, especially where it meets a neck.
No camera motion or moving background rectangles are used.
"""

from __future__ import annotations

import argparse
from collections import deque
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SIZE = (240, 135)
OUTPUT_SIZE = (960, 540)
FRAME_COUNT = 49
DURATION = 100

# Coordinates match the selected base. Override any key with a JSON config.
DEFAULT_REGIONS = {
    "neon_boxes": [[19, 4, 64, 46]],
    "monitor_box": [84, 82, 100, 96],
    "cursor": [98, 96],
    # Move just the large ear; the face, whiskers and neck stay planted.
    "head_polygon": [[118, 91], [121, 87], [124, 85], [128, 86],
                     [131, 89], [132, 94], [131, 99], [128, 103],
                     [124, 105], [118, 104]],
    "head_warm_only": True,
    "head_shift": [1, 0],
    "head_active_frames": [18, 19, 20, 34, 35],
    "hand_polygon": [[97, 110], [99, 108], [102, 107], [104, 108],
                     [105, 110], [108, 110], [108, 112], [104, 113],
                     [100, 111], [97, 111]],
    "hand_shift": [0, -1],
    "hand_active_frames": [4, 5, 10, 11, 16, 17, 24, 25, 30, 31, 42, 43],
    "stars": [[191, 20], [215, 32], [204, 13]],
}


def region_mask(boxes: list[list[int]]) -> Image.Image:
    mask = Image.new("L", SIZE)
    drawing = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in boxes:
        if not (0 <= x0 < x1 <= SIZE[0] and 0 <= y0 < y1 <= SIZE[1]):
            raise ValueError(f"Region outside the logical canvas: {x0,y0,x1,y1}")
        drawing.rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)
    return mask


def neon_mask(base: Image.Image, boxes: list[list[int]]) -> Image.Image:
    """Select pink/magenta pixels, keeping nearby dark wall pixels stationary."""
    color_mask = Image.new("L", SIZE)
    color_mask.putdata([
        255 if r > 80 and b > 70 and r > g * 1.3 and b > g * 1.2 else 0
        for r, g, b in base.getdata()
    ])
    return ImageChops.multiply(color_mask, region_mask(boxes))


def fill_mask_holes(mask: Image.Image) -> Image.Image:
    """Include dark eyes and internal outlines enclosed by a selected silhouette."""
    padded = Image.new("L", (SIZE[0] + 2, SIZE[1] + 2))
    padded.paste(mask, (1, 1))
    ImageDraw.floodfill(padded, (0, 0), 128)
    filled = padded.point(lambda value: 0 if value == 128 else 255)
    return filled.crop((1, 1, SIZE[0] + 1, SIZE[1] + 1))


def head_mask(base: Image.Image, regions: dict) -> Image.Image | None:
    """Create a real silhouette, never a translated rectangular crop.

    For an exact hand-drawn outline set head_warm_only=false. Otherwise the
    polygon limits brown/gold/pink segmentation, which expands by one pixel
    to retain outlines and fills enclosed eye/mouth holes.
    """
    polygon = regions["head_polygon"]
    if not polygon:
        return None
    if len(polygon) < 3 or any(not (0 <= x < SIZE[0] and 0 <= y < SIZE[1]) for x, y in polygon):
        raise ValueError("head_polygon must contain at least three in-bounds points")
    outline = Image.new("L", SIZE)
    ImageDraw.Draw(outline).polygon([tuple(point) for point in polygon], fill=255)
    if not regions["head_warm_only"]:
        return outline
    warm = Image.new("L", SIZE)
    warm.putdata([
        255 if r > 65 and r > g * 1.08 and r > b * 1.2 and g > 25 else 0
        for r, g, b in base.getdata()
    ])
    selected = ImageChops.multiply(warm, outline)
    if not selected.getbbox():
        raise ValueError("No warm character pixels inside head_polygon; inspect the mask")
    selected = selected.filter(ImageFilter.MaxFilter(3))
    return ImageChops.multiply(fill_mask_holes(selected), outline)


def local_edge_fill(base: Image.Image, mask: Image.Image) -> Image.Image:
    """Extend nearest surrounding pixels into the mask for a 1-pixel twitch.

    Only the exposed edge is visible after the masked character is pasted.
    This deliberately simple fill is intended for one-pixel motion; inspect
    intersections with furniture/neck edges before publishing.
    """
    result = base.copy()
    pixels, selected = result.load(), mask.load()
    visited = set()
    queue = deque()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            if not selected[x, y]:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < SIZE[0] and 0 <= ny < SIZE[1] and not selected[nx, ny]:
                    visited.add((x, y))
                    queue.append((x, y, pixels[nx, ny]))
                    break
    while queue:
        x, y, color = queue.popleft()
        pixels[x, y] = color
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (0 <= nx < SIZE[0] and 0 <= ny < SIZE[1]
                    and selected[nx, ny] and (nx, ny) not in visited):
                visited.add((nx, ny))
                queue.append((nx, ny, color))
    return result


def frames_for(base: Image.Image, regions: dict) -> list[Image.Image]:
    pink = neon_mask(base, regions["neon_boxes"])
    character = head_mask(base, regions)
    clean = local_edge_fill(base, character) if character is not None else base
    hand = head_mask(base, dict(regions, head_polygon=regions["hand_polygon"]))
    hand_clean = local_edge_fill(base, hand) if hand is not None else base
    monitor = regions["monitor_box"]
    if monitor is not None:
        region_mask([monitor])  # Validate the exclusive bounds.
    frames = []
    for index in range(FRAME_COUNT):
        frame = base.copy()
        # Mild breathing light: never global brightness or whole-scene movement.
        brightness = 0.92 + 0.08 * math.cos(2 * math.pi * index / FRAME_COUNT)
        dimmed = base.point(lambda value: round(value * brightness))
        frame.paste(dimmed, (0, 0), pink)
        if character is not None and index in regions["head_active_frames"]:
            frame.paste(clean, (0, 0), character)
            frame.paste(base, tuple(regions["head_shift"]), character)
        if hand is not None and index in regions["hand_active_frames"]:
            frame.paste(hand_clean, (0, 0), hand)
            frame.paste(base, tuple(regions["hand_shift"]), hand)
        draw = ImageDraw.Draw(frame)
        for star, (x, y) in enumerate(regions["stars"]):
            pulse = (1 + math.cos(2 * math.pi * (index / FRAME_COUNT + star / 3))) / 2
            color = tuple(round(a + pulse * (b - a)) for a, b in zip(
                base.getpixel((x, y)), (37, 95, 148), strict=True
            ))
            draw.point((x, y), fill=color)
        if monitor is not None:
            x0, y0, x1, y1 = monitor
            # Short code marks progress through seven rows in a 4.9-second loop.
            # This also retains 49 distinct frames without artificial noise.
            column, row = index % 7, index // 7
            x = x0 + 1 + round(column * max(0, x1 - x0 - 5) / 6)
            y = y0 + 1 + round(row * max(0, y1 - y0 - 3) / 6)
            draw.line((x, y, min(x + 2, x1 - 1), y), fill=(87, 137, 198))
        cursor = regions["cursor"]
        if cursor is not None and index % 12 < 6:
            x, y = cursor
            draw.line((x, y, x, y + 2), fill=(173, 180, 211))
        frames.append(frame)
    return frames


def write_gif(frames: list[Image.Image], output: Path) -> None:
    # Quantize all logical frames together: one shared palette, no crawling
    # dithering patterns. Nearest-neighbor upscaling retains hard pixel edges.
    atlas = Image.new("RGB", (SIZE[0], SIZE[1] * len(frames)))
    for index, frame in enumerate(frames):
        atlas.paste(frame, (0, index * SIZE[1]))
    palette = atlas.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE).resize(
            OUTPUT_SIZE, Image.Resampling.NEAREST
        )
        for frame in frames
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(
        output, save_all=True, append_images=indexed[1:], duration=DURATION,
        loop=0, optimize=True, disposal=1,
    )
    indexed[0].convert("RGB").save(output.with_name(f"{output.stem}-still.png"))
    with Image.open(output) as check:
        duration = 0
        for index in range(check.n_frames):
            check.seek(index)
            duration += check.info["duration"]
        print(f"{output}: {check.n_frames} frames, {duration} ms, {output.stat().st_size / 1024:.1f} KiB")
        if duration != FRAME_COUNT * DURATION:
            raise RuntimeError("GIF duration does not match the intended loop")


def write_guide(base: Image.Image, regions: dict, output: Path) -> None:
    preview = base.convert("RGBA")
    character = head_mask(base, regions)
    if character is not None:
        tint = Image.new("RGBA", SIZE, (255, 170, 32, 100))
        preview.paste(tint, (0, 0), character)
    hand = head_mask(base, dict(regions, head_polygon=regions["hand_polygon"]))
    if hand is not None:
        tint = Image.new("RGBA", SIZE, (60, 255, 150, 100))
        preview.paste(tint, (0, 0), hand)
    draw = ImageDraw.Draw(preview)
    for box in regions["neon_boxes"]:
        draw.rectangle(box, outline=(255, 70, 220, 255))
    if regions["monitor_box"]:
        draw.rectangle(regions["monitor_box"], outline=(70, 230, 230, 255))
    preview = preview.resize(OUTPUT_SIZE, Image.Resampling.NEAREST)
    grid = ImageDraw.Draw(preview)
    for x in range(0, SIZE[0], 20):
        grid.text((x * 4 + 2, 2), str(x), fill="white")
    for y in range(20, SIZE[1], 20):
        grid.text((2, y * 4), str(y), fill="white")
    output.parent.mkdir(parents=True, exist_ok=True)
    preview.save(output)
    print(f"Region guide: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "assets/jerry-room-base.png")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/jerry-room.gif")
    parser.add_argument("--config", type=Path, help="JSON overrides for DEFAULT_REGIONS")
    parser.add_argument("--guide", type=Path, help="Write a region preview only")
    args = parser.parse_args()
    regions = dict(DEFAULT_REGIONS)
    if args.config:
        overrides = json.loads(args.config.read_text())
        unknown = set(overrides) - set(regions)
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        regions.update(overrides)
    with Image.open(args.input) as source:
        if abs(source.width / source.height - SIZE[0] / SIZE[1]) > 0.02:
            raise ValueError("Base image must have a 16:9 aspect ratio")
        base = source.convert("RGB").resize(SIZE, Image.Resampling.NEAREST)
    if args.guide:
        write_guide(base, regions, args.guide)
    else:
        write_gif(frames_for(base, regions), args.output)


if __name__ == "__main__":
    main()
