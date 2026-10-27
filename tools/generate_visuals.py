"""Render the original, decorative animations used by Jerry's profile.

Requires Pillow, PyGObject, and the system GdkPixbuf SVG loader.
Run from any directory: python3 tools/generate_visuals.py
"""

from __future__ import annotations

import base64
import io
import math
import re
from pathlib import Path

import gi
from PIL import Image, ImageDraw, ImageFont

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
BG = "#0d1726"
MINT = "#91efd0"
LAVENDER = "#b7a6ed"
WHITE = "#e9f1fb"
MUTED = "#96a9bf"


def font(size: int, *, mono: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont:
    family = "DejaVuSansMono" if mono else "DejaVuSans"
    filename = f"{family}{'-Bold' if bold else ''}.ttf"
    return ImageFont.truetype(filename, size)


def svg_image(source: str) -> Image.Image:
    loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
    loader.write(source.encode())
    loader.close()
    pixbuf = loader.get_pixbuf()
    success, encoded = pixbuf.save_to_bufferv("png", [], [])
    if not success:
        raise RuntimeError("Could not render SVG")
    rgba = Image.open(io.BytesIO(encoded)).convert("RGBA")
    background = Image.new("RGBA", rgba.size, BG)
    background.alpha_composite(rgba)
    return background.convert("RGB")


def save_gif(name: str, frames: list[Image.Image], durations: int | list[int]) -> None:
    # One shared palette keeps colors stable between frames and avoids dithering noise.
    sample = Image.new("RGB", (frames[0].width, frames[0].height * 5))
    for index in range(5):
        sample.paste(frames[index * (len(frames) - 1) // 4], (0, index * frames[0].height))
    palette = sample.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(
        ASSETS / name,
        save_all=True,
        append_images=indexed[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )
    frames[0].save(ASSETS / name.replace(".gif", "-still.png"))
    print(f"{name}: {(ASSETS / name).stat().st_size / 1024:.0f} KiB", flush=True)


def ease(value: float) -> float:
    return value * value * (3 - 2 * value)


def arm_pose(t: float) -> tuple[float, float, float, float, float]:
    # End-effector x/y, decorative cube x/y, and gripper opening.
    keys = [
        (0.00, 1015, 183, 1026, 264, 13),
        (0.16, 1026, 228, 1026, 264, 13),
        (0.24, 1026, 228, 1026, 264, 8),
        (0.42, 1026, 155, 1026, 191, 8),
        (0.62, 943, 155, 943, 191, 8),
        (0.78, 943, 228, 943, 264, 8),
        (0.87, 943, 228, 943, 264, 13),
        (1.00, 943, 183, 943, 264, 13),
    ]
    for start, end in zip(keys, keys[1:]):
        if start[0] <= t <= end[0]:
            weight = ease((t - start[0]) / (end[0] - start[0]))
            return tuple(a + (b - a) * weight for a, b in zip(start[1:], end[1:]))
    raise ValueError(t)


def hero_logo(source: str) -> str:
    """Embed the red/yellow logo without its original black matte.

    Both flat logo colors have a 255-valued channel. Its maximum channel thus
    gives edge coverage; unpremultiplying preserves smooth edges on navy.
    """
    logo = Image.open(ASSETS / "better-call-jerry-logo.png").convert("RGB")
    transparent = Image.new("RGBA", logo.size)
    transparent.putdata([
        (round(red * 255 / alpha), round(green * 255 / alpha), round(blue * 255 / alpha), alpha)
        if (alpha := max(red, green, blue)) else (0, 0, 0, 0)
        for red, green, blue in logo.getdata()
    ])
    transparent = transparent.crop(transparent.getbbox())
    buffer = io.BytesIO()
    transparent.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    element = f'''<!-- profile-logo:start -->
    <image x="40" y="50" width="630" height="300" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{encoded}"/>
    <!-- profile-logo:end -->'''
    return re.sub(r"<!-- profile-logo:start -->.*?<!-- profile-logo:end -->", element, source, flags=re.DOTALL)


def make_hero() -> None:
    banner = ASSETS / "banner.svg"
    original = hero_logo(banner.read_text())
    banner.write_text(original)
    background = original.split('    <path d="M789 242')[0]
    background = background.replace('width="1200" height="400" viewBox', 'width="960" height="320" viewBox')
    frames = []
    for index in range(100):
        t = index / 100
        tx, ty, cx, cy, opening = arm_pose(2 * t if t <= 0.5 else 2 * (1 - t))
        sx, sy = 832, 260
        dx, dy = tx - sx, ty - sy
        length = math.hypot(dx, dy)
        angle = math.atan2(dy, dx) - math.acos(length / 244)
        ex, ey = sx + 122 * math.cos(angle), sy + 122 * math.sin(angle)
        dot_x = 788 + 255 * t
        dot_y = 216 - 110 * math.sin(math.pi * t)
        scene = f'''
    <path d="M788 216Q915 -4 1043 216" fill="none" stroke="#b7a6ed" stroke-width="2" stroke-dasharray="5 9" opacity=".35"/>
    <circle cx="{dot_x}" cy="{dot_y}" r="5" fill="#b7a6ed"/>
    <ellipse cx="832" cy="308" rx="61" ry="19" fill="#060d16" opacity=".5"/>
    <path d="M790 284L832 269L874 284V302L832 317L790 302Z" fill="#1d3342" stroke="#5b847d"/>
    <path d="M790 284L832 299L874 284M832 299V317" fill="none" stroke="#5b847d"/>
    <rect x="813" y="255" width="38" height="39" rx="12" fill="#3e655f" stroke="#83c6b2"/>
    <path d="M{sx} {sy}L{ex} {ey}L{tx} {ty}" fill="none" stroke="#07151c" stroke-width="37" stroke-linejoin="round"/>
    <path d="M{sx} {sy}L{ex} {ey}L{tx} {ty}" fill="none" stroke="url(#arm)" stroke-width="25" stroke-linejoin="round"/>
    <path d="M{sx} {sy}L{ex} {ey}L{tx} {ty}" fill="none" stroke="#dcfff0" stroke-opacity=".4" stroke-width="3"/>
    <g fill="#152d36" stroke="#adf1d9" stroke-width="3">
      <circle cx="{sx}" cy="{sy}" r="18"/>
      <circle cx="{ex}" cy="{ey}" r="20"/>
      <circle cx="{tx}" cy="{ty}" r="12"/>
    </g>
    <g fill="#80d8bd">
      <circle cx="{sx}" cy="{sy}" r="5"/>
      <circle cx="{ex}" cy="{ey}" r="6"/>
      <circle cx="{tx}" cy="{ty}" r="4"/>
    </g>
    <path d="M{tx} {ty+12}V{ty+22}M{tx-opening} {ty+22}H{tx+opening}M{tx-opening} {ty+22}V{ty+33}M{tx+opening} {ty+22}V{ty+33}" fill="none" stroke="#c4d5e4" stroke-width="5" stroke-linecap="round"/>
    <ellipse cx="{cx}" cy="289" rx="33" ry="10" fill="none" stroke="#b7a6ed" stroke-opacity=".3" stroke-dasharray="3 6"/>
    <path d="M{cx-15} {cy-10}L{cx} {cy-16}L{cx+15} {cy-10}V{cy+9}L{cx} {cy+15}L{cx-15} {cy+9}Z" fill="#514869" stroke="#c6b5f6" stroke-width="1.5"/>
    <path d="M{cx-15} {cy-10}L{cx} {cy-4}L{cx+15} {cy-10}M{cx} {cy-4}V{cy+15}" fill="none" stroke="#c6b5f6"/>
  </g>
</svg>'''
        frames.append(svg_image(background + scene))
    save_gif("better-call-jerry-hero.gif", frames, 80)


def make_typing() -> None:
    phrases = [
        "Your robot has the right to remain stable.",
        "Exploring LLM + VLA + RL + WM.",
        "Building one experiment at a time.",
    ]
    frames, durations = [], []
    face = font(24, mono=True)

    def append(text: str, duration: int) -> None:
        frame = Image.new("RGB", (960, 64), BG)
        draw = ImageDraw.Draw(frame)
        draw.text((42, 17), ">", font=face, fill=MINT)
        draw.text((76, 17), text, font=face, fill=WHITE)
        x = 78 + draw.textlength(text, font=face)
        draw.rectangle((x, 21, x + 11, 43), fill=MINT)
        frames.append(frame)
        durations.append(duration)

    append(phrases[0], 1500)
    for current, following in zip(phrases, phrases[1:] + phrases[:1]):
        for count in range(len(current) - 1, -1, -2):
            append(current[:count], 50)
        append("", 180)
        for count in range(1, len(following) + 1):
            append(following[:count], 55)
        append(following, 1500)
    save_gif("robot-rights-typing.gif", frames, durations)


def make_buddy() -> None:
    frames = []
    for index in range(64):
        t = index / 64
        bob = 3 * math.sin(2 * math.pi * t)
        wave = 20 * math.sin(6 * math.pi * t)
        blink = 0.40 < t < 0.45 or 0.84 < t < 0.88
        eyes = '<path d="M83 96H99M125 96H141" stroke="#91efd0" stroke-width="5" stroke-linecap="round"/>' if blink else '<rect x="85" y="85" width="13" height="23" rx="6" fill="#91efd0"/><rect x="126" y="85" width="13" height="23" rx="6" fill="#91efd0"/>'
        source = f'''<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240">
<rect width="240" height="240" rx="24" fill="{BG}"/>
<circle cx="120" cy="117" r="85" fill="none" stroke="#20384a" stroke-dasharray="3 8"/>
<ellipse cx="115" cy="208" rx="57" ry="9" fill="#07101c"/>
<g transform="translate(0 {bob})">
  <path d="M92 177V197M134 177V197" stroke="#aebfd3" stroke-width="16" stroke-linecap="round"/>
  <path d="M85 198H99M127 198H141" stroke="#91efd0" stroke-width="12" stroke-linecap="round"/>
  <path d="M76 147L55 166L50 154" fill="none" stroke="#aebfd3" stroke-width="11" stroke-linecap="round"/>
  <g transform="rotate({wave} 155 145)">
    <path d="M155 145L180 120L181 97" fill="none" stroke="#aebfd3" stroke-width="11" stroke-linecap="round"/>
    <circle cx="181" cy="89" r="12" fill="#91efd0"/>
    <path d="M174 84V75M182 81V71M189 84V76" stroke="#91efd0" stroke-width="5" stroke-linecap="round"/>
  </g>
  <rect x="76" y="129" width="76" height="53" rx="16" fill="#becbdc"/>
  <rect x="91" y="143" width="46" height="24" rx="8" fill="#21374a"/>
  <path d="M101 155H108L113 148L118 161L123 155H128" fill="none" stroke="#91efd0" stroke-width="2"/>
  <path d="M113 57V41" stroke="#bac9db" stroke-width="5"/>
  <circle cx="113" cy="36" r="7" fill="#b7a6ed"/>
  <rect x="59" y="57" width="108" height="74" rx="24" fill="#d4e0ed"/>
  <rect x="71" y="70" width="84" height="48" rx="17" fill="#142739"/>
  {eyes}
  <path d="M105 108Q113 114 121 108" fill="none" stroke="#91efd0" stroke-width="2.5" stroke-linecap="round"/>
  <circle cx="58" cy="94" r="7" fill="#a9b6cb"/><circle cx="168" cy="94" r="7" fill="#a9b6cb"/>
</g>
</svg>'''
        frames.append(svg_image(source))
    save_gif("robot-buddy.gif", frames, 80)


def pixel_robot(draw: ImageDraw.ImageDraw, x: int, y: int, step: int) -> None:
    sprite = [
        "      m      ",
        "      s      ",
        "   sssssss   ",
        "  sssssssss  ",
        "  sddddddds  ",
        "  sdmdddmds  ",
        "  sdmdddmds  ",
        "  sddddddds  ",
        "   sssssss   ",
        "     sss     ",
        "  sssssssss  ",
        " sssdmmdsss  ",
        " sssdmmdsss  ",
        "  sssssssss  ",
        "    ss ss    ",
    ]
    colors = {"s": "#d8e4f4", "d": "#173247", "m": MINT}
    for row, line in enumerate(sprite):
        for column, pixel in enumerate(line):
            if pixel in colors:
                px, py = x + column * 3, y + row * 3
                draw.rectangle((px, py, px + 2, py + 2), fill=colors[pixel])
    offset = 3 if step else -3
    draw.rectangle((x + 12 + offset, y + 45, x + 20 + offset, y + 50), fill=MINT)
    draw.rectangle((x + 24 - offset, y + 45, x + 32 - offset, y + 50), fill=MINT)


def make_arcade() -> None:
    frames = []
    label_font, small_font = font(17, mono=True), font(12, mono=True)
    for index in range(100):
        t = index / 100
        frame = Image.new("RGB", (960, 190), BG)
        draw = ImageDraw.Draw(frame)
        draw.text((28, 18), "A LITTLE ROBOT. A LOT TO LEARN.", font=label_font, fill=WHITE)
        draw.text((705, 23), "LEARN > BUILD > REPEAT", font=small_font, fill=MUTED)
        for star in range(26):
            x = (star * 137 + 83) % 940 + 10
            y = (star * 29) % 70 + 53
            draw.rectangle((x, y, x + 2, y + 2), fill="#30445c")
        for block in range(16):
            x = block * 64
            top = 117 - (block % 3) * 9
            draw.rectangle((x, top, x + 45, 155), fill="#152538")
            draw.rectangle((x + 7, top + 7, x + 10, top + 11), fill="#29435a")
        draw.rectangle((0, 157, 960, 160), fill="#5fbdab")
        for x in range(0, 960, 24):
            draw.rectangle((x, 164, x + 14, 166), fill="#263c4c")
        robot_x = int(t * 1080 - 60)
        for checkpoint, label in enumerate(("LLM", "VLA", "RL", "WM")):
            x = 180 + checkpoint * 200
            active = abs(robot_x + 20 - x) < 64
            color = MINT if active else LAVENDER
            draw.rounded_rectangle((x - 28, 66, x + 28, 91), radius=5, outline=color, width=2)
            width = draw.textlength(label, font=small_font)
            draw.text((x - width / 2, 71), label, font=small_font, fill=color)
            draw.line((x, 97, x, 105), fill="#466471", width=2)
            if active:
                draw.line((x - 38, 71, x - 33, 75), fill=MINT, width=2)
                draw.line((x + 33, 75, x + 38, 71), fill=MINT, width=2)
        bob = int(5 * abs(math.sin(t * math.pi * 12)))
        pixel_robot(draw, robot_x, 105 - bob, (index // 5) % 2)
        frames.append(frame)
    save_gif("robot-arcade.gif", frames, 70)


def make_badges() -> None:
    for label, color in (("LLM", MINT), ("VLA", "#94bcff"), ("RL", "#f2be7d"), ("WM", LAVENDER)):
        source = f'''<svg xmlns="http://www.w3.org/2000/svg" width="108" height="34" viewBox="0 0 108 34" role="img" aria-label="{label}">
<rect x=".5" y=".5" width="107" height="33" rx="9" fill="{BG}" stroke="#34475c"/>
<circle cx="20" cy="17" r="4" fill="{color}"/>
<text x="36" y="22" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" letter-spacing="2" fill="{color}">{label}</text>
</svg>'''
        (ASSETS / f"badge-{label.lower()}.svg").write_text(source + "\n")


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    make_hero()
    make_typing()
    make_buddy()
    make_arcade()
    make_badges()
